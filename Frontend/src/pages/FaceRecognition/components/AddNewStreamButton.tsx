
import { Button } from "@nextui-org/button";
import {
  useDisclosure,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  Input,
  ModalFooter,
  Progress,
} from "@nextui-org/react";
import { useState, useEffect } from "react";
import useAxios from "../../../services/axios";
import { useStreamStore } from "../../../store/stream";
import { HTMLElementEvent } from "../../../types/types";
import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import { RadioGroup, Radio } from "@nextui-org/react";
import { useGpuStore } from "../../../store/gpus";
import { toast } from 'react-hot-toast';

const StreamProgress = ({ message }) => {
  const [progress, setProgress] = useState(0);

  const statusMap = {
    "Get stream from URL": 20,
    "Ai Worker started": 40,
    "Stream data created": 60,
    "Start Loading faces database": 80,
    "Trying Start Stream": 90,
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

export const AddNewStreamButton = ({ places, indexplace, text, streamtype = "face" }) => {
  const { isOpen, onOpen, onOpenChange, onClose } = useDisclosure();
  const axios = useAxios();
  const stream = useStreamStore();
  const [place, setPlace] = useState(undefined);
  const [url, setUrl] = useState(undefined);
  const [title, setTitle] = useState(undefined);
  const gpuStore = useGpuStore();
  const [selected, setSelected] = useState(0);
  const [toggle, setToggle] = useState(false);
  const [message, setMessage] = useState("Initializing...");
  const [service, setService] = useState("");

  const handleUrlChange = (e) => {
    setUrl(e.target.value);
  };

  const handleTitleChange = (e) => {
    setTitle(e.target.value);
  };

  const handleSetAuto = (value) => {
    setPlace(value);
  };

  const handleModalClose = () => {
    onClose();
    setMessage("");
    setToggle(false);
  };

  useEffect(() => {
    const socket = new WebSocket(`ws://${import.meta.env.VITE_APP_SOCKET}/wsStat/`);

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessage(data.message);

      if (data.message === "Can't start stream because no faces are found") {
        handleModalClose();
        toast.error("Can't start stream because no faces are found", { duration: 5000 });
      }

      if (data.message === "Stream is ready") {
        handleModalClose();
        toast.success("Stream is ready");
      }
    };

    if (!place && places.length > 0 && places[indexplace]) {
      setPlace(places[indexplace]?.name);
    }

    return () => {
      socket.close();
    };
  }, [indexplace]);

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

  const handleSubmit = async () => {
    setToggle(true);
    const gpuPrefix = `/gpu${selected}`;
    stream.places.forEach(async (element) => {
      try {
        if (element.id === places[indexplace].id) {
          await axios.post(
            `${gpuPrefix}/api/stream/`,
            {
              title: `${title}`,
              place: `${places[indexplace].id}`,
              url: `${url}`,
              cudadevice: selected
            }
          );
          if (places[indexplace]?.id) {
            const res = await axios.get(
              `${gpuPrefix}/api/streamfilter/${places[indexplace]?.id}/${streamtype}`
            );
            stream.load(res.data);
          } else {
            stream.load([]);
          }
          const res1 = await axios.get(`${gpuPrefix}/api/zones/${streamtype}`);
          stream.setPlaces(res1.data);
        }
      } catch (e) {
        toast.error(`Can't add stream - invalid action`);
        handleModalClose();
      }
    });
  };

  return (
    <>
      <Button
        onPress={onOpen}
        color="primary"
        className="w-52 text-foreground font-bold"
        variant="bordered"
      >
        {text}
      </Button>

      <Modal
        isOpen={isOpen}
        onOpenChange={onOpenChange}
        placement="top-center"
        isDismissable={false}
        isKeyboardDismissDisabled={true}
      >
        <ModalContent className="dark">
          {() => (
            <>
              {!toggle ? (
                <>
                  <ModalHeader className="flex flex-col gap-1 text-black dark:text-white">
                    Add Stream
                  </ModalHeader>
                  <ModalBody>
                    <Autocomplete
                      label="Place"
                      placeholder="Search for a place"
                      defaultItems={stream.places}
                      labelPlacement="outside"
                      className="w-full h-full"
                      disableSelectorIconRotation
                      onInputChange={handleSetAuto}
                      defaultSelectedKey={places[indexplace]?.name}
                    >
                      {(item) => (
                        <AutocompleteItem className="h-full" key={item?.name}>
                          {item.name}
                        </AutocompleteItem>
                      )}
                    </Autocomplete>

                    <Input
                      className="text-white"
                      autoFocus
                      onChange={handleTitleChange}
                      label="Title"
                      placeholder="Enter stream title"
                      variant="bordered"
                    />
                    <Input
                      className="text-white"
                      label="Url"
                      placeholder="Enter stream url"
                      type="text"
                      onChange={handleUrlChange}
                      variant="bordered"
                    />
                    <div className="flex flex-col gap-3">
                      <RadioGroup
                        label="Select GPU"
                        value={selected}
                        onValueChange={(val) => {
                          setSelected(val);
                          const gpuInfo = gpuStore.gpuList ? gpuStore.gpuList[val] : null;
                          if (gpuInfo && gpuInfo.service) {
                            setService(gpuInfo.service);
                          }
                        }}
                        orientation="horizontal"
                        classNames={{
                          label: "text-white",
                          wrapper: "flex flex-wrap gap-4"
                        }}
                      >
                        {Array.from({ length: gpuStore.gpus }).map((_, index) => (
                          <Radio 
                            key={index} 
                            value={index}
                            classNames={{
                              label: "text-white",
                              wrapper: "bg-background/50 p-2 rounded-lg"
                            }}
                          >
                            GPU {index + 1}
                          </Radio>
                        ))}
                      </RadioGroup>
                      <p className="text-default-500 text-small">
                        Selected: GPU {parseInt(selected) + 1}
                      </p>
                    </div>
                  </ModalBody>
                  <ModalFooter>
                    <Button color="danger" variant="flat" onPress={handleModalClose}>
                      Close
                    </Button>
                    <Button color="primary" className=" text-black dark:bg-primary-400 dark:hover:bg-primary-300" onClick={handleSubmit}>
                      Add
                    </Button>
                  </ModalFooter>
                </>
              ) : (
                <>
                  <ModalHeader className="flex flex-col gap-1 text-white">
                    Stream Progress
                  </ModalHeader>
                  <ModalBody className="flex justify-center items-center py-8">
                    <StreamProgress message={message} />
                  </ModalBody>
                </>
              )}
            </>
          )}
        </ModalContent>
      </Modal>
    </>
  );
};

export default AddNewStreamButton;