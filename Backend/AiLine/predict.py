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
import os
from Backend.celery import app as solo_worker
import django
import asyncio
import json
import websockets
import datetime
from threading import Thread

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()

from Api.helpers import send_stream_status
from Api.janus_api import main_api

# Goal width for resizing, set to 0 for no resizing
GOAL_WIDTH = 600

def check_line_crossing(obj_id, prev_pos, current_pos, line_list, frame_skip=1):
    """
    Enhanced line crossing detection with better accuracy.
    
    Args:
    - obj_id: Object identifier
    - prev_pos: Previous position (x, y)
    - current_pos: Current position (x, y)
    - line_list: List of lines to check for crossing
    - frame_skip: Number of frames skipped between detections
    
    Returns:
    - Dictionary with crossing information if a crossing occurred, None otherwise
    """
    global object_line_crossing_state, entering_count, exiting_count
    
    if prev_pos is None:
        return None
    
    # Increase number of interpolation points for more granular path tracking
    num_interp_points = max(5, frame_skip * 2)  # At least 5 points, or 2x frame_skip
    
    # Generate dense path between previous and current positions
    path_points = []
    for i in range(num_interp_points + 1):
        t = i / num_interp_points
        x = int(prev_pos[0] * (1 - t) + current_pos[0] * t)
        y = int(prev_pos[1] * (1 - t) + current_pos[1] * t)
        path_points.append((x, y))
    
    # Store trajectory history for this object (up to 10 points)
    if obj_id not in object_motion_points:
        object_motion_points[obj_id] = []
    
    object_motion_points[obj_id].append(current_pos)
    if len(object_motion_points[obj_id]) > 10:
        object_motion_points[obj_id] = object_motion_points[obj_id][-10:]
    
    # Get object direction vector from recent history
    direction_vector = None
    if len(object_motion_points[obj_id]) >= 3:
        # Use multiple points to get a more stable direction
        points = object_motion_points[obj_id]
        dx = points[-1][0] - points[-3][0]
        dy = points[-1][1] - points[-3][1]
        
        # Only use direction if movement is significant
        if abs(dx) > 3 or abs(dy) > 3:
            direction_vector = (dx, dy)
    
    # Initialize crossing state for this object if needed
    if obj_id not in object_line_crossing_state:
        object_line_crossing_state[obj_id] = {}
    
    # Check each segment of the path against each line
    for i in range(len(path_points) - 1):
        p1 = path_points[i]
        p2 = path_points[i + 1]
        
        for line_idx, line in enumerate(line_list):
            line_start = (line[0], line[1])
            line_end = (line[2], line[3])
            line_key = f"line_{line_idx}"
            
            # Skip if this object recently crossed this line (avoid double counting)
            last_cross_time = object_line_crossing_state[obj_id].get(line_key, 0)
            current_time = time.time()
            if current_time - last_cross_time < 1.0:  # 1 second cooldown
                continue
            
            # Improved line intersection check with buffer zone
            if line_segment_intersect_with_buffer(p1, p2, line_start, line_end, buffer=4):
                # Calculate crossing direction using the perpendicular method
                line_vec = (line_end[0] - line_start[0], line_end[1] - line_start[1])
                
                # Determine crossing direction
                if direction_vector:
                    # Use the cross product to determine which side the object is moving to
                    cross_product = line_vec[0] * direction_vector[1] - line_vec[1] * direction_vector[0]
                    
                    # Update counters based on cross product sign (positive is left, negative is right)
                    if cross_product < 0:
                        entering_count += 1
                        crossing_type = "entering"
                    else:
                        exiting_count += 1
                        crossing_type = "exiting"
                    
                    # Mark the time of this crossing
                    object_line_crossing_state[obj_id][line_key] = current_time
                    
                    return {
                        "obj_id": obj_id,
                        "line_idx": line_idx,
                        "crossing_type": crossing_type
                    }
    
    return None

def line_segment_intersect_with_buffer(p1, p2, p3, p4, buffer=2):
    """
    Check if line segments (p1,p2) and (p3,p4) intersect with a small buffer zone.
    
    Args:
    - p1, p2: First line segment endpoints
    - p3, p4: Second line segment endpoints
    - buffer: Buffer distance to make intersection detection more robust
    
    Returns:
    - Boolean indicating if line segments intersect
    """
    # Check standard line intersection
    if line_segment_intersect(p1, p2, p3, p4):
        return True
    
    # If no direct intersection, check distance from points to line segment
    # This helps catch "near miss" crossings
    min_dist = point_to_line_segment_distance(p1, p3, p4)
    min_dist = min(min_dist, point_to_line_segment_distance(p2, p3, p4))
    
    return min_dist <= buffer

