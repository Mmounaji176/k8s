import subprocess
from Backend.celery_prefork import app as prefork_queue
import os
from Api.models import ImageProc
@prefork_queue.task()
def run_prediction_task(model : str, source : str, conf : float, cords : str, location : str, camera : int, camera_name : str, url : str, cords_type : str, title : str, camera_type : str, model_type: str):
    env = os.environ.copy()
    print(f"model is {model} source is {source} conf is {conf} cords is {cords} location is {location} camera is {camera} camera_name is {camera_name} url is {url} camera type is {camera_type} model_type {model_type}")
    env['DJANGO_SETTINGS_MODULE'] = 'Backend.settings'
    
    env['CUDA_HOME'] = '/usr/local/cuda'
    env['LD_LIBRARY_PATH'] = f"{env['CUDA_HOME']}/lib64:{env['LD_LIBRARY_PATH']}"
    env['PYTHONPATH'] = '/app/Backend/AiModels/ultralytics/yolo/v8/detect' 
    working_directory = None
    cords_normalize = None
    if cords_type == "line":
        working_directory = '/app/Backend/AiModels/ultralytics/yolo/v8/detect'
        cords_normalize = f'line={cords}'
    elif cords_type == "region":
        working_directory = '/app/Backend/AiAreaDetection/ultralytics/yolo/v8/detect'
        cords_normalize = f'region={cords}'
    print(f'cords normalize is {cords_normalize}')
    command = [
        'python', 'monitor.py',
        f'model="{model}"',
        f'source="{source}"',
        f'conf={conf}', 
        cords_normalize,
        f'location="{location}"', 
        f'camera={camera}', 
        f'camera_name="{camera_name}"',
        f"camera_type='{camera_type}'",
        f'url={url}', 
        f'model_type="{model_type}"',
        
    ]

    try:
        process = subprocess.Popen(
            command,
            env=env,
            cwd=working_directory,
            preexec_fn=os.setsid
        )
        pid = process.pid
        print("pid is ",pid)
        instance = ImageProc.objects.filter(title=title).update(taskId=pid)
        

    except Exception as e:
        print("e ",e)




    
  