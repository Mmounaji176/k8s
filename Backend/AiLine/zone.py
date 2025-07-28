import argparse
import ast
import cv2
import torch
from ultralytics import YOLO
import numpy as np
import math
import time
import psutil
import subprocess
import threading
import queue
from shapely.geometry import Point, Polygon
from collections import defaultdict
from Backend.celery import app as solo_worker
import os 
import django
from Api.helpers import send_stream_status

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()
# Dictionary to store tracked objects and their timestamps
object_tracker = {}
object_last_seen = {}  # Track when an object was last detected
object_in_region = defaultdict(dict)  # Format: {obj_id: {region_idx: entry_time}}
region_counters = defaultdict(int)    # Count of objects in each region

# Frame skipping parameters
FRAME_SKIP = 3
SEND_DATA_EVERY = 1.0  # Interval to send data to WebSocket (in seconds)

# Object timeout - how long to wait before considering an object as lost (in seconds)
OBJECT_TIMEOUT = 0.5

def point_in_polygon(point, polygon):
    """
    Check if a point is inside a polygon using Shapely.
    
    Args:
    - point: (x, y) coordinate
    - polygon: List of (x, y) coordinates forming the polygon vertices
    
    Returns:
    - Boolean indicating if the point is inside the polygon
    """
    point_obj = Point(point)
    polygon_obj = Polygon(polygon)
    return polygon_obj.contains(point_obj)


import asyncio
import json
import websockets
from datetime import datetime

# Global tracking dictionary to store elapsed times for objects
object_region_times = {}  # {obj_id: {region_idx: elapsed_time}}

# Create a global queue for WebSocket notifications
websocket_queue = queue.Queue()

import asyncio

# Define a wrapper function to run the async function in an event loop
def websocket_thread_wrapper(websocket_url):
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Run the async function until it completes
    loop.run_until_complete(websocket_notification_thread(websocket_url))
    loop.close()

async def websocket_notification_thread(websocket_url):
    """
    Thread function to handle WebSocket notifications.
    Takes payloads from the queue and sends them via WebSocket.
    """
    # print(f"WebSocket notification thread started, sending to: {websocket_url}")
    
    while True:
        try:
            # Connect to the WebSocket server
            async with websockets.connect(websocket_url) as websocket:
                print("WebSocket connection established")
                # Start the notification loop
                while True:
                    try:
                        # Get payload from queue (blocking with timeout)
                        payload = websocket_queue.get(timeout=1.0)
                        
                        if payload is None:  # Sentinel value to stop the thread
                            print("WebSocket notification thread received stop signal")
                            break
                        
                        # Convert payload to JSON
                        payload_json = json.dumps(payload)
                        
                        # Send data to WebSocket server on realtime_line event
                        await websocket.send(
                            json.dumps({
                                'event': 'realtime_zone',
                                'data': payload_json
                            })
                        )
                        print(f"WebSocket data sent successfully: {payload}")
                        
                        # Mark task as done
                        websocket_queue.task_done()
                        
                    except queue.Empty:
                        # Timeout occurred, just continue the loop
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        print("WebSocket connection closed, reconnecting...")
                        break  # Break inner loop to reconnect
                    except Exception as e:
                        print(f"Error in WebSocket communication: {e}")
                        await asyncio.sleep(5)  # Wait before retrying
                        break  # Break inner loop to reconnect
        except Exception as e:
            print(f"Error in WebSocket notification thread: {e}")
            time.sleep(5)

def prepare_detection_payload(lost_objects_data):
    """
    Format the detection data for the payload
    """
    if not lost_objects_data:
        return "{}"
    
    return json.dumps(lost_objects_data)

def get_current_occupancy_stats():
    """
    Calculate total occupancy and max waiting time across all regions
    for objects that are currently being tracked (not lost or exited).
    
    Returns:
    - tuple: (total_occupation, max_waiting_time)
    """
    current_time = time.time()
    total_occupation = 0
    max_waiting_time = 0.0
    
    # Sum up objects in all regions
    for region_idx, count in region_counters.items():
        total_occupation += count
    
    # Find max waiting time across all tracked objects still in regions
    for obj_id, regions in object_in_region.items():
        for region_idx, entry_time in regions.items():
            elapsed_time = current_time - entry_time
            max_waiting_time = max(max_waiting_time, elapsed_time)
    
    return total_occupation, max_waiting_time