def point_to_line_segment_distance(p, line_start, line_end):
    """
    Calculate minimum distance from point p to line segment (line_start, line_end)
    
    Args:
    - p: Point coordinates (x, y)
    - line_start, line_end: Line segment endpoints
    
    Returns:
    - Minimum distance from point to line segment
    """
    x, y = p
    x1, y1 = line_start
    x2, y2 = line_end
    
    # Calculate the squared length of the line segment
    l2 = (x2 - x1)**2 + (y2 - y1)**2
    
    # If line segment is just a point, return distance to that point
    if l2 == 0:
        return math.sqrt((x - x1)**2 + (y - y1)**2)
    
    # Calculate projection of point onto line
    t = ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / l2
    
    # Clamp t to [0,1] for points outside the line segment
    t = max(0, min(1, t))
    
    # Calculate closest point on line segment
    proj_x = x1 + t * (x2 - x1)
    proj_y = y1 + t * (y2 - y1)
    
    # Return distance to this point
    return math.sqrt((x - proj_x)**2 + (y - proj_y)**2)

def extrapolate_position(prev_pos, curr_pos, num_points=5):
    """
    Enhanced position extrapolation with more points for better accuracy
    
    Args:
    - prev_pos: Previous position (x, y)
    - curr_pos: Current position (x, y)
    - num_points: Number of points to generate
    
    Returns:
    - List of extrapolated positions
    """
    if prev_pos is None:
        return []
        
    dx = curr_pos[0] - prev_pos[0]
    dy = curr_pos[1] - prev_pos[1]
    
    # Generate extrapolated positions
    extrapolated = []
    for i in range(1, num_points + 1):
        t = i / (num_points + 1)
        x = prev_pos[0] + dx * t
        y = prev_pos[1] + dy * t
        extrapolated.append((int(x), int(y)))
    
    return extrapolated

def calculate_object_velocity(obj_id, current_pos, timestamp, velocity_history=None):
    """
    Calculate and smooth object velocity for improved direction detection
    
    Args:
    - obj_id: Object identifier
    - current_pos: Current position (x, y)
    - timestamp: Current timestamp
    - velocity_history: Dictionary to store velocity history
    
    Returns:
    - Velocity vector (dx, dy) per second
    """
    if velocity_history is None:
        velocity_history = {}
    
    if obj_id not in velocity_history:
        velocity_history[obj_id] = {
            'positions': [],
            'timestamps': [],
            'velocity': (0, 0)
        }
    
    # Add current position and timestamp
    history = velocity_history[obj_id]
    history['positions'].append(current_pos)
    history['timestamps'].append(timestamp)
    
    # Keep only last 5 positions for velocity calculation
    if len(history['positions']) > 5:
        history['positions'] = history['positions'][-5:]
        history['timestamps'] = history['timestamps'][-5:]
    
    # Need at least 2 positions to calculate velocity
    if len(history['positions']) < 2:
        return (0, 0)
    
    # Calculate velocity using the two most recent positions
    p1 = history['positions'][-2]
    p2 = history['positions'][-1]
    t1 = history['timestamps'][-2]
    t2 = history['timestamps'][-1]
    
    time_diff = t2 - t1
    if time_diff <= 0:
        return history['velocity']  # Use previous velocity if time difference is invalid
    
    dx = (p2[0] - p1[0]) / time_diff
    dy = (p2[1] - p1[1]) / time_diff
    
    # Smooth velocity using exponential moving average
    alpha = 0.3  # Smoothing factor
    vx_old, vy_old = history['velocity']
    vx_new = alpha * dx + (1 - alpha) * vx_old
    vy_new = alpha * dy + (1 - alpha) * vy_old
    
    # Update stored velocity
    history['velocity'] = (vx_new, vy_new)
    
    return (vx_new, vy_new)

def get_line_orientation(line):
    """
    Calculate line orientation vector and normal vector
    
    Args:
    - line: Line coordinates [x1, y1, x2, y2]
    
    Returns:
    - Tuple of (orientation_vector, normal_vector)
    """
    x1, y1, x2, y2 = line
    
    # Line orientation vector
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx*dx + dy*dy)
    
    if length > 0:
        # Normalized orientation vector
        orientation = (dx/length, dy/length)
        
        # Normal vector (perpendicular to orientation)
        normal = (-dy/length, dx/length)
        
        return (orientation, normal)
    else:
        return ((0, 0), (0, 0))

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

