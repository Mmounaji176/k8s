# Ultralytics YOLO 🚀, GPL-3.0 license

import hydra
import torch
import argparse
import time
from pathlib import Path
import schedule
import cv2
import torch
import torch.backends.cudnn as cudnn
from numpy import random
from ultralytics.yolo.engine.predictor import BasePredictor
from ultralytics.yolo.utils import DEFAULT_CONFIG, ROOT, ops
from ultralytics.yolo.utils.checks import check_imgsz
from ultralytics.yolo.utils.plotting import Annotator, colors, save_one_box
import json
import cv2
from deep_sort_pytorch.utils.parser import get_config
from deep_sort_pytorch.deep_sort import DeepSort
from collections import deque
import numpy as np
from websockets.sync.client import connect as websocketConnect
from datetime import datetime
palette = (2 ** 11 - 1, 2 ** 15 - 1, 2 ** 20 - 1)
user_timings = {}  # Add this line
# data_deque = {}
# deepsort = None
limitsUp = [57,192,306,148]
limitsDown = [449,401,633,339]
totalCountUp = []
totalCountDown = []
entry_time = {}
def init_tracker():
    global deepsort
    cfg_deep = get_config()
    cfg_deep.merge_from_file("deep_sort_pytorch/configs/deep_sort.yaml")

    deepsort= DeepSort(cfg_deep.DEEPSORT.REID_CKPT,
                            max_dist=cfg_deep.DEEPSORT.MAX_DIST, min_confidence=cfg_deep.DEEPSORT.MIN_CONFIDENCE,
                            nms_max_overlap=cfg_deep.DEEPSORT.NMS_MAX_OVERLAP, max_iou_distance=cfg_deep.DEEPSORT.MAX_IOU_DISTANCE,
                            max_age=cfg_deep.DEEPSORT.MAX_AGE, n_init=cfg_deep.DEEPSORT.N_INIT, nn_budget=cfg_deep.DEEPSORT.NN_BUDGET,
                            use_cuda=True)
##########################################################################################
def xyxy_to_xywh(*xyxy):
    """" Calculates the relative bounding box from absolute pixel values. """
    bbox_left = min([xyxy[0].item(), xyxy[2].item()])
    bbox_top = min([xyxy[1].item(), xyxy[3].item()])
    bbox_w = abs(xyxy[0].item() - xyxy[2].item())
    bbox_h = abs(xyxy[1].item() - xyxy[3].item())
    x_c = (bbox_left + bbox_w / 2)
    y_c = (bbox_top + bbox_h / 2)
    w = bbox_w
    h = bbox_h
    return x_c, y_c, w, h

def xyxy_to_tlwh(bbox_xyxy):
    tlwh_bboxs = []
    for i, box in enumerate(bbox_xyxy):
        x1, y1, x2, y2 = [int(i) for i in box]
        top = x1
        left = y1
        w = int(x2 - x1)
        h = int(y2 - y1)
        tlwh_obj = [top, left, w, h]
        tlwh_bboxs.append(tlwh_obj)
    return tlwh_bboxs

def compute_color_for_labels(label):
    """
    Simple function that adds fixed color depending on the class
    """
    if label == 0: #person
        color = (85,45,255)
    elif label == 2: # Car
        color = (222,82,175)
    elif label == 3:  # Motobike
        color = (0, 204, 255)
    elif label == 5:  # Bus
        color = (0, 149, 255)
    else:
        color = [int((p * (label ** 2 - label + 1)) % 255) for p in palette]
    return tuple(color)

def draw_border(img, pt1, pt2, color, thickness, r, d):
    x1,y1 = pt1
    x2,y2 = pt2
    # Top left
    cv2.line(img, (x1 + r, y1), (x1 + r + d, y1), color, thickness)
    cv2.line(img, (x1, y1 + r), (x1, y1 + r + d), color, thickness)
    cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)
    # Top right
    cv2.line(img, (x2 - r, y1), (x2 - r - d, y1), color, thickness)
    cv2.line(img, (x2, y1 + r), (x2, y1 + r + d), color, thickness)
    cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)
    # Bottom left
    cv2.line(img, (x1 + r, y2), (x1 + r + d, y2), color, thickness)
    cv2.line(img, (x1, y2 - r), (x1, y2 - r - d), color, thickness)
    cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)
    # Bottom right
    cv2.line(img, (x2 - r, y2), (x2 - r - d, y2), color, thickness)
    cv2.line(img, (x2, y2 - r), (x2, y2 - r - d), color, thickness)
    cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)

    cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, -1, cv2.LINE_AA)
    cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r - d), color, -1, cv2.LINE_AA)
    
    cv2.circle(img, (x1 +r, y1+r), 2, color, 12)
    cv2.circle(img, (x2 -r, y1+r), 2, color, 12)
    cv2.circle(img, (x1 +r, y2-r), 2, color, 12)
    cv2.circle(img, (x2 -r, y2-r), 2, color, 12)
    
    return img

