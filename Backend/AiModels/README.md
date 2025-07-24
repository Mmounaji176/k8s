<H1 align="center">
People counting </H1>

## Steps to run Code

- Clone the repository
- Goto the cloned folder.
```
cd people-counting
```
- Create env with python3.8
```
python3 -m venv env

```
- Activate env
```
source env/bin/activate 

```
- Install the dependecies
```
pip install ultralytics==8.0.10
pip install -r requirements.txt
pip install easydict
pip install websockets
```
- Add 
line: null
location: ""
camera: 0
camera_name: ""
url: ""
to the specified file:
```
/env/lib/python3.8/site-packages/ultralytics/yolo/configs/default.yaml
```

- Setting the Directory.
```
cd ultralytics/yolo/v8/detect
```
- Run prediction
```
python predict.py model=yolov8l.pt source="test3.mp4" show=True  conf=0.5 line='[0, 490, 2686, 490]'
```

- Run prediction with cpu limit (--cpu-list 'number' cpu id)
``` 
taskset --cpu-list 5 python3 predict.py model=/home/ismailkharrobi1/test/Person-models-master/PersonModelOldYoloN/best.pt source="v.mp4"  conf=0.5 line='[0, 490, 2686, 490]
```
```
python3 predict.py model=/home/bluedove/Desktop/Sara/people/people-counting/Person-models-master/PersonModelOldYoloN/best.pt source="/home/bluedove/Desktop/Sara/people/people-counting/saverestauum6p.avi"  conf=0.5 line='[0, 490, 2686, 490]' location="CAMPUS_RESTAURANT" camera=0 camera_name="main_door"
taskset --cpu-list 0 python3 predict.py model=/home/bluedove/Desktop/Sara/people/people-counting/Person-models-master/PersonModelOldYoloN/best.pt source="/home/bluedove/Desktop/Sara/SaveVideo/saverestaucampusentry.avi"  conf=0.5 line='[0, 490, 2686, 490]' location="CAMPUS_RESTAURANT" camera=1 camera_name="entry_door" url='ws://34.173.77.60:3005/' show=True save=False
```
# Customizing Stream Display

To customize the behavior of stream display in the `predictor.py` file, follow these steps:

1. Navigate to the `predictor.py` file located in the `people-counting/env/lib/python3.10/site-packages/ultralytics/yolo/engine/` directory.
2. Locate the `show` method within the `BasePredictor` class.
3. Update code for the `show` method:

    ```python
    def show(self, p):
    if not self.webcam and not self.from_img:
        im0 = self.annotator.result()
        if platform.system() == 'Linux' and p not in self.windows:
            self.windows.append(p)
            cv2.namedWindow(str(p), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # allow window resize (Linux)
            cv2.resizeWindow(str(p), im0.shape[1], im0.shape[0])
        cv2.imshow(str(p), im0)
        cv2.waitKey(1)  # 1 millisecond
    ```

4. Save the changes to the `predictor.py`

####line parking in street
taskset --cpu-list 5 python3 predict.py model=/home/bluedove/Desktop/Sara/car/New-Model-Car/best_1000.pt source="/home/bluedove/Desktop/Sara/people/people-counting/parking.mp4"  conf=0.5 line='[1150, 438, 1425, 545]' location="Parking" camera=1 camera_name="entry_door" url='ws://34.173.77.60:3005/' show=True save=False

[x1, y1, x2, y2]
##line parking in entry
taskset --cpu-list 4 python3 predict.py model=/home/bluedove/Desktop/Sara/car/New-Model-Car/best_1000.pt source="/home/bluedove/Desktop/Sara/people/people-counting/parking.mp4"  conf=0.5 line='[338, 634, 1576, 243]' location="Parking" camera=1 camera_name="entry_door" url='ws://34.173.77.60:3005/' show=True save=False

##line people 
taskset --cpu-list 3  python3 predict.py model=/home/bluedove/Desktop/Sara/people/people-counting/Person-models-master/PersonModelOldYoloN/best.pt source="/home/bluedove/Desktop/Sara/people/people-counting/pergola.avi"  conf=0.5 line='[495, 1277, 1627, 1039]' location="pergola" camera=1 camera_name="entry_door" url='ws://34.173.77.60:3005/' show=True save=False

taskset --cpu-list 3  python3 predict.py model=/home/bluedove/Desktop/Sara/people/people-counting/Person-models-master/PersonModelOldYoloN/best.pt source="/home/bluedove/Desktop/Sara/people/people-counting/pergola.avi"  conf=0.5 line='[495, 1277, 1627, 1039]' location="pergola" camera=0 camera_name="visitors" url='ws://10.24.82.13:3000/' show=True save=False

taskset --cpu-list 3  python3 predict.py model=/home/bluedove/Desktop/Sara/people/people-counting/Person-models-master/PersonModelOldYoloN/best.pt source="/home/bluedove/Desktop/Sara/people/people-counting/pergola.avi"  conf=0.5 line='[495, 1277, 1627, 1039]' location="pergola" camera=0 camera_name="passengers" url='ws://10.24.82.13:3000/' show=True save=False