async def websocket_sender_loop(websocket_url, location, camera_id, camera_name, camera_type, model):
    """
    Main WebSocket sender loop that maintains a persistent connection and reconnects if needed
    """
    global entering_count, exiting_count, previous_entering, previous_exiting
    
    while True:
        try:
            # Connect to WebSocket server
            async with websockets.connect(websocket_url) as websocket:
                print(f"WebSocket connected to {websocket_url}")
                
                while True:
                    try:
                        # Check if counts have changed
                        if entering_count != previous_entering or exiting_count != previous_exiting:
                            # Update previous counts
                            previous_entering = entering_count
                            previous_exiting = exiting_count
                            
                            # Generate current timestamp
                            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                            
                            # Create payload
                            payload = {
                                'in': entering_count,
                                'out': exiting_count,
                                'location': location,
                                'date': current_time,
                                'camera': camera_id,
                                'camera_name': camera_name,
                                'camera_type': camera_type,
                                'model': model
                            }
                            
                            # Convert payload to JSON
                            payload_json = json.dumps(payload)
                            
                            # Send data to WebSocket server on realtime_line event
                            await websocket.send(
                                json.dumps({
                                    'event': 'realtime_line',
                                    'data': payload_json
                                })
                            )
                            # print(f"WebSocket data sent successfully: {payload}")
                        
                        # Wait before next check
                        await asyncio.sleep(1)  # Check every second
                        
                    except websockets.exceptions.ConnectionClosed:
                        print("WebSocket connection closed, reconnecting...")
                        break  # Break inner loop to reconnect
                    except Exception as e:
                        print(f"Error in WebSocket communication: {e}")
                        await asyncio.sleep(5)  # Wait before retrying
                        break  # Break inner loop to reconnect
                        
        except Exception as e:
            print(f"WebSocket connection error: {e}, retrying in 5 seconds...")
            await asyncio.sleep(5)  # Wait before reconnecting

def websocket_sender_thread(websocket_url, location, camera_id, camera_name, camera_type, model):
    """
    Thread function to run the WebSocket sender loop
    """
    # Set up the event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run the sender loop indefinitely
        loop.run_until_complete(
            websocket_sender_loop(websocket_url, location, camera_id, camera_name, camera_type, model)
        )
    except Exception as e:
        print(f"WebSocket thread fatal error: {e}")
    finally:
        loop.close()

# Dictionary to store previous positions of tracked objects
object_tracker = {}
object_motion_points = {}
object_line_crossing_state = {}

# Counters for entering and exiting
entering_count = 0
exiting_count = 0

previous_entering = 0
previous_exiting = 0

# Frame skipping parameters
FRAME_SKIP = 4

def create_line_mask(frame_shape, lines, mask_width=100):
    """
    Generate a mask focused around the specified lines.

    Example:
        Create mask based on lines
            mask = create_line_mask(frame.shape, line_list, mask_width=100)
        Apply mask to frame
            masked_frame = cv2.bitwise_and(frame, frame, mask=mask)
        
        Optional: Visualize the mask (for debugging)
            mask_visualization = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            mask_visualization = cv2.addWeighted(mask_visualization, 0.5, frame, 0.5, 0)
            cv2.imshow("Mask", mask_visualization)
    
    Args:
    - frame_shape: Shape of the input frame (height, width, channels)
    - lines: List of line coordinates [(x1,y1,x2,y2), ...]
    - mask_width: Width of the white region around the lines
    
    Returns:
    - Mask with white regions around the lines
    """
    # Create a black mask
    mask = np.zeros(frame_shape[:2], dtype=np.uint8)
    
    for line in lines:
        x1, y1, x2, y2 = line
        
        # Calculate line vector
        line_vec = np.array([x2 - x1, y2 - y1])
        line_length = np.linalg.norm(line_vec)
        
        # Normalize line vector
        if line_length > 0:
            line_unit_vec = line_vec / line_length
        else:
            continue
        
        # Perpendicular vector (rotate 90 degrees)
        perp_vec = np.array([-line_unit_vec[1], line_unit_vec[0]])
        
        # Create polygon points for the mask region
        pts = np.array([
            (x1 + perp_vec[0] * mask_width/2, y1 + perp_vec[1] * mask_width/2),
            (x1 - perp_vec[0] * mask_width/2, y1 - perp_vec[1] * mask_width/2),
            (x2 - perp_vec[0] * mask_width/2, y2 - perp_vec[1] * mask_width/2),
            (x2 + perp_vec[0] * mask_width/2, y2 + perp_vec[1] * mask_width/2)
        ], dtype=np.int32)
        
        # Fill the polygon with white
        cv2.fillPoly(mask, [pts], 255)
    
    return mask

