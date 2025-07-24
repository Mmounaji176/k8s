import face_recognition
import cv2
import numpy as np
import os, sys
from os import listdir
from PIL import Image
from progress.bar import Bar
import threading
from os import path
import pickle
from datetime import datetime
import shutil
import torch
from ultralytics import YOLO
from ultralytics.yolo.utils import LOGGER

def get_local_cuda_index(global_gpu_id):
    """Given a global GPU ID, return the local index in CUDA_VISIBLE_DEVICES."""
    cuda_devices = os.environ.get('CUDA_VISIBLE_DEVICES', '0')
    device_list = [int(x) for x in cuda_devices.split(',')]
    return device_list.index(global_gpu_id)

def load_encodings():
    encodings_file = 'known_face_encodings.pkl'
    if path.exists(encodings_file):
        with open(encodings_file, 'rb') as file:
            return pickle.load(file)
    else:
        return [], []

def save_encodings(known_face_encodings, known_face_names):
    encodings_file = 'known_face_encodings.pkl'
    with open(encodings_file, 'wb') as file:
        pickle.dump((known_face_encodings, known_face_names), file)

known_face_encodings, known_face_names = load_encodings()

if not known_face_encodings or not known_face_names:
    main_dir = "./database_b/"
    files = listdir(main_dir)
    images_list = [i for i in files if i.endswith('.jpg')]

    with Bar('Loading database in processing...', max=len(images_list)) as bar:
        for idx, image in enumerate(images_list):
            print(main_dir + image)
            img = face_recognition.load_image_file(main_dir + image)
            face_encodings = face_recognition.face_encodings(img)

            if face_encodings:
                known_face_encodings.append(face_encodings[0])
                known_face_names.append(images_list[idx][:-4])
            else:
                print(f"No face detected in {main_dir + image}")

            bar.next()

    save_encodings(known_face_encodings, known_face_names)

print(known_face_names)

def face_recognition_worker(frame, i, gpu_id):
    # Map global GPU ID to local CUDA index
    local_index = get_local_cuda_index(gpu_id)
    # Set CUDA device for PyTorch
    if torch.cuda.is_available():
        torch.cuda.set_device(local_index)
    
    rgb_frame = frame[:, :, ::-1]
    code = cv2.COLOR_BGR2RGB
    rgb_frame = cv2.cvtColor(rgb_frame, code)
    face_locations = face_recognition.face_locations(rgb_frame, number_of_times_to_upsample=0, model="cnn")
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    face_names = []
    index = 0
    save_frame = rgb_frame
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, 1)
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argsort(face_distances)[:3]
        
        if face_distances[best_match_index[0]] <= 0.40:
            best_match_index = best_match_index[0]
            name = known_face_names[best_match_index]
            face_names.append(name)
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
            
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            directory_path = f"./cci_cafet_face/known/{name}"
            if not os.path.exists(directory_path):
                os.mkdir(directory_path)
            
            index += 1
            out_path = f"./cci_cafet_face/known/{name}"
            source_file = f"./database_b/{name}.jpg"
            destination_file = os.path.join(out_path, f"database_b{name}.jpg")
            if not os.path.exists(destination_file):
                shutil.copy(source_file, out_path)
            
            frame_name = f"Index_{index}_Frame_{name}_{current_time}.jpg"
            cv2.imwrite(os.path.join(out_path, frame_name), frame)
            cv2.imwrite(os.path.join(out_path, f"_Original_{frame_name}"), save_frame)
        else:
            best_match_indexes = best_match_index
            unknown = ["unknown"] * len(face_locations)
            for (top, right, bottom, left), name in zip(face_locations, unknown):
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
            
            for best_match_index in best_match_indexes:
                name = known_face_names[best_match_index]
                face_names.append(name)
                
                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")
                directory_path = f"./cci_cafet_face/unknowns/{current_time}/"
                if not os.path.exists(directory_path):
                    os.mkdir(directory_path)
                
                index += 1
                out_path = f"./cci_cafet_face/unknowns/{current_time}/"
                source_file = f"./database_b/{name}.jpg"
                destination_file = os.path.join(out_path, f"database_b{name}.jpg")
                if not os.path.exists(destination_file):
                    shutil.copy(source_file, out_path)
                
                frame_name = f"Index_{index}_Frame_{name}_{current_time}.jpg"
                cv2.imwrite(os.path.join(out_path, frame_name), frame)
                cv2.imwrite(os.path.join(out_path, f"_Original_{frame_name}"), save_frame)

class StreamProcessor:
    def __init__(self, model_path='yolov8n.pt', skip_frames=5, gpu_id=0):
        """
        Initialize the stream processor.

        Args:
            model_path (str): Path to the YOLO model
            skip_frames (int): Number of frames to skip between predictions
            gpu_id (int): Global GPU ID to use
        """
        self.skip_frames = skip_frames
        self.frame_count = 0
        self.gpu_device = get_local_cuda_index(gpu_id)
        LOGGER.info(f"Initializing StreamProcessor on GPU {self.gpu_device}")
        # Load model
        self.model = YOLO(model_path, gpu_id=gpu_id)
        if torch.cuda.is_available():
            self.model = self.model.to(f'cuda:{self.gpu_device}')
        else:
            self.model = self.model.to('cpu')

    def process_frame(self, frame):
        """
        Process a single frame.

        Args:
            frame (numpy.ndarray): Input frame

        Returns:
            tuple: (processed_frame, detections)
        """
        self.frame_count += 1
        
        # Skip frames if needed
        if self.frame_count % self.skip_frames != 0:
            return frame, None

        # Run prediction
        results = self.model(frame)
        
        # Process results
        processed_frame = frame.copy()
        detections = []
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                cls = box.cls[0].cpu().numpy()
                
                # Draw bounding box
                cv2.rectangle(processed_frame, 
                            (int(x1), int(y1)), 
                            (int(x2), int(y2)), 
                            (0, 255, 0), 2)
                
                # Add label
                label = f"{self.model.names[int(cls)]} {conf:.2f}"
                cv2.putText(processed_frame, 
                          label, 
                          (int(x1), int(y1) - 10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 
                          0.5, 
                          (0, 255, 0), 
                          2)
                
                detections.append({
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'confidence': float(conf),
                    'class': int(cls)
                })
        
        return processed_frame, detections

    def process_stream(self, stream_url):
        """
        Process a video stream.

        Args:
            stream_url (str): URL of the video stream
        """
        cap = cv2.VideoCapture(stream_url)
        
        if not cap.isOpened():
            LOGGER.error(f"Failed to open stream: {stream_url}")
            return
        
        LOGGER.info(f"Processing stream: {stream_url}")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                LOGGER.warning("Failed to read frame from stream")
                break
            
            # Process frame
            processed_frame, detections = self.process_frame(frame)
            
            # Display results
            cv2.imshow('Stream', processed_frame)
            
            # Break on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()

def main():
    # Get GPU device and node type
    gpu_device = get_local_cuda_index(0)
    LOGGER.info(f"Starting stream processing on GPU {gpu_device}")
    
    # Initialize stream processor
    processor = StreamProcessor(skip_frames=5)
    
    # Process stream
    import os
    stream_url = os.environ.get("STREAM_URL")
    if not stream_url:
        LOGGER.warning("STREAM_URL environment variable not set. Using default fallback URL.")
        stream_url = "rtsp://your_stream_url"
    processor.process_stream(stream_url)

if __name__ == "__main__":
    main()