def process_lost_objects(lost_objects, args):
    """
    Process lost objects and send notification.
    Stats (occupancy, max_waiting_time) are based on current objects in regions.
    
    Args:
    - lost_objects: Dictionary of {obj_id: elapsed_time} for objects that exited or were lost
    - args: Command line arguments containing WebSocket and other config
    """
    if not lost_objects:
        return
    
    # Extract args
    location = args[4]
    camera_id = int(args[5])
    camera_name = args[6]
    websocket_url = args[7]
    model = "ZONE"
    camera_type = args[10]
    
    # Get current occupancy stats for objects still in regions
    total_occupation, max_waiting_time = get_current_occupancy_stats()
    
    # Create detection payload for lost/exited objects only
    detection_data = prepare_detection_payload(lost_objects)
    
    # Create full payload
    payload = {
        'location': location,
        'max_waiting_time': round(max_waiting_time, 2),  # Using current max time in regions
        'occupation': total_occupation,  # Using current total occupation
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
        'camera': camera_id,
        'camera_name': camera_name,
        'detection': detection_data,  # Still contains only the lost/exited objects
        'model': model,
        'camera_type': camera_type
    }
    
    # Queue for WebSocket thread instead of direct sending
    try:
        websocket_queue.put_nowait(payload)
    except queue.Full:
        print("WebSocket queue full, skipping lost objects notification")

# Modify the cleanup_lost_objects function to track and report lost objects
def cleanup_lost_objects(region_list, args):
    """
    Clean up objects that haven't been seen for a while (lost detections)
    and send notifications via WebSocket.
    
    Args:
    - region_list: List of regions
    - args: Command line arguments containing WebSocket and other config
    """
    current_time = time.time()
    lost_objects = []
    lost_objects_data = {}  # {obj_id: elapsed_time}
    
    # Find objects that haven't been seen recently
    for obj_id, last_seen_time in list(object_last_seen.items()):
        if current_time - last_seen_time > OBJECT_TIMEOUT:
            lost_objects.append(obj_id)
    
    # Clean up lost objects and collect their data
    for obj_id in lost_objects:
        # Check if object was in any regions and decrement counters
        if obj_id in object_in_region:
            # Track maximum elapsed time for this object across all regions
            max_elapsed_time = 0
            
            for region_idx in list(object_in_region[obj_id].keys()):
                # Calculate elapsed time for this object in this region
                entry_time = object_in_region[obj_id][region_idx]
                elapsed_time = current_time - entry_time
                max_elapsed_time = max(max_elapsed_time, elapsed_time)
                
                # Decrement the counter for this region
                region_counters[region_idx] -= 1
                # print(f"Object {obj_id} lost while in region {region_idx}. Counter adjusted to {region_counters[region_idx]}")
            
            # Store the maximum elapsed time for this lost object
            lost_objects_data[str(obj_id)] = round(max_elapsed_time, 2)
            
            # Remove object from region tracking
            del object_in_region[obj_id]
        
        # Remove object from trackers
        if obj_id in object_tracker:
            del object_tracker[obj_id]
        del object_last_seen[obj_id]
    
    # Send notification about lost objects if any were found
    if lost_objects_data:
        process_lost_objects(lost_objects_data, args)

