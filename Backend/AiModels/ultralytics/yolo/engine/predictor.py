# Ultralytics YOLO 🚀, GPL-3.0 license
"""
Run prediction on images, videos, directories, globs, YouTube, webcam, streams, etc.
Usage - sources:
    $ yolo task=... mode=predict  model=s.pt --source 0                         # webcam
                                                img.jpg                         # image
                                                vid.mp4                         # video
                                                screen                          # screenshot
                                                path/                           # directory
                                                list.txt                        # list of images
                                                list.streams                    # list of streams
                                                'path/*.jpg'                    # glob
                                                'https://youtu.be/Zgi9g1ksQHc'  # YouTube
                                                'rtsp://example.com/media.mp4'  # RTSP, RTMP, HTTP stream
Usage - formats:
    $ yolo task=... mode=predict --weights yolov8n.pt          # PyTorch
                                    yolov8n.torchscript        # TorchScript
                                    yolov8n.onnx               # ONNX Runtime or OpenCV DNN with --dnn
                                    yolov8n_openvino_model     # OpenVINO
                                    yolov8n.engine             # TensorRT
                                    yolov8n.mlmodel            # CoreML (macOS-only)
                                    yolov8n_saved_model        # TensorFlow SavedModel
                                    yolov8n.pb                 # TensorFlow GraphDef
                                    yolov8n.tflite             # TensorFlow Lite
                                    yolov8n_edgetpu.tflite     # TensorFlow Edge TPU
                                    yolov8n_paddle_model       # PaddlePaddle
    """
import platform
from collections import defaultdict
from pathlib import Path
import os
import torch

import cv2
import numpy as np

from ultralytics.nn.autobackend import AutoBackend
from ultralytics.yolo.configs import get_config
from ultralytics.yolo.data.dataloaders.stream_loaders import LoadImages, LoadScreenshots, LoadStreams
from ultralytics.yolo.data.utils import IMG_FORMATS, VID_FORMATS
from ultralytics.yolo.utils import DEFAULT_CONFIG, LOGGER, SETTINGS, callbacks, colorstr, ops
from ultralytics.yolo.utils.checks import check_file, check_imgsz, check_imshow
from ultralytics.yolo.utils.files import increment_path
from ultralytics.yolo.utils.torch_utils import select_device, smart_inference_mode
from ultralytics.yolo.utils.plotting import Annotator, colors, save_one_box


