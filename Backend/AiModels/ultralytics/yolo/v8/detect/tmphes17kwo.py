
import cv2
from PIL import Image
import sys
import os

sys.path.extend([
    '/app/Backend/AiModels/ultralytics/yolo/v8/detect',
    os.path.dirname('/app/Backend/AiModels/ultralytics/yolo/v8/detect'),
    os.path.dirname(os.path.dirname('/app/Backend/AiModels/ultralytics/yolo/v8/detect'))
])

cv2.waitKey = lambda x: None
cv2.imshow = lambda *args, **kwargs: None
cv2.destroyAllWindows = lambda: None
cv2.namedWindow = lambda *args, **kwargs: None
Image.show = lambda *args, **kwargs: None

try:
    import deep_sort_pytorch
except ImportError as e:
    print(f"Error importing deep_sort_pytorch: {e}")
    print(f"Current sys.path: {sys.path}")
    raise

exec(open('predict.py').read())