def line_segment_intersect(p1, p2, p3, p4):
    """
    Check if line segments (p1,p2) and (p3,p4) intersect.
    
    Args:
    - p1, p2: First line segment endpoints
    - p3, p4: Second line segment endpoints
    
    Returns:
    - Boolean indicating if line segments intersect
    """
    def ccw(A, B, C):
        """Check counterclockwise turn"""
        return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

def extrapolate_position(prev_pos, curr_pos, num_skipped_frames):
    """
    Extrapolate potential position based on previous and current positions
    
    Args:
    - prev_pos: Previous position
    - curr_pos: Current position
    - num_skipped_frames: Number of frames skipped
    
    Returns:
    - Extrapolated positions list
    """
    dx = curr_pos[0] - prev_pos[0]
    dy = curr_pos[1] - prev_pos[1]
    
    # Generate interpolated positions
    extrapolated_positions = []
    for i in range(1, num_skipped_frames + 1):
        interp_x = prev_pos[0] + (dx * i / (num_skipped_frames + 1))
        interp_y = prev_pos[1] + (dy * i / (num_skipped_frames + 1))
        extrapolated_positions.append((int(interp_x), int(interp_y)))
    
    return extrapolated_positions


def draw_perpendicular_arrow(frame, line):
    """
    Draw a 90-degree arrow perpendicular to the line indicating entering direction.
    """
    x1, y1, x2, y2 = line
    # Calculate the midpoint of the line
    mid_x = (x1 + x2) // 2
    mid_y = (y1 + y2) // 2
    
    # Calculate line vector
    dx = x2 - x1
    dy = y2 - y1
    
    # Calculate perpendicular vector (rotate 90 degrees)
    perp_dx = -dy
    perp_dy = dx
    
    # Normalize the perpendicular vector
    line_length = math.sqrt(perp_dx**2 + perp_dy**2)
    arrow_length = min(50, line_length // 4)
    norm_perp_x = perp_dx / line_length * arrow_length
    norm_perp_y = perp_dy / line_length * arrow_length
    
    # Calculate arrow points
    arrow_base_x = int(mid_x + norm_perp_x)
    arrow_base_y = int(mid_y + norm_perp_y)
    arrow_tip_x = int(mid_x - norm_perp_x)
    arrow_tip_y = int(mid_y - norm_perp_y)
    
    # Draw the perpendicular arrow
    cv2.arrowedLine(frame, 
                    (arrow_base_x, arrow_base_y), 
                    (arrow_tip_x, arrow_tip_y), 
                    (0, 255, 255),  # Bright yellow color
                    2)  # Line thickness

def parse_lines(line_arg):
    """
    Parses the command-line argument for multiple line coordinates.
    Handles input strings with square brackets like '[848,138,597,573,306,148,405,658]'
    and returns a list of line coordinates, where each line is represented by [x1, y1, x2, y2].
    """
    try:
        # Remove the outer square brackets if present
        cleaned_arg = line_arg.strip()
        if cleaned_arg.startswith('[') and cleaned_arg.endswith(']'):
            cleaned_arg = cleaned_arg[1:-1]
        
        # Convert the input string into a list of integers
        values = [int(x.strip()) for x in cleaned_arg.split(',')]
        
        # Check if the total number of values is a multiple of 4
        if len(values) % 4 != 0:
            raise ValueError(f"Total number of coordinates ({len(values)}) must be a multiple of 4")
        
        # Group values into sets of 4
        lines = [values[i:i+4] for i in range(0, len(values), 4)]
        
        return lines
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing line argument: {e}")
        exit(1)

def resize_frame(frame, scale_percent=40):
    # return frame
    """Resize frame by percentage"""
    scale_percent = (720 / frame.shape[1]) * 100

    width = int(frame.shape[1] * scale_percent / 100)
    height = int(frame.shape[0] * scale_percent / 100)
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
@solo_worker.task
def main(*args ,**kwargs):
    import os 
    import redis 
   
    # Set CUDA_VISIBLE_DEVICES dynamically from args if provided
    gpu_id = args[13] if len(args) > 13 else 0
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    
    import torch
    print("Initializing main function with args:")
    for i, arg in enumerate(args):
        print(f"Arg {i}: {arg}\n")
    print("CUDA available:", torch.cuda.is_available())
    print("CUDA version:", torch.version.cuda)
    print("PyTorch version:", torch.__version__)
    torch.cuda.set_device(0)  # Always 0 because CUDA_VISIBLE_DEVICES is set to the correct global GPU
    print(f"Current CUDA device: {torch.cuda.current_device()}")
    print(f"Args: {args}")

    # Parse arguments for WebSocket
    location = args[4]
    camera_id = int(args[5])
    camera_name = args[9]
    camera_type = args[10]
    model = args[8]
    websocket_url = args[7]
    
    # Start WebSocket sender thread
    websocket_thread = Thread(
        target=websocket_sender_thread,
        args=(websocket_url, location, camera_id, camera_name, camera_type, model),
        daemon=True
    )
    websocket_thread.start()

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

    line_list = parse_lines(args[3])
    print(line_list)
    global entering_count, exiting_count
    
    while True:
        try:
            ip = "mediamtx-primary-service"  # Default IP for RTSP stream
            place_id = f"{args[12]}"
            ffmpeg_stream_url = f'rtsp:/{ip}:8554/live/{place_id}'
            
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
            
            # RTSP stream or video file
            cap = cv2.VideoCapture(stream_url)

            if not cap.isOpened():
                print("Error: Could not open RTSP stream.")
                time.sleep(5)
                continue

            # Load YOLO model with optimizations
            model = YOLO("/app/Backend/AiLine/ppl.pt")
            
            # Configure model for lower computational overhead
            model.overrides.update({
                'imgsz': (640, 640),  # Smaller input size reduces computation
                'conf': 0.5,  # Higher confidence threshold reduces unnecessary detections
                'iou': 0.45,  # Adjust IOU threshold for more efficient NMS
                'batch': 1,  # Set batch size to 1
                'device': 0,
            })

            # Initialize FPS calculation
            frame_count = 0
            processed_frame_count = 0
            start_time = time.perf_counter()
            fps = 0
            old_boxes = None
            consecutive_failures = 0
            max_consecutive_failures = 5
            ffmpeg_restart_delay = 5

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

                # FPS Calculation
                processed_frame_count += 1
                if processed_frame_count % 30 == 0:  # Calculate FPS less frequently
                    current_time = time.perf_counter()
                    fps = processed_frame_count / (current_time - start_time)
                    start_time = current_time
                    processed_frame_count = 0
                cv2.putText(frame, f"FPS: {fps:.2f}", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                
                for line in line_list:
                    cv2.line(frame, (line[0], line[1]), (line[2], line[3]), (0, 0, 255), 2)
                    draw_perpendicular_arrow(frame, line)
                cv2.putText(frame, f"Entering: {entering_count}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, f"Exiting: {exiting_count}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                # Skip frames to reduce processing load
                if frame_count % FRAME_SKIP != 0:
                    frame_count += 1
                    for box in old_boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = box.conf[0].item()
                        class_id = int(box.cls[0].item())
                        class_name = model.names[class_id]
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"{class_name} {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        if box.id is not None:
                            cv2.putText(frame, f"ID: {int(box.id[0].item())}", (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                    # cv2.imshow("YOLO People Counter", frame)
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
                    verbose=False,
                    device=0, # Always 0 because CUDA_VISIBLE_DEVICES is set
                    conf=0.1,
                    iou=0.45,
                )

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

                        prev_pos = object_tracker.get(obj_id, None)
                        # Update the tracker with the current position
                        object_tracker[obj_id] = current_pos
                        
                        if prev_pos is not None:
                            cv2.putText(frame, f"ID: {obj_id}", (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)                        
                            # Check each consecutive pair of points in the path
                            crossing_info = check_line_crossing(obj_id, prev_pos, current_pos, line_list, frame_skip=FRAME_SKIP)
                            # if crossing_info:
                            #     print(f"Object {obj_id} crossed line {crossing_info['line_idx']} by {crossing_info['crossing_type']}")
                            # Update object position
                            object_tracker[obj_id] = current_pos
                # Show frame with detections
                # cv2.imshow("YOLO People Counter", frame)
                # if cv2.waitKey(1) & 0xFF == ord('q'):
                #     break
                try:
                    ffmpeg_process = handle_ffmpeg_process(frame, ffmpeg_process, width, height, ffmpeg_stream_url)
                except BrokenPipeError:
                    print("FFmpeg process has terminated, restarting...")
                    kill_ffmpeg_process(ffmpeg_process)
                    time.sleep(ffmpeg_restart_delay)
                    ffmpeg_process = start_ffmpeg_process(width, height, ffmpeg_stream_url)

                # Increment frame count
                frame_count += 1

            # print(f"Entering: {entering_count}, Exiting: {exiting_count}")
            
            # Cleanup
            cap.release()
            # cv2.destroyAllWindows()

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