# Modify check_region_presence to detect when objects leave regions
def check_region_presence(obj_id, current_pos, region_list, args):
    """
    Check if an object is present in any of the defined regions and track elapsed time.
    Report when objects leave regions via WebSocket.
    
    Args:
    - obj_id: Object identifier
    - current_pos: Current position (x, y)
    - region_list: List of regions, each defined by 4 points [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
    - args: Command line arguments containing WebSocket and other config
    
    Returns:
    - Dictionary with region presence information
    """
    current_time = time.time()
    result = {}
    exited_regions_data = {}  # {obj_id: elapsed_time}
    
    # Update the last seen time for this object
    object_last_seen[obj_id] = current_time
    
    # Store object's previously known regions to detect exits
    previous_regions = set(object_in_region.get(obj_id, {}).keys())
    current_regions = set()
    
    for region_idx, region in enumerate(region_list):
        # Convert region to format required by point_in_polygon
        polygon = [(region[i], region[i+1]) for i in range(0, len(region), 2)]
        
        if point_in_polygon(current_pos, polygon):
            # Object is in this region
            current_regions.add(region_idx)
            
            if obj_id not in object_in_region or region_idx not in object_in_region[obj_id]:
                # First time in this region, save entry time
                if obj_id not in object_in_region:
                    object_in_region[obj_id] = {}
                object_in_region[obj_id][region_idx] = current_time
                region_counters[region_idx] += 1
                
            # Calculate elapsed time in region
            entry_time = object_in_region[obj_id][region_idx]
            elapsed_time = current_time - entry_time
            
            result[region_idx] = elapsed_time
    
    # Check for regions the object has left
    regions_exited = previous_regions - current_regions
    
    if regions_exited:
        # Object has left at least one region
        for region_idx in regions_exited:
            # Calculate elapsed time in the region before exiting
            entry_time = object_in_region[obj_id][region_idx]
            elapsed_time = current_time - entry_time
            
            # Store elapsed time for notification
            exited_regions_data[str(obj_id)] = round(elapsed_time, 2)
            
            # Remove region from tracking and update counter
            del object_in_region[obj_id][region_idx]
            region_counters[region_idx] -= 1
            # print(f"Object {obj_id} exited region {region_idx}. Counter adjusted to {region_counters[region_idx]}")
        
        # Clean up if object is no longer in any region
        if len(object_in_region[obj_id]) == 0:
            del object_in_region[obj_id]
        
        # Send notification about objects that exited regions
        if exited_regions_data:
            process_lost_objects(exited_regions_data, args)
    
    return result

def frame_writer_thread(ffmpeg_process, frame_queue):
    """Dedicated thread for writing frames to FFmpeg with improved error handling"""
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        try:
            while True:
                frame = frame_queue.get()
                if frame is None:  # Sentinel to stop thread
                    return
                
                try:
                    ffmpeg_process.stdin.write(frame.tobytes())
                    ffmpeg_process.stdin.flush()
                    retry_count = 0  # Reset retry count on successful write
                except (BrokenPipeError, IOError) as pipe_error:
                    print(f"FFmpeg pipe error: {pipe_error}")
                    retry_count += 1
                    
                    if retry_count >= max_retries:
                        print("Max retries reached. Stopping frame writer thread.")
                        return
                    
                    # Optional: Add a short sleep between retries
                    time.sleep(1)
        
        except Exception as e:
            print(f"Unexpected error in frame writer thread: {e}")
            retry_count += 1
            
            if retry_count >= max_retries:
                print("Max retries reached. Stopping frame writer thread.")
                return
            
            # Optional: Add a short sleep between retries
            time.sleep(1)

def kill_ffmpeg_process(process):
    try:
        if process is None:
            return True
            
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
        
        # First try graceful termination
        process.terminate()
        
        try:
            process.wait(timeout=3)
            print("FFmpeg process terminated gracefully")
            return True
        except:
            print("Graceful termination failed, forcing kill")
            
        # Force kill children and parent
        for child in children:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        
        if parent.is_running():
            parent.kill()
            
        return True
        
    except (psutil.NoSuchProcess, ProcessLookupError) as e:
        print(f"Process already terminated: {e}")
        return True
    except Exception as e:
        print(f"Error killing FFmpeg process: {e}")
        return False

def initialize_stream(url, max_retries=10):
    """Initialize video capture with retries"""
    for attempt in range(max_retries):
        try:
            cap = cv2.VideoCapture(url)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    return cap, frame
        except Exception as e:
            print(f"Stream initialization attempt {attempt + 1} failed: {e}")
        
        print(f"Retrying stream initialization in 5 seconds... (Attempt {attempt + 1}/{max_retries})")
        time.sleep(5)
    return None, None