class BasePredictor:
    """
    BasePredictor

    A base class for creating predictors.

    Attributes:
        args (SimpleNamespace): Configuration for the predictor.
        save_dir (Path): Path to the directory where the results will be saved.
        done_setup (bool): Whether the predictor has finished setting up the model.
        model (nn.Module): Model used for prediction.
        data (dict): Data configuration.
        device (torch.device): Device used for prediction.
        dataset (Dataset): Dataset used for prediction.
        vid_path (str): Path to the video file.
        vid_writer (cv2.VideoWriter): Video writer for saving video prediction results.
        annotator (Annotator): Annotator used for prediction.
        data_path (str): Path to the data.
    """

    def __init__(self, overrides=None):
        """
        Initializes the BasePredictor class.

        Args:
            overrides (dict, optional): Configuration to override the default config file.
        """
        self.args = get_config(config=DEFAULT_CONFIG, overrides=overrides)
        project = self.args.project or Path(SETTINGS['runs_dir']) / self.args.task
        name = self.args.name or f"{self.args.mode}"
        self.save_dir = increment_path(Path(project) / name, exist_ok=self.args.exist_ok)
        if self.args.conf is None:
            self.args.conf = 0.25  # default conf=0.25
        self.done_warmup = False
        if self.args.show:
            check_requirements(('opencv-python>=4.1.1',))
            self.show = True
            self.window_name = self.args.name or 'ultralytics'
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, self.args.imgsz, self.args.imgsz)
        else:
            self.show = False

        # Usable if setup is done
        self.model = None
        self.data = self.args.data  # data_dict
        self.imgsz = None
        self.device = None
        self.dataset = None
        self.vid_path, self.vid_writer = None, None
        self.plotted_img = None
        self.data_path = None
        self.source_type = None
        self.batch = None
        self.results = None
        self.transforms = None
        self.callbacks = _callbacks or callbacks.get_default_callbacks()
        callbacks.add_integration_callbacks(self)

    def get_local_cuda_index(global_gpu_id):
        """Given a global GPU ID, return the local index in CUDA_VISIBLE_DEVICES."""
        cuda_devices = os.environ.get('CUDA_VISIBLE_DEVICES', '0')
        device_list = [int(x) for x in cuda_devices.split(',')]
        return device_list.index(global_gpu_id)

    def preprocess(self, img):
        """
        Prepares image for inference by conducting pre transforms and adding a batch dimension.

        Args:
            img (Numpy.ndarray): Image to be preprocessed.

        Returns:
            (torch.Tensor): Preprocessed image.
        """
        not_tensor = not isinstance(img, torch.Tensor)
        if not_tensor:
            img = np.stack(self.pre_transform(img))
            img = img[..., ::-1].transpose((0, 3, 1, 2))  # HWC to CHW, BGR to RGB
            img = np.ascontiguousarray(img)
            img = torch.from_numpy(img)

        img = img.to(self.device)
        img = img.half() if self.model.fp16 else img.float()  # uint8 to fp16/32
        if not_tensor:
            img /= 255  # 0 - 255 to 0.0 - 1.0
        return img

    def get_model(self):
        """Returns a model."""
        model = self.model or self.args.model
        self.model = model
        self.device = model.device if hasattr(model, 'device') else next(model.parameters()).device
        return model

    def setup_source(self, source):
        """
        Sets up source and inference mode.

        Args:
            source (int | str | ndarray): Source to setup.
        """
        self.imgsz = check_imgsz(self.args.imgsz, stride=self.model.stride, min_dim=2)  # check image size
        self.transforms = getattr(self.model.model, 'transforms', classify_transforms(
            self.imgsz[0])) if self.args.task == 'classify' else None
        self.dataset = load_inference_source(source=source,
                                          imgsz=self.imgsz,
                                          vid_stride=self.args.vid_stride,
                                          stream_buffer=self.args.stream_buffer,
                                          stride=self.model.stride,
                                          auto=self.model.pt,
                                          transforms=self.transforms)
        self.source_type = self.dataset.source_type
        if not getattr(self, 'stream', True) and (self.dataset.mode == 'stream' or  # streams
                                                  len(self.dataset) > 1 or  # images
                                                  any(Path(x).is_video for x in self.dataset.source)):  # videos
            LOGGER.warning(STREAM_WARNING)
        self.vid_path, self.vid_writer = [None] * self.dataset.bs, [None] * self.dataset.bs

    @smart_inference_mode()
    def stream_inference(self, source=None, model=None):
        """Streams real-time inference on camera feed and saves results to file."""
        if self.args.verbose:
            LOGGER.info('')

        # Setup model
        if not self.model:
            self.setup_model(model)
        # Setup source every time predict is called
        self.setup_source(source if source is not None else self.args.source)

        # Check if save_dir/ label file exists
        if self.args.save or self.args.save_txt:
            (self.save_dir / 'labels' if self.args.save_txt else self.save_dir).mkdir(parents=True, exist_ok=True)
        # Warmup model
        if not self.done_warmup:
            self.model.warmup(imgsz=(1 if self.model.pt or self.model.triton else self.dataset.bs, 3, *self.imgsz))
            self.done_warmup = True

        self.seen, self.windows, self.batch, profilers = 0, [], None, (ops.Profile(), ops.Profile(), ops.Profile())
        self.run_callbacks('on_predict_start')
        for batch in self.dataset:
            self.run_callbacks('on_predict_batch_start')
            self.batch = batch
            path, im0s, vid_cap, s = batch

            # Preprocess
            with profilers[0]:
                im = self.preprocess(im0s)

            # Inference
            with profilers[1]:
                preds = self.inference(im, im0s)

            # Postprocess
            with profilers[2]:
                if isinstance(self.model, SegmentationModel):
                    self.results = self.postprocess(preds, im, im0s, self.model)
                else:
                    self.results = self.postprocess(preds, im, im0s)

            self.run_callbacks('on_predict_postprocess_end')

            # Visualize, save, write results
            n = len(im0s)
            for i in range(n):
                self.seen += 1
                self.results[i].speed = {
                    'preprocess': profilers[0].dt * 1E3 / n,
                    'inference': profilers[1].dt * 1E3 / n,
                    'postprocess': profilers[2].dt * 1E3 / n}
                p, im0 = path[i], None if self.source_type.tensor else im0s[i].copy()
                p = Path(p)

                if self.args.verbose or self.args.save or self.args.save_txt or self.args.show:
                    s += self.write_results(i, self.results, (p, im, im0))
                if self.args.save or self.args.save_txt:
                    self.results[i].save_dir = self.save_dir.__str__()
                if self.args.show and self.plotted_img is not None:
                    self.show(p)
                if self.args.save and self.plotted_img is not None:
                    self.save_preds(vid_cap, i, str(self.save_dir / p.name))

            self.run_callbacks('on_predict_batch_end')
            yield from self.results

            # Print time (inference-only)
            if self.args.verbose:
                LOGGER.info(f'{s}Done. ({t3 - t1:.3f}s)')

        # Release assets
        if isinstance(self.vid_writer[-1], cv2.VideoWriter):
            self.vid_writer[-1].release()  # release final video writer

        # Print results
        if self.args.verbose and self.seen:
            t = tuple(x.t / self.seen * 1E3 for x in profilers)  # speeds per image
            LOGGER.info(f'Speed: %.1fms preprocess, %.1fms inference, %.1fms postprocess per image at shape '
                       f'{(1, 3, *im.shape[2:])}' % t)
        if self.args.save or self.args.save_txt or self.args.save_crop:
            nl = len(list(self.save_dir.glob('labels/*.txt')))  # number of labels
            s = f"\n{nl} label{'s' * (nl > 1)} saved to {self.save_dir / 'labels'}" if self.args.save_txt else ''
            LOGGER.info(f"Results saved to {colorstr('bold', self.save_dir)}{s}")

        self.run_callbacks('on_predict_end')

    def setup_model(self, model, verbose=True):
        """Initialize YOLO model with given parameters and set it to evaluation mode."""
        device = select_device(self.args.device, verbose=verbose)
        if model is None:
            model = self.args.model

        # Set device for the model
        if torch.cuda.is_available():
            model = model.to(f'cuda:{get_local_cuda_index(self.gpu_device)}')
        else:
            model = model.to(device)

        model.eval()
        self.model = model
        self.device = model.device
        self.args.half = self.device.type != 'cpu'  # force FP16 val during training

        return model

    def show(self, p):
        """Display an image in a window using OpenCV imshow()."""
        im0 = self.plotted_img
        if platform.system() == 'Linux' and p not in self.windows:
            self.windows.append(p)
            cv2.namedWindow(str(p), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # allow window resize (Linux)
            cv2.resizeWindow(str(p), im0.shape[1], im0.shape[0])
        cv2.imshow(str(p), im0)
        cv2.waitKey(500 if self.batch[3].startswith('image') else 1)  # 1 millisecond

    def save_preds(self, vid_cap, idx, save_path):
        """Save video predictions as mp4 at specified path."""
        im0 = self.plotted_img
        # Save imgs
        if self.dataset.mode == 'image':
            cv2.imwrite(save_path, im0)
        else:  # 'video' or 'stream'
            if self.vid_path[idx] != save_path:  # new video
                self.vid_path[idx] = save_path
                if isinstance(self.vid_writer[idx], cv2.VideoWriter):
                    self.vid_writer[idx].release()  # release previous video writer
                if vid_cap:  # video
                    fps = int(vid_cap.get(cv2.CAP_PROP_FPS))  # integer required, floats produce errors in MP4 codec
                    w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                else:  # stream
                    fps, w, h = 30, im0.shape[1], im0.shape[0]
                suffix = '.mp4' if MACOS else '.avi' if WINDOWS else '.avi'
                fourcc = 'avc1' if MACOS else 'WMV2' if WINDOWS else 'MJPG'  # codecs
                save_path = str(Path(save_path).with_suffix(suffix))
                self.vid_writer[idx] = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*fourcc), fps, (w, h))
            self.vid_writer[idx].write(im0)

    def run_callbacks(self, event: str):
        """Runs all registered callbacks for a specific event."""
        for callback in self.callbacks.get(event, []):
            callback(self)

    def add_callback(self, event: str, func):
        """
        Add callback
        """
        self.callbacks[event].append(func)