def UI_box(x, img, color=None, label=None, line_thickness=None, object_id=None, entry_time=None):
    # Plots one bounding box on image img
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]

        img = draw_border(img, (c1[0], c1[1] - t_size[1] - 3), (c1[0] + t_size[0], c1[1] + 3), color, 1, 8, 2)

        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)

        if entry_time is not None:
            current_time = time.time()
            elapsed_time = current_time - entry_time[object_id]  # Use the object_id to retrieve entry_time

            # Convert entry_time to a human-readable format
            entry_datetime = datetime.fromtimestamp(entry_time[object_id])
           # entry_time_str = entry_datetime.strftime('%Y-%m-%d %H:%M:%S')

            time_label = f"ID: {object_id} - Elapsed Time: {round(elapsed_time, 2)}s"
            t_size_time = cv2.getTextSize(time_label, 0, fontScale=tl / 3, thickness=tf)[0]
            img = draw_border(img, (c1[0], c1[1] + 3), (c1[0] + t_size_time[0], c1[1] + 3 + t_size_time[1] + 3),
                              color, 1, 8, 2)
            cv2.putText(img, time_label, (c1[0], c1[1] + t_size_time[1] + 3), 0, tl / 3, [225, 255, 255],
                        thickness=tf, lineType=cv2.LINE_AA)
            
            # print(time_label)
            return elapsed_time

def count_persons_in_region(bbox, region):
    count = 0
    for box in bbox:
        if is_in_region(box, region):
            count += 1
    return count

def draw_boxes(img, bbox, names,object_id, identities=None, offset=(0, 0)):

    height, width, _ = img.shape

    for i, box in enumerate(bbox):
        x1, y1, x2, y2 = [int(i) for i in box]
        x1 += offset[0]
        x2 += offset[0]
        y1 += offset[1]
        y2 += offset[1]
    
        # code to find center of bottom edge
        center = (int((x2+x1)/ 2), int((y2+y2)/2))

        # get ID of object
        id = int(identities[i]) if identities is not None else 0

        # create new buffer for new object
        color = compute_color_for_labels(object_id[i])
        obj_name = names[object_id[i]]
        label = '{}{:d}'.format("", id) + ":"+ '%s' % (obj_name)

        # add center to buffer
        UI_box(box, img, label=label, color=color, line_thickness=2)
    
    return img

def is_in_region(box, region):
    x1, y1, x2, y2 = box
    return region[0] <= x1 <= region[2] and region[1] <= y1 <= region[3]

def draw_boxes_in_region(img, bbox, names, object_id, identities=None, offset=(0, 0), region=None, zone_thickness=None):
    waiting_times = {}
    total_detected_objects = 0
    max_waiting_time = 0
    height, width, _ = img.shape
    det = [
        box for box in bbox if (
            region and (
                region[0] <= box[0] <= region[2] and
                region[1] <= box[1] <= region[3] or
                region[0] <= box[2] <= region[2] and
                region[1] <= box[3] <= region[3] or
                region[0] <= (box[0] + box[2]) / 2 <= region[2] and
                region[1] <= (box[1] + box[3]) / 2 <= region[3]
            )
        )
    ]
    # count_in_region = count_persons_in_region(det, region)  # Count persons in the region
    # ##print("Number of persons in zone:", count_in_region)
    for i, box in enumerate(det):
        x1, y1, x2, y2 = [int(i) for i in box]

        # Draw the zone around the bounding box
        if zone_thickness:
            zone_c1 = (max(x1 - zone_thickness, 0), max(y1 - zone_thickness, 0))
            zone_c2 = (min(x2 + zone_thickness, width - 1), min(y2 + zone_thickness, height - 1))

        # code to find center of the bottom edge
        center = (int((x2 + x1) / 2), int((y2 + y2) / 2))

        # get ID of the object
        id = int(identities[i]) if identities is not None else 0

        # create a new buffer for the new object
        color = compute_color_for_labels(object_id[i])
        obj_name = names[object_id[i]]
        label = '{}{:d}'.format("", id) + ":" + '%s' % (obj_name)
        max1 = 0
        # When an object enters the region, update the entry time
        if id not in entry_time:
            entry_time[id] = time.time()
        total_detected_objects += 1 
        # Calculate elapsed time for each person
        current_time = time.time()
        elapsed_time = current_time - entry_time[id]  # Use the object_id to retrieve entry_time
        if elapsed_time > 0:
            waiting_times[id] = round(elapsed_time, 2)
        max_waiting_time_new = UI_box(box, img, label=label, color=color, line_thickness=2, object_id=id, entry_time=entry_time)
        if (max_waiting_time < max_waiting_time_new):
            max_waiting_time = max_waiting_time_new
            #send max_waiting_time
    return img,round(max_waiting_time, 2),waiting_times,total_detected_objects