def start_ffmpeg_process2(width, height, stream_url):
    ffmpeg_command = [
        'ffmpeg',
        '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{width}x{height}',  
        '-pix_fmt', 'bgr24',
        '-i', '-',  
        '-c:v', 'libx264',
        '-preset', 'ultrafast',  
        '-vf', 'fps=30,scale=1280:720',
        '-pix_fmt', 'yuv420p',
        '-b:v', '5M',
        '-f', 'rtsp',
        '-rtsp_transport', 'tcp',
        '-rtsp_flags', 'listen',
        stream_url
    ]
    return subprocess.Popen(
        ffmpeg_command, 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        bufsize=10**6
    )
    

def handle_ffmpeg_process(frame, ffmpeg_process, width, height, stream_url):
    try:
        if ffmpeg_process.poll() is not None:
            # Process has terminated, check error output
            _, stderr = ffmpeg_process.communicate(timeout=1)
            print(f"FFmpeg process terminated with error: {stderr.decode() if stderr else 'No error message'}")
            
            # Restart the process
            ffmpeg_process = start_ffmpeg_process(width, height, stream_url)
            time.sleep(0.5)  # Short delay before resuming
            
        # Ensure frame is contiguous and properly formatted
        frame_bytes = np.ascontiguousarray(frame).tobytes()
        ffmpeg_process.stdin.write(frame_bytes)
        ffmpeg_process.stdin.flush()  # Ensure data is written
            
    except BrokenPipeError:
        print("FFmpeg pipe broken, restarting process...")
        kill_ffmpeg_process(ffmpeg_process)
        time.sleep(1)
        return start_ffmpeg_process(width, height, stream_url)
        
    except subprocess.TimeoutExpired:
        print("FFmpeg process timeout, restarting...")
        kill_ffmpeg_process(ffmpeg_process)
        time.sleep(1)
        return start_ffmpeg_process(width, height, stream_url)
        
    except Exception as e:
        print(f"Unexpected error in FFmpeg handling: {e}")
        kill_ffmpeg_process(ffmpeg_process)
        time.sleep(1)
        return start_ffmpeg_process(width, height, stream_url)
        
    return ffmpeg_process

def start_ffmpeg_process(width, height, stream_url):
    import subprocess

    ffmpeg_command1 = [
        'ffmpeg',
        '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{width}x{height}',  
        '-pix_fmt', 'bgr24',
        '-i', '-',  
        # '-c:v', 'h264_nvenc',  
        # '-preset', 'p1',  
        # '-zerolatency', '1',  # NVENC-specific low latency flag
        # '-rc', 'constqp', 
        # '-qp', '23', 
        '-c:v', 'libx264',
        '-preset', 'ultrafast',  
        '-vf', 'fps=30,scale=1280:720',
        '-pix_fmt', 'yuv420p',
        '-b:v', '5M',
        '-f', 'rtsp',
        '-rtsp_transport', 'tcp',
        '-rtsp_flags', 'listen',
        stream_url
    ]
    ffmpeg_command = [
        'ffmpeg',
        # Global options
        '-y',                           # Overwrite output without asking
        '-hwaccel', 'cuda',            # Enable CUDA hardware acceleration
     
        
        # Input options
        '-f', 'rawvideo',              # Force input format to raw video
        '-vcodec', 'rawvideo',         # Input video codec
        '-s', f'{width}x{height}',     # Input frame size
        '-pix_fmt', 'bgr24',           # Input pixel format
        '-framerate', '30',            # Input framerate
        '-i', '-',                     # Read from pipe
        
        # Video encoding options
        '-c:v', 'h264_nvenc',          # Use NVIDIA H.264 encoder
        '-preset', 'p1',               # Lowest latency preset
        '-tune', 'ull',                # Ultra-low latency tuning
        '-profile:v', 'baseline',      # Maximum compatibility profile
        '-level', '4.1',               # Widely supported H.264 level
        
        # Performance optimization
        '-rc', 'cbr',                  # Constant bitrate mode for stable streaming
        '-zerolatency', '1',           # Enable zero-latency operation
        '-delay', '0',                 # Minimize encoding delay
        '-g', '30',                    # GOP size = framerate for 1-second GOPs
        '-sc_threshold', '0',          # Disable scene change detection
        
        # Quality and bitrate settings
        '-b:v', '4M',                  # Target bitrate (4 Mbps)
        '-maxrate', '4M',              # Maximum bitrate
        '-bufsize', '8M',              # Buffer size (2x bitrate)
        '-qmin', '17',                 # Minimum quantizer
        '-qmax', '28',                 # Maximum quantizer
        
        # Format conversion
        '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p',
        
        # RTSP output settings
        '-f', 'rtsp',                  # Output format
        '-rtsp_transport', 'tcp',      # Use TCP for more reliable streaming
        '-rtsp_flags', 'prefer_tcp+listen',  # Prefer TCP and enable server mode
        '-fflags', '+nobuffer',        # Reduce buffering
        '-flags', 'low_delay',         # Enable low delay flags
        '-avioflags', 'direct',        # Minimize IO operations
        
        # Maximum compatibility options
        '-strict', 'experimental',     # Allow experimental features
        '-max_muxing_queue_size', '1024',  # Prevent muxing queue overflow
        
        stream_url                     # Output URL
    ]
    
    # Start process with pipe configuration
    process = subprocess.Popen(
        ffmpeg_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=10**8
    )
    send_stream_status("integrating stream (60s approx)")

    return process


