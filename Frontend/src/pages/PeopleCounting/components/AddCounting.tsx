
import { useState, useEffect } from "react";
import { Button } from "@nextui-org/button";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  Input,
  ModalFooter,
  useDisclosure,
  Progress
} from "@nextui-org/react";
import { RadioGroup, Radio } from "@nextui-org/react";
import { toast } from 'react-hot-toast';
import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import { useStreamStore } from "../../../store/stream";
import useAxios from "../../../services/axios";
import { create } from "zustand";
import { BiPlus } from "react-icons/bi";
import DrawBoard, { useArrowsStore, useRectanglesStore } from "./DrawBoard";
// import { toast } from 'react-hot-toast'
import { useGpuStore } from "../../../store/gpus";
import { useWebSocketStore } from "../store/useSocket";

const StreamProgress = ({ message }) => {
  const [progress, setProgress] = useState(0);

  const statusMap = {
    "Ai process is starting": 40,
    "Starting streaming process": 60,
    "integrating stream (60s approx)": 90,
    "Stream is ready": 100
  };

  useEffect(() => {
    if (message in statusMap) {
      setProgress(statusMap[message]);
    }
  }, [message]);

  return (
    <div className="w-full flex flex-col gap-4">
      <Progress
        size="md"
        radius="sm"
        classNames={{
          base: "max-w-md",
          track: "drop-shadow-md border border-default",
          indicator: "bg-gradient-to-r from-blue-500 to-blue-600",
          label: "tracking-wider font-medium text-default-600",
          value: "text-blue-600"
        }}
        value={progress}
        showValueLabel={true}
        label={message}
      />
    </div>
  );
};
type STORE = {
  place: string;
  url: string;
  title: string;
  id: string;
  model: string;
  cuda_device: number;
  pod_id: string;
  gpu_id: number;
  service: string;
};
type ACTION = {
  setPlace: (data: string) => void;
  setUrl: (data: string) => void;
  setTitle: (data: string) => void;
  setResponse: (data: any) => void;
  setId: (data: string) => void;
  setModel: (data: string) => void;
  setCudaDevice: (data: number) => void;
  setPodId: (data: string) => void;
  setGpuId: (data: number) => void;
  setService: (data: string) => void;
  response: any;
  handleSubmit: () => void;
};
const useAddStreamStore = create<STORE & ACTION>((set) => ({
  id: "",
  place: "",
  url: "",
  title: "",
  model: "",
  cuda_device: 0,
  response: null,
  pod_id: "",
  gpu_id: 0,
  service: "",

  setPlace(data) {
    set({ place: data });
  },
  setId(data) {
    set({ id: data });
  },
  setUrl(data) {
    set({ url: data });
  },
  setTitle(data) {
    set({ title: data });
  },
  setResponse(data) {
    set({ response: data });
  },
  setModel(data) {
    set({ model: data });
  },
  setCudaDevice(data) {
    set({ cuda_device: data });
  },
  setPodId(data) {
    set({ pod_id: data });
  },
  setGpuId(data) {
    set({ gpu_id: data });
  },
  setService(data) {
    set({ service: data });
  },
  handleSubmit() {
    console.log("Submit");
  },
}));

