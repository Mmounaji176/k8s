
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
} from "@nextui-org/react";
import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import { Stage, Layer, Line, Circle, Text, Image } from "react-konva";
import useImage from "use-image";
import { useStreamStore } from "../../../store/stream";
import useAxios from "../../../services/axios";
import { HTMLElementEvent } from "../../../types/types";
import { create } from "zustand";
import { useGpuStore } from "../../../store/gpu";

type STORE = {
  place: string;
  url: string;
  title: string;
};
type ACTION = {
  setPlace: (data: string) => void;
  setUrl: (data: string) => void;
  setTitle: (data: string) => void;
  setResponse: (data: any) => void;
  response: any;
  handleSubmit: () => void;
};
const useAddStreamStore = create<STORE & ACTION>((set) => ({
  place: "",
  url: "",
  title: "",
  response: null,
  setPlace(data) {
    set({ place: data });
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
  handleSubmit() {
    console.log("Submit");
  },
}));

const calculateHypotenuse = (points: { x: number; y: number }[]) => {
  return Math.sqrt(
    Math.pow(points[1].x - points[0].x, 2) +
      Math.pow(points[1].y - points[0].y, 2)
  );
};

const ImageWithPoints = ({ imageUrl }: { imageUrl: string }) => {
  const [image] = useImage(imageUrl);

  const [points, setPoints] = useState<
    {
      x: number;
      y: number;
    }[]
  >([]);

  const yOffset = 100;
  const xOffset = 50;

  const handleStageClick = (e: { target: { getStage: () => any } }) => {
    const stage = e.target.getStage();
    const point = stage.getPointerPosition();
    console.log(point);
    if (points.length === 2) {
      setPoints([point]);
      return;
    }
    setPoints([...points, point]);
  };

  return (
    <Stage
      width={image ? image.width : 970}
      height={image ? image.height : 600}
    >
      <Layer>
        <Image
          image={image}
          onClick={handleStageClick}
          width={image ? image.width : 970}
          height={image ? image.height : 600}
        />
        {points.map((point, index) => (
          <Circle
            key={`circle-${index}`}
            x={point.x}
            y={point.y}
            radius={5}
            fill="orange"
          />
        ))}
        {points.length === 2 && (
          <>
            <Text
              text="In"
              x={
                (points[0].x + points[1].x) / 2 +
                ((points[1].y - points[0].y) / calculateHypotenuse(points)) *
                  xOffset
              }
              y={
                (points[0].y + points[1].y) / 2 +
                ((points[1].x - points[0].x) / calculateHypotenuse(points)) *
                  yOffset
              }
              fill="yellow"
              fontSize={26}
              fontVariant="bold"
              stroke="orange"
              strokeWidth={1}
            />
            <Line
              points={[points[0].x, points[0].y, points[1].x, points[1].y]}
              stroke="yellow"
              strokeWidth={2}
            />
            <Text
              text="Out"
              x={
                (points[0].x + points[1].x) / 2 -
                ((points[1].y - points[0].y) / calculateHypotenuse(points)) *
                  xOffset
              }
              y={
                (points[0].y + points[1].y) / 2 -
                ((points[1].x - points[0].x) / calculateHypotenuse(points)) *
                  yOffset
              }
              fill="yellow"
              fontSize={26}
              fontVariant="bold"
              stroke="orange"
              strokeWidth={1}
            />
          </>
        )}
      </Layer>
    </Stage>
  );
};

const StepOne = (places: any, indexplace: number, streamtype: string) => {
  const flag = false;
  const stream = useStreamStore();

  const streamStore = useAddStreamStore();

  const handleUrlChange = (e: HTMLElementEvent<HTMLInputElement>) => {
    streamStore.setUrl(e.target.value);
  };
  const handleTitleChange = (e: HTMLElementEvent<HTMLInputElement>) => {
    streamStore.setTitle(e.target.value);
  };

  const handleSetAuto = (value: string) => {
    streamStore.setPlace(value);
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
        </>
      )}
    </>
  );
};

const StepTwo = () => {
  const streamStore = useAddStreamStore();
  console.log(streamStore.response);
  console.log(`${import.meta.env.VITE_APP_BACKEND}${streamStore.thumbnail}`);
  return (
    <ImageWithPoints
      imageUrl={`${import.meta.env.VITE_APP_BACKEND}${
        streamStore.response?.thumbnail
      }`}
    />
  );
};

export const AddNewStreamLineButton = ({
  places,
  indexplace,
  text,
  streamtype,
}: any) => {
  const { onOpen, isOpen, onOpenChange } = useDisclosure();
  const [step, setStep] = useState(1);
  const axios = useAxios();
  const streamStore = useAddStreamStore();
  const stream = useStreamStore();
  const [service, setService] = useState("");
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

  const handleSubmit = async () => {
    const gpuPrefix = `/gpu${selected}`;
    stream.places.forEach(async (element) => {
      if (element.name === streamStore.place) {
        const response = await axios.post(
          `${gpuPrefix}/api/stream/`,
          {
            title: `${streamStore.title}`,
            place: `${element.id}`,
            url: `${streamStore.url}`,
            websocket_url: `${streamStore.url}`,
          }
        );
        streamStore.setResponse(response.data);
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
    });
  };
  return (
    <>
      <Button
        onPress={onOpen}
        color="primary"
        className="w-52 text-foreground font-bold "
        variant="bordered"
      >
        Add new Stream
      </Button>
      <Modal
        isOpen={isOpen}
        onOpenChange={onOpenChange}
        placement="top-center"
        size={step == 1 ? "md" : "full"}
        radius="none"
        className={step == 1 ? "" : "w-[70vw] h-[80vh]"}
      >
        <ModalContent>
          {(onClose: () => void) => (
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
                    2: <StepTwo />,
                  }[step]
                }
              </ModalBody>
              <ModalFooter>
                <Button color="danger" variant="flat" onPress={onClose}>
                  Close
                </Button>
                <Button
                  color="primary"
                  onPress={
                    step == 1
                      ? () => {
                          setStep(2);
                          handleSubmit();
                        }
                      : () => {
                          setStep(1);
                          onClose();
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
          )}
        </ModalContent>
      </Modal>
    </>
  );
};