def parse_regions(regions_arg):
    """
    Parses the command-line argument for multiple region coordinates.
    Each region is defined by 4 points (8 values: x1,y1,x2,y2,x3,y3,x4,y4)
    """
    try:
        # Convert the input string into a list of regions
        regions = ast.literal_eval(f"[{regions_arg}]")
        for region in regions:
            if len(region) != 8:
                raise ValueError("Each region must have exactly 8 coordinates [x1,y1,x2,y2,x3,y3,x4,y4]")
        return regions
    except (SyntaxError, ValueError) as e:
        print(f"Error parsing region argument: {e}")
        exit(1)

def resize_frame(frame, scale_percent=40):
    """Resize frame by percentage"""
    # goal_width = 512
    # scale_percent = (goal_width / frame.shape[1]) * 100
    width = int(frame.shape[1] * scale_percent / 100)
    height = int(frame.shape[0] * scale_percent / 100)
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

def draw_regions(frame, region_list):
    """Draw regions on the frame"""
    for region_idx, region in enumerate(region_list):
        # Create points as tuples
        points = [(region[i], region[i+1]) for i in range(0, len(region), 2)]
        # Convert to numpy array for OpenCV
        pts = np.array(points, np.int32)
        pts = pts.reshape((-1, 1, 2))
        
        # Draw the polygon
        cv2.polylines(frame, [pts], True, (0, 255, 255), 2)
        
        # Display region index and count
        center_x = sum(p[0] for p in points) // len(points)
        center_y = sum(p[1] for p in points) // len(points)
        cv2.putText(frame, f"Region {region_idx}: {region_counters[region_idx]}", 
                   (center_x, center_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    return frame
def convert_rectangle_format(input_points):
    
    result = []
    
    # Handle string input
    if isinstance(input_points, str):
        # Remove outer brackets and spaces
        input_str = input_points.strip()
        if input_str.startswith('[') and input_str.endswith(']'):
            input_str = input_str[1:-1]
        
        # Parse the string to get numbers
        nums = [int(x.strip()) for x in input_str.split(',') if x.strip()]
        input_points = nums
    
    # Check if input is already a list of lists
    if isinstance(input_points, list) and input_points and isinstance(input_points[0], list):
        # Process each sublist as a rectangle
        for rect in input_points:
            if len(rect) != 4:
                raise ValueError(f"Each rectangle should be in format [x1,y1,x2,y2], got {rect}")
                
            x1, y1, x2, y2 = rect
            
            # Calculate all four corners of the rectangle (clockwise order)
            corners = [
                x1, y1,  # top-left
                x2, y1,  # top-right
                x2, y2,  # bottom-right
                x1, y2   # bottom-left
            ]
            
            result.append(corners)
    else:
        # Handle flat list of points
        if len(input_points) % 4 != 0:
            raise ValueError(f"Number of points must be divisible by 4, got {len(input_points)} points")
        
        # Process points in groups of 4
        for i in range(0, len(input_points), 4):
            if i + 3 >= len(input_points):
                break
                
            x1, y1, x2, y2 = input_points[i:i+4]
            
            # Calculate all four corners of the rectangle (clockwise order)
            corners = [
                x1, y1,  # top-left
                x2, y1,  # top-right
                x2, y2,  # bottom-right
                x1, y2   # bottom-left
            ]
            
            result.append(corners)
    
    return result

# {'location': 'CAFET_EMINES', 'max_waiting_time': 16.5, 'occupation': 2, 'date': '2025-04-11 16:21:35.305440', 'camera': 0, 'camera_name': 'CAFET_EMINES_GUICHET', 'detection': '{"27": 16.5, "28": 14.01}', 'model': 'ZONE'}

@solo_worker.task
def main_zone(*args , **kwargs):
    print("inside zone script")
    import os 
    import redis 
    os.environ["CUDA_VISIBLE_DEVICES"] = args[13] 
    import torch
    print("CUDA available:", torch.cuda.is_available())
    print("CUDA version:", torch.version.cuda)
    print("PyTorch version:", torch.__version__)
    torch.cuda.set_device(int(args[13]))
    print(f"Current CUDA device: {torch.cuda.current_device()}")
    try:
            # Connect to Redis
        redis_client = redis.from_url('redis://:admin@redis-primary-service:6379/0')
        
        redis_client.select(0)  # Queue database
        redis_client.flushdb()
    
        
        # Wait a moment for connections to reestablish
        import time
        time.sleep(1)
        
        print("Redis cache successfully flushed")
    except redis.RedisError as e:
        print(f"Error setting up Redis queue: {e}")
        exit(1)
        # Parse websocket URL and other configuration
    websocket_url = args[7]
    print(f"WebSocket URL: {websocket_url}")
    print(f"Location: {args[4]}")
    print(f"Camera ID: {args[5]}")
    print(f"Camera Name: {args[6]}")
    
    print("region list")
    print(args[3])
    region_list = convert_rectangle_format(args[3])
    print("region list after")
    print(region_list)

    # Start WebSocket notification thread
    websocket_thread = threading.Thread(
        target=websocket_thread_wrapper, 
        args=(websocket_url,),
        daemon=True
    )
    websocket_thread.start()

    while True:
        try:
            ip = "mediamtx-primary-service"
            place_id = f"{args[12]}"
            ffmpeg_stream_url = f'rtsp://{ip}:8554/live/{place_id}'
            
            # ffmpeg_stream_url = "rtsp://35.222.205.3:8555/live/901"
            print(f"stream is {args[1]}")
            print(f"send to rtsp {ffmpeg_stream_url}")
            # stream_url = "rtsp://35.222.205.3:8555/live/999"
            stream_url = f"{args[1]}"
            webrtc_stream_id =  2147483647 - int(args[12])
            
            cap, frame = initialize_stream(stream_url)
            # frame = resize_frame(frame)
            if cap is None or frame is None:
                print("Failed to initialize stream, retrying in 10 seconds...")
                time.sleep(10)
                continue
                
            height, width, _ = frame.shape
            print(f"Stream initialized with resolution: {width}x{height}")
            
            ffmpeg_process = start_ffmpeg_process(width, height, ffmpeg_stream_url)
            if ffmpeg_process is None:
                print("Failed to start FFmpeg process, retrying in 10 seconds...")
                time.sleep(10)
                continue

            # Create a thread-safe queue for frame writing
            # frame_queue = queue.Queue(maxsize=30)

            # Start frame writer thread
            # frame_writer = threading.Thread(
            #     target=frame_writer_thread, 
            #     args=(ffmpeg_process, frame_queue), 
            #     daemon=True
            # )
            # frame_writer.start()
            
            # RTSP stream or video file
            cap = cv2.VideoCapture(stream_url)

            if not cap.isOpened():
                print("Error: Could not open RTSP stream.")
                time.sleep(5)
                continue

            # Load YOLO model with optimizations
            model = YOLO(args[0], gpu_id=torch.cuda.current_device())
            
            # Configure model for lower computational overhead
            model.overrides.update({
                'imgsz': (640, 640),  # Smaller input size reduces computation
                'conf': 0.5,  # Higher confidence threshold reduces unnecessary detections
                'iou': 0.45,  # Adjust IOU threshold for more efficient NMS
            })

            # Initialize FPS calculation
            frame_count = 0
            processed_frame_count = 0
            start_time = time.time()
            fps = 0
            old_boxes = None
            consecutive_failures = 0
            max_consecutive_failures = 5
            ffmpeg_restart_delay = 5
            last_data_sent = 0
            
            # Last time we cleaned up lost objects
            last_cleanup_time = time.time()

            while True:
                ret, frame = cap.read()
                # frame = resize_frame(frame)
                if not ret:
                    consecutive_failures += 1
                    print(f"Failed to grab frame (attempt {consecutive_failures}/{max_consecutive_failures})")
                    
                    if consecutive_failures >= max_consecutive_failures:
                        print("Too many consecutive failures, reinitializing stream...")
                        break
                    
                    # Quick retry
                    cap.release()
                    time.sleep(0.1)
                    cap = cv2.VideoCapture(stream_url)
                    continue

                consecutive_failures = 0

                # Check if it's time to clean up lost objects (do this every second)
                current_time = time.time()
                if current_time - last_cleanup_time > 1.0:
                    cleanup_lost_objects(region_list, args)
                    last_cleanup_time = current_time

                # FPS Calculation
                processed_frame_count += 1
                if processed_frame_count % 30 == 0:  # Calculate FPS less frequently
                    current_time = perf_counter = time.time()
                    fps = processed_frame_count / (current_time - start_time)
                    start_time = current_time
                    processed_frame_count = 0
                cv2.putText(frame, f"FPS: {fps:.2f}", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                
                # Draw the regions on the frame
                frame = draw_regions(frame, region_list)

                # Skip frames to reduce processing load
                if frame_count % FRAME_SKIP != 0:
                    frame_count += 1
                    if old_boxes is not None:
                        for box in old_boxes:
                            if box.id is None:
                                continue
                                
                            obj_id = int(box.id[0].item())
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            conf = box.conf[0].item()
                            class_id = int(box.cls[0].item())
                            class_name = model.names[class_id]
                            
                            # Calculate center of the bounding box
                            center_x = (x1 + x2) // 2
                            center_y = (y1 + y2) // 2
                            current_pos = (center_x, center_y)
                            
                            # Update the last seen timestamp
                            object_last_seen[obj_id] = time.time()
                            
                            # Display basic detection info
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(frame, f"{class_name} {conf:.2f}", (x1, y1 - 10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                            cv2.putText(frame, f"ID: {obj_id}", (x1, y1 - 30), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                            
                            # Show elapsed time for each region if object is present
                            if obj_id in object_in_region:
                                y_offset = y1 - 50
                                for region_idx, elapsed_time in object_in_region[obj_id].items():
                                    # Update elapsed time since we're skipping frames
                                    current_elapsed = time.time() - (object_in_region[obj_id][region_idx])
                                    time_str = f"Region {region_idx}: {current_elapsed:.1f}s"
                                    cv2.putText(frame, time_str, (x1, y_offset), 
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                                    y_offset -= 20
                            
                    # Add frame to queue for writing
                    # try:
                    #     if not frame_queue.full():
                    #         frame_queue.put_nowait(frame)
                    # except queue.Full:
                    #     pass
                    # cv2.imshow("YOLO Region Tracker", frame)
                    # if cv2.waitKey(1) & 0xFF == ord('q'):
                    #     break
                    try:
                        ffmpeg_process = handle_ffmpeg_process(frame, ffmpeg_process, width, height, ffmpeg_stream_url)
                    except BrokenPipeError:
                        print("FFmpeg process has terminated, restarting...")
                        kill_ffmpeg_process(ffmpeg_process)
                        time.sleep(ffmpeg_restart_delay)
                        ffmpeg_process = start_ffmpeg_process(width, height, ffmpeg_stream_url)
                    continue

                # Run YOLO inference with tracking
                results = model.track(
                    source=frame, 
                    show=False, 
                    persist=True, 
                    tracker="bytetrack.yaml",
                    verbose=False  # Disable verbose logging
                )

                total_occupation = 0
                max_waiting_time = 0
                # Process detections
                if results and results[0].boxes is not None:
                    old_boxes = results[0].boxes
                    for box in results[0].boxes:
                        # Object ID tracking
                        obj_id = int(box.id[0].item()) if box.id is not None else None
                        if obj_id is None:
                            continue

                        x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
                        conf = box.conf[0].item()  # Confidence score
                        class_id = int(box.cls[0].item())  # Class ID
                        class_name = model.names[class_id]  # Class name
                        label = f"{class_name} {conf:.2f}"

                        # Calculate center of the bounding box
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2
                        current_pos = (center_x, center_y)

                        # Draw bounding box and label
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        cv2.putText(frame, f"ID: {obj_id}", (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                        # Update the tracker with the current position
                        object_tracker[obj_id] = current_pos
                        
                        # Check if the object is in any region and get elapsed time
                        region_presence = check_region_presence(obj_id, current_pos, region_list, args)
                        
                        # Display elapsed time for each region
                        y_offset = y1 - 50
                        for region_idx, elapsed_time in region_presence.items():
                            time_str = f"Region {region_idx}: {elapsed_time:.1f}s"
                            cv2.putText(frame, time_str, (x1, y_offset), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                            y_offset -= 20
                            total_occupation += 1
                            max_waiting_time = max(max_waiting_time, elapsed_time)
                    # send total_occupation and max_waiting_time to websocket
                    if max_waiting_time > 0 and last_data_sent + SEND_DATA_EVERY < time.time():
                        last_data_sent = time.time()
                        payload = {
                            'location': args[4],
                            'max_waiting_time': round(max_waiting_time, 2),
                            'occupation': total_occupation,
                            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                            'camera': int(args[5]),
                            'camera_name': args[6],
                            'detection': '{}',
                            'model': 'ZONE',
                            'camera_type': args[10]
                        }
                        try:
                            websocket_queue.put_nowait(payload)
                        except queue.Full:
                            print("WebSocket queue full, skipping notification")
                # Add frame to queue for writing
                # try:
                #     if not frame_queue.full():
                #         frame_queue.put_nowait(frame)
                # except queue.Full:
                #     pass
                try:
                    ffmpeg_process = handle_ffmpeg_process(frame, ffmpeg_process, width, height, ffmpeg_stream_url)
                except BrokenPipeError:
                    print("FFmpeg process has terminated, restarting...")
                    kill_ffmpeg_process(ffmpeg_process)
                    time.sleep(ffmpeg_restart_delay)
                    ffmpeg_process = start_ffmpeg_process(width, height, ffmpeg_stream_url)
                
                # Show frame with detections
                # cv2.imshow("YOLO Region Tracker", frame)
                # if cv2.waitKey(1) & 0xFF == ord('q'):
                #     break

                # Increment frame count
                frame_count += 1

            # Print final statistics
            # print("Final region counts:")
            # for region_idx, count in region_counters.items():
            #     print(f"Region {region_idx}: {count}")
            
            # Cleanup
            cap.release()
            cv2.destroyAllWindows()

            # When cleaning up
            # try:
            #     frame_queue.put(None, timeout=5)  # Give thread time to process sentinel
            #     frame_writer.join(timeout=5)  # Wait for thread to terminate
            # except queue.Full:
            #     print("Frame queue full, force closing")

        except KeyboardInterrupt:
            print("Exiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
            # Check if FFmpeg needs restart
            if ffmpeg_process.poll() is not None:
                print("FFmpeg process has ended, restarting...")
                kill_ffmpeg_process(ffmpeg_process)
                time.sleep(ffmpeg_restart_delay)
                ffmpeg_process = start_ffmpeg_process(width, height, ffmpeg_stream_url)


