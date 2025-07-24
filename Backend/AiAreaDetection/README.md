<H1 align="center">
People detection by zone </H1>

## Steps to run Code

1. Clone the repository
2. Navigate to the cloned folder
```
cd people-detect-zone
```
3. Create a virtual environment
```
python3 -m venv env

```
4. Activate the virtual environment
```
source env/bin/activate 

```
5. Install the dependencies.
```
pip install ultralytics==8.0.10
pip install -r requirements.txt
pip install easydict
```
6. Add the following line to the specified file:
```
/env/lib/python3.10/site-packages/ultralytics/yolo/configs/default.yaml
```
Add: region: null
url: null
location: ""
camera: 0
camera_name : ""


7. Setting the Directory.
```
cd ultralytics/yolo/v8/detect
```
9. Run prediction
```
python predict.py model=yolov8l.pt source="test3.mp4" show=True region=\[1000,0,2000,1400\]
taskset --cpu-list 0 python3 predict.py model=/home/bluedove/Desktop/Sara/people/people-counting/Person-models-master/PersonModelOldYoloN/best.pt source="/home/bluedove/Desktop/Sara/SaveVideo/savecafetemine.avi" region=\[1000,0,2000,1400\] show=True
```

- Run prediction with cpu limit (--cpu-list 'number' cpu id)
``` 
taskset --cpu-list 5 python3 predict.py model=/home/ismailkharrobi1/test/Person-models-master/PersonModelOldYoloN/best.pt source="v.mp4" region=\[1000,0,2000,1400\]
```
taskset --cpu-list 5 python3 predict.py model=/home/bluedove/Desktop/Sara/people/people-detect-zone/Person-models-master/training-2000/weights/best.pt source="/home/bluedove/Desktop/Sara/SaveVideo/savecafetemine.avi" region=\[500,1000,2000,1400\] show=True save=False conf=0.5 url="ws://10.24.81.32:3000/" location="CAFET_EMINES" camera=0 camera_name="queue"