class DetectionPredictor(BasePredictor):
    def __init__(self, cfg,region=None):
            super(DetectionPredictor, self).__init__(cfg)
            self.nbrperson = 0
            self.region = region
            self.last_notification_time = time.time()
            self.websocket = websocketConnect(cfg.url)# 'ws://10.24.82.13:3000'
            self.location = cfg.location
            self.camera = cfg.camera
            self.camera_name = cfg.camera_name
            self.camera_type = cfg.camera_type
            self.model_type = cfg.model_type
            self.dict = {}
            self.max_w = 0

    def get_annotator(self, img):
        return Annotator(img, line_width=self.args.line_thickness, example=str(self.model.names))
    # def job():
    #     print("I'm working...")
    def preprocess(self, img):
        img = torch.from_numpy(img).to(self.model.device)
        img = img.half() if self.model.fp16 else img.float()  # uint8 to fp16/32
        img /= 255  # 0 - 255 to 0.0 - 1.0
        return img

    def postprocess(self, preds, img, orig_img):
        preds = ops.non_max_suppression(preds,
                                        self.args.conf,
                                        self.args.iou,
                                        agnostic=self.args.agnostic_nms,
                                        max_det=self.args.max_det)

        for i, pred in enumerate(preds):
            shape = orig_img[i].shape if self.webcam else orig_img.shape
            pred[:, :4] = ops.scale_boxes(img.shape[2:], pred[:, :4], shape).round()

        return preds

    def write_results(self, idx, preds, batch):
        max_waiting_time = 0
        p, im, im0 = batch
        all_outputs = []
        log_string = ""
        if len(im.shape) == 3:
            im = im[None]  # expand for batch dim
        self.seen += 1
        im0 = im0.copy()
        if self.webcam:  # batch_size >= 1
            # log_string += f'{idx}: '
            frame = self.dataset.count
        else:
            frame = getattr(self.dataset, 'frame', 0)

        self.data_path = p
        save_path = str(self.save_dir / p.name)  # im.jpg
        self.txt_path = str(self.save_dir / 'labels' / p.stem) + ('' if self.dataset.mode == 'image' else f'_{frame}')
        self.annotator = self.get_annotator(im0)
        region_of_interest = self.region
        cv2.rectangle(im0, (region_of_interest[0], region_of_interest[1]),
                    (region_of_interest[2], region_of_interest[3]), (0, 255, 255), 2)
        det_filtered = preds[idx]

        # Filter detections within the specified region
        det = [
            det_item for det_item in det_filtered if (
                region_of_interest[0] <= det_item[0] <= region_of_interest[2] and
                region_of_interest[1] <= det_item[1] <= region_of_interest[3] or
                region_of_interest[0] <= det_item[2] <= region_of_interest[2] and
                region_of_interest[1] <= det_item[3] <= region_of_interest[3] or
                region_of_interest[0] <= (det_item[0] + det_item[2]) / 2 <= region_of_interest[2] and
                region_of_interest[1] <= (det_item[1] + det_item[3]) / 2 <= region_of_interest[3]
            )
        ]

        waiting_times1 = {}
        total_detected_objects = 0
        all_outputs.append(det)
        if len(det) == 0:
            if not self.dict or self.nbrperson != total_detected_objects or max_waiting_time != self.max_w:
                self.nbrperson = total_detected_objects
                self.max_w = max_waiting_time
                self.dict = {"location": self.location, "max_waiting_time": self.max_w, "occupation": self.nbrperson, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), 
                                    "camera": self.camera, "camera_name": self.camera_name, "detection": json.dumps(waiting_times1),"camera_type":self.camera_type,"model": "ZONE", "model_type": self.model_type}
                self.websocket.send(json.dumps({
                    "event": "realtime_zone",
                    "data": self.dict
                }))
                print(self.dict)
            return log_string

        # Extract class information from each detection
        classes = [det_item[5] for det_item in det]

        for c in set(classes):  # Use set to get unique classes
            log_string += '%gx%g ' % im.shape[2:]  # print string

            n = sum(1 for det_item in det if det_item[5] == c)  # detections per class
            log_string += f"{n} {self.model.names[int(c)]}{'s' * (n > 1)}, "
            #print(f"{n} {self.model.names[int(c)]}{'s' * (n > 1)}, ")

        # write
        gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
        xywh_bboxs = []
        confs = []
        oids = []
        outputs = []
        
        for *xyxy, conf, cls in reversed(det):
            x_c, y_c, bbox_w, bbox_h = xyxy_to_xywh(*xyxy)
            xywh_obj = [x_c, y_c, bbox_w, bbox_h]
            xywh_bboxs.append(xywh_obj)
            confs.append([conf.item()])
            oids.append(int(cls))
        
        xywhs = torch.Tensor(xywh_bboxs)
        confss = torch.Tensor(confs)
        
        outputs = deepsort.update(xywhs, confss, oids, im0)
     
        if len(outputs) > 0:
            bbox_xyxy = outputs[:, :4]
            identities = outputs[:, -2]
            object_id = outputs[:, -1]
            #draw_boxes(im0, bbox_xyxy, self.model.names,object_id, identities=None, offset=(0, 0))
            im,max_waiting_time,waiting_times1, total_detected_objects= draw_boxes_in_region(im0, bbox_xyxy, self.model.names, object_id, identities, region=region_of_interest, zone_thickness=5)
            # if waiting_times1:
            #     print(waiting_times1)
            #     waiting_times1.clear()
        if self.nbrperson != total_detected_objects or max_waiting_time != self.max_w:
            self.nbrperson = total_detected_objects
            self.max_w = max_waiting_time
            if self.dict:
                self.dict["occupation"] = self.nbrperson
                self.dict["max_waiting_time"] = self.max_w
                self.dict["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                if waiting_times1:
                    self.dict["detection"] = json.dumps(waiting_times1)
                self.websocket.send(json.dumps({
                    "event": "realtime_zone",
                    "data": self.dict
                }))

            else:
                self.dict = {"location": self.location, "max_waiting_time": self.max_w, "occupation": self.nbrperson, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), 
                                    "camera": self.camera, "camera_name": self.camera_name, "detection": json.dumps(waiting_times1),"camera_type":self.camera_type,"model": "ZONE", "model_type": self.model_type}
            print(self.dict)
            if waiting_times1:
                waiting_times1.clear()
            
            self.websocket.send(json.dumps({
                "event": "realtime_zone",
                "data": self.dict
            }))
        cv2.putText(im0, f"Total persons: {self.nbrperson}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0), 2)
        #current_time = time.time()
        #elapsed_time = current_time - self.last_notification_time
        
        # Check if an hour has passed since the last notification
        # if elapsed_time >= 3600:  # 3600 seconds = 1 hour
        #     if len(waiting_times) != 0:
        #         print("Dictionary is not empty:", waiting_times)
        #current_time = datetime.datetime.now()
        #schedule.every().hour.do(self.job)
        #print(current_time)
        # Check if it's the start of a new hour
        #if current_time.minute == 0:
        # if current_time.tm_min == 0 and current_time.tm_sec == 0:
                #print("Dictionary is not empty:", waiting_times)
                #waiting_times.clear()
            #self.last_notification_time = current_time
        return log_string



@hydra.main(version_base=None, config_path=str(DEFAULT_CONFIG.parent), config_name=DEFAULT_CONFIG.name)
def predict(cfg):
    region = (cfg.region[0],cfg.region[1], cfg.region[2], cfg.region[3])
    init_tracker()
    cfg.model = cfg.model or "yolov8n.pt"
    cfg.imgsz = check_imgsz(cfg.imgsz, min_dim=2)  # check image size
    cfg.source = cfg.source if cfg.source is not None else ROOT / "assets"
    predictor = DetectionPredictor(cfg,region)
    predictor()


if __name__ == "__main__":
    predict()