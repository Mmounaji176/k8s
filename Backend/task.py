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
from celery import Task
from ultralytics import YOLO
from ultralytics.yolo.engine.predictor import BasePredictor
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

            bar.next()

    save_encodings(known_face_encodings, known_face_names)

print(known_face_names)

def face_recognition_worker(frame, gpu_id):
    # Map global GPU ID to local CUDA index
    local_index = get_local_cuda_index(gpu_id)
    if torch.cuda.is_available():
        torch.cuda.set_device(local_index)
    
    code = cv2.COLOR_BGR2RGB
    rgb_frame2 = frame[:, :, ::-1]

    rgb_frame = cv2.cvtColor(rgb_frame2, code)
    face_locations = face_recognition.face_locations(rgb_frame, number_of_times_to_upsample=0, model="cnn")
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    face_names = []
    index = 0
    save_frame = rgb_frame
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, 1)
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argsort(face_distances)[:3]
        
        if face_distances[best_match_index[0]] <= 0.44:
            best_match_index = best_match_index[0]
            name = known_face_names[best_match_index]
            face_names.append(name)
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
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
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
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
    
    del rgb_frame
    del face_locations
    del face_names
    del face_encodings
    del save_frame
    del frame

def mainloop(rtsp_url, place, gpu_id):
    video_capture = cv2.VideoCapture(rtsp_url)
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

                bar.next()

    save_encodings(known_face_encodings, known_face_names)
    process_this_frame = True
    
    if not video_capture.isOpened():
        print("Error opening video source:", video_capture.isOpened())
        exit(1)
    
    while True:
        ret, frame = video_capture.read()
        
        if process_this_frame and ret:
            face_recognition_worker(frame, gpu_id)
        
        process_this_frame = not process_this_frame

    video_capture.release()
    cv2.destroyAllWindows()

class YOLOPredictor(BasePredictor):
    def __init__(self, gpu_id, overrides=None):
        super().__init__(overrides)
        self.gpu_device = get_local_cuda_index(gpu_id)
        LOGGER.info(f"Initializing YOLOPredictor on GPU {self.gpu_device}")

    def setup_model(self, model, verbose=True):
        """Initialize YOLO model with given parameters and set it to evaluation mode."""
        if model is None:
            model = self.args.model

        # Set device for the model
        if torch.cuda.is_available():
            model = model.to(f'cuda:{self.gpu_device}')
        else:
            model = model.to('cpu')

        model.eval()
        self.model = model
        self.device = model.device
        self.args.half = self.device.type != 'cpu'  # force FP16 val during training

        return model

class YOLOTask(Task):
    _model = None
    _predictor = None

    def __init__(self, gpu_id):
        super().__init__()
        self.gpu_id = gpu_id

    @property
    def model(self):
        if self._model is None:
            self._model = YOLO('yolov8n.pt', gpu_id=self.gpu_id)
            gpu_device = get_local_cuda_index(self.gpu_id)
            LOGGER.info(f"Loading YOLO model on GPU {gpu_device}")
            if torch.cuda.is_available():
                self._model = self._model.to(f'cuda:{gpu_device}')
        return self._model

    @property
    def predictor(self):
        if self._predictor is None:
            self._predictor = YOLOPredictor(self.gpu_id)
            self._predictor.setup_model(self.model)
        return self._predictor

    def predict(self, image):
        """
        Run prediction on an image.

        Args:
            image (numpy.ndarray): Input image

        Returns:
            dict: Prediction results
        """
        gpu_device = get_local_cuda_index(self.gpu_id)
        LOGGER.info(f"Running prediction on GPU {gpu_device}")

        # Run prediction
        results = self.predictor(image)
        
        # Process results
        processed_results = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                cls = box.cls[0].cpu().numpy()
                processed_results.append({
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'confidence': float(conf),
                    'class': int(cls)
                })
        
        return processed_results

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        LOGGER.error(f"Task {task_id} failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry"""
        LOGGER.warning(f"Task {task_id} retrying: {exc}")
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        LOGGER.info(f"Task {task_id} completed successfully")
        super().on_success(retval, task_id, args, kwargs)

if __name__ == "__main__":
    mainloop()