type GpuInfo = { pod: string; node: string; gpu_id: number; status: string; last_heartbeat: number; service: string };
const useDynamicGpuSelection = () => {
  const [gpus, setGpus] = useState<GpuInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const axios = useAxios();
  useEffect(() => {
    axios.get("/api/gpus/").then(res => {
      setGpus(res.data.gpus as GpuInfo[]);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);
  return { gpus, loading };
};

const StepOne = (places: any, indexplace: number, streamtype: string) => {
  const flag = false;
  const stream = useStreamStore();
  const streamStore = useAddStreamStore();
  const { gpus, loading } = useDynamicGpuSelection();
  const [selectedGpu, setSelectedGpu] = useState<GpuInfo | null>(null);

  const handleUrlChange = (e: any) => {
    streamStore.setUrl(e.target.value);
  };
  const handleCudaDeviceChange = (value: any) => {
    const gpu = gpus.find((g) => `${g.pod}_${g.gpu_id}` === value);
    setSelectedGpu(gpu);
    if (gpu) {
      streamStore.setCudaDevice(gpu.gpu_id);
      streamStore.setGpuId(gpu.gpu_id);
      streamStore.setPodId(gpu.pod);
      streamStore.setService(gpu.service);
      streamStore.setResponse({ ...streamStore.response, pod_id: gpu.pod });
    }
  };
  const handleTitleChange = (e: any) => {
    streamStore.setTitle(e.target.value);
  };

  const handleSetAuto = (value: string) => {
    streamStore.setPlace(value);
  };
  const handleModelChange = (value: string) => {
    streamStore.setModel(value);
    stream.setModel(value)
  };

  return (
    <>
      {flag == false && (
        <>
          <Autocomplete
            label="Place"
            placeholder="Search for a place"
            defaultItems={stream.places}
            labelPlacement="outside"
            className="w-full h-full"
            disableSelectorIconRotation
            onInputChange={handleSetAuto}
          >
            {(item) => (
              <AutocompleteItem className="h-full" key={item.name}>
                {item.name}
              </AutocompleteItem>
            )}
          </Autocomplete>
          <Autocomplete
            label="Model"
            placeholder="set model"
            defaultItems={stream.models}
            labelPlacement="outside"
            className="w-full h-full"
            disableSelectorIconRotation
            onInputChange={handleModelChange}
          >
            {(item) => (
              <AutocompleteItem className="h-full" key={item.name}>
                {item.name}
              </AutocompleteItem>
            )}
          </Autocomplete>
          <Input
            className="text-white"
            autoFocus
            label="Camera"
            placeholder="Enter camera name"
            variant="bordered"
            onChange={handleTitleChange}
          />
          <Input
            className="text-white"
            label="Url"
            placeholder="Enter stream url"
            type="text"
            variant="bordered"
            onChange={handleUrlChange}
          />
          <div className="flex flex-col gap-3">
            <RadioGroup
              label="Select GPU"
              value={selectedGpu ? `${selectedGpu.pod}_${selectedGpu.gpu_id}` : ""}
              onValueChange={handleCudaDeviceChange}
            >
              {loading ? (
                <Radio value="loading">Loading GPUs...</Radio>
              ) : gpus.length === 0 ? (
                <Radio value="none">No GPUs available</Radio>
              ) : (
                gpus.map((gpu) => (
                  <Radio key={`${gpu.pod}_${gpu.gpu_id}`} value={`${gpu.pod}_${gpu.gpu_id}`}
                    isDisabled={gpu.status !== "idle"}
                  >
                    {`GPU ${gpu.gpu_id} (${gpu.pod}, ${gpu.status})`}
                  </Radio>
                ))
              )}
            </RadioGroup>
            {selectedGpu && (
              <p className="text-default-500 text-small">
                Selected: GPU {selectedGpu.gpu_id} (Pod: {selectedGpu.pod})
              </p>
            )}
          </div>
        </>
      )}
    </>
  );
};

const StepTwo = ({ streamtype }: { streamtype: "line" | "zone" }) => {
  const stream = useStreamStore();
  const gateStreamType = streamtype;
  // console.log();
  // console.log();

  return (
    <DrawBoard
      imageUrl={`${import.meta.env.VITE_APP_BACKEND}${stream?.streams[0]?.thumbnail
        }`}
      type={gateStreamType}
    />
  );
};

export const AddStreamCountingButton = ({
  places,
  indexplace,
  text,
  streamtype,
  category_name,
  camera_type,
  model_type
}: any) => {
  const arrowStore = useArrowsStore();
  const rectangleStore = useRectanglesStore();
  const { onOpen, isOpen, onOpenChange, onClose } = useDisclosure();
  const [step, setStep] = useState(1);
  const [toggle, setToggle] = useState(false)
  const [message, setMessage] = useState("")
  const axios = useAxios();
  const streamStore = useAddStreamStore();
  const stream = useStreamStore();
  const gpuStore = useGpuStore();

  useEffect(() => {
    if (!gpuStore.gpuList || gpuStore.gpuList.length === 0) {
      axios.get("/api/gpus/").then(res => {
        if (res.data && Array.isArray(res.data.gpus)) {
          gpuStore.setGpuList(res.data.gpus);
          gpuStore.setGpu(res.data.gpus.length);
        }
      }).catch(err => {
        console.error("Failed to fetch GPU registry:", err);
      });
    }
  }, []);

  const handleSubmitStepOne = async () => {
    const gpuPrefix = `/gpu${streamStore.gpu_id}`;
    stream.places.forEach(
      async (element: { name: string | undefined; id: number }) => {
        if (element.name === streamStore.place) {
          const response = await axios.post(
            `${gpuPrefix}/peoplecounting/addStreamCounting/`,
            {
              title: `${streamStore.title}`,
              place: `${element.id}`,
              url: `${streamStore.url}`,
              camera_type: `${camera_type}`,
              place_name: `${streamStore.place}`,
              category_name: `${category_name}`,
              model_type: `${model_type}`,
              cuda_device: `${streamStore.cuda_device}`,
              pod_id: `${streamStore.pod_id}`,
              gpu_id: `${streamStore.gpu_id}`
            }
          );
          streamStore.setResponse(response.data);
          streamStore.setId(response.data.id);
          if (places[indexplace]?.id) {
            const res = await axios.get(
              `${gpuPrefix}/peoplecounting/streamCounting/${places[indexplace]?.id}`
            );
            stream.load(res.data);
          } else {
            stream.load([]);
          }
          const res1 = await axios.get(`${gpuPrefix}/api/zones/line`);
          stream.setPlaces(res1.data);
        }
      }
    );
  };

const handleSubmitStepTwo = async () => {
  // Calculate cords once, outside the loop
  const cord_types = arrowStore.arrows.length > 0 ? "line" : "region";
  const cords =
    cord_types === "line"
      ? `[${arrowStore.arrows
          .map((arrow) =>
            arrow.points.map((point) => Math.round(point)).join(",")
          )
          .join(",")}]`
      : `[${rectangleStore.rectangles
          .map(
            (rect) =>
              Math.round(rect.x) +
              "," +
              Math.round(rect.y) +
              "," +
              Math.round(rect.width + rect.x) +
              "," +
              Math.round(rect.height + rect.y)
          )
          .join(",")}]`;

  console.log("Cords type:", cord_types);
  console.log("Cords data:", cords);

  // Find the matching place (more efficient than forEach)
  const selectedPlace = stream.places.find(element => element.name === streamStore.place);
  
  if (!selectedPlace) {
    toast.error("Selected place not found");
    return;
  }

  try {
    console.log("streamStore.id", streamStore.response.id);
    console.log("streamStore.id", streamStore.id);
    
    // FIXED: Add the GPU prefix to the PATCH request
    const gpuPrefix = `/gpu${streamStore.gpu_id}`;
    console.log("Using GPU prefix:", gpuPrefix);
    
    const response = await axios.patch(
      `${gpuPrefix}/peoplecounting/addStreamCounting/`, // ✅ FIXED: Added GPU prefix
      {
        id: streamStore.id,
        title: streamStore.title,
        place: selectedPlace.id,
        url: streamStore.url,
        place_name: streamStore.place,
        cords: cords,
        camera_type: camera_type,
        cords_type: cord_types,
        model_type: stream.model,
        cuda_device: streamStore.cuda_device,
        pod_id: streamStore.pod_id,     // ADDED: Include pod_id
        gpu_id: streamStore.gpu_id      // ADDED: Include gpu_id
      }
    );

    console.log("PATCH response:", response.data);
    streamStore.setResponse(response.data);
    
    if (places[indexplace]?.id) {
      const res = await axios.get(
        `${gpuPrefix}/peoplecounting/streamCounting/${places[indexplace]?.id}` // ✅ Use GPU prefix here too
      );
      stream.load(res.data);
    } else {
      stream.load([]);
    }
    
    const res1 = await axios.get(`${gpuPrefix}/api/zones/line`); // ✅ Use GPU prefix here too
    stream.setPlaces(res1.data);
    arrowStore.resetArrows();
    rectangleStore.resetRectangles();
    
    toast.success("Stream configuration updated!");
    
  } catch (error) {
    console.error("Error updating stream:", error);
    console.error("Error details:", error.response?.data);
    toast.error("Failed to update stream configuration: " + (error.response?.data?.error || error.message));
  }
};

  const webSocketStore = useWebSocketStore();
  
  // Only connect to the WebSocket when the modal is opened and toggle is true
  useEffect(() => {
    if (isOpen && toggle) {
      webSocketStore.connect();
      
      // Set up a listener for the "Stream is ready" message
      const checkMessage = () => {
        if (webSocketStore.message === "Stream is ready") {
          handleModalClose();
          toast.success("Stream is ready");
        }
      };
      
      // Check for messages periodically
      const intervalId = setInterval(checkMessage, 100);
      
      return () => {
        clearInterval(intervalId);
      };
    }
  }, [isOpen, toggle, webSocketStore.message]);
  
  const handleModalClose = () => {
    onClose();
    setToggle(false);
  };
  


  return (
    <>
      <Button
        onPress={onOpen}
        color="primary"
        className="text-foreground font-bold max-w-52 min-w-36"
        variant="ghost"
        endContent={<BiPlus className="text-medium text-foreground" />}
      >
        Add Stream ({text})
      </Button>
      <Modal
        isOpen={isOpen}
        onOpenChange={onOpenChange}
        placement="top-center"
        size={step == 1 ? "md" : "full"}
        radius="none"
        className={step == 1 ? "" : "w-[80rem] h-[50rem]"}
      >
        <ModalContent>
          {
            toggle ? (
              <>
                <ModalHeader className="flex flex-col gap-1 text-white">
                  Stream Progress
                </ModalHeader>
                <ModalBody className="flex justify-center items-center py-8">
                  <StreamProgress message={webSocketStore.message} />
                </ModalBody>
              </>
            ) : (
              (onClose: () => void) => (
                <>
                  <ModalHeader className="flex flex-col gap-1 text-white">
                    {
                      {
                        1: "Add new stream",
                        2: "Add New Stream Line",
                      }[step]
                    }
                  </ModalHeader>
                  <ModalBody className="flex justify-start items-center">
                    {

                      {
                        1: (
                          <StepOne
                            places={places}
                            indexplace={indexplace}
                            streamtype={streamtype}
                          />
                        ),
                        2: <StepTwo streamtype={streamtype} />,
                      }[step]
                    }
                  </ModalBody>
                  <ModalFooter>
                    <Button color="danger" variant="flat" onPress={onClose}>
                      Close
                    </Button>
                    <Button
                      color="primary"
                      className="text-black"
                      onPress={
                        step == 1
                          ? () => {
                            setStep(2);
                            handleSubmitStepOne();
                          }
                          : () => {
                            setStep(1);
                            handleSubmitStepTwo();
                            setToggle(true)

                          }
                      }
                    >
                      {
                        {
                          1: "Next",
                          2: "Add",
                        }[step]
                      }
                    </Button>
                  </ModalFooter>
                </>
              )
            )
          }

        </ModalContent>
      </Modal>
    </>
  );
};
