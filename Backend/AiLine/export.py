from ultralytics import YOLO

# Load a model
model = YOLO("./ppl.pt", gpu_id=gpu_id)  # load a pretr
model.export(format="engine")  