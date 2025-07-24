import { Button, Card, CardBody, Input } from "@nextui-org/react";
import { BiSearch } from "react-icons/bi";
import { IoLocation, IoTrash } from "react-icons/io5";
import { StreamCard } from "./components/StreamCard";
import { AddNewStreamLineButton } from "./components/AddNewStreamLine";
import useAxios from "../../services/axios";
import { useStreamStore } from "../../store/stream";
import { useEffect, useState } from "react";
import { CameraCard } from "../FaceRecognition/components/CameraCard";
import { AddNewZoneButton } from "../FaceRecognition/components/AddNewZoneButton";

export const LineCounterPage = () => {
  const stream = useStreamStore();
  const axios = useAxios();
  const [indexPlace, setIndexPlace] = useState(0);

  const handleDeletePlace = async (key: number) => {
    await axios.delete(`/api/zones/${key}`);
    const res1 = await axios.get("/api/zones/line");
    stream.setPlaces(res1.data);
  };
  useEffect(() => {
    (async () => {
      const res1 = await axios.get("/api/zones/line");
      stream.setPlaces(res1.data);
    })();
  }, []);
  useEffect(() => {
    try {
      (async () => {
        if (stream.places) {
          const res1 = await axios.get("/api/zones/line");
          stream.setPlaces(res1.data);
          if (res1.data[indexPlace]?.id) {
            const res = await axios.get(
              `/api/streamfilter/${res1.data[indexPlace]?.id}/line`
            );
            stream.load(res.data);
          } else {
            stream.load([]);
          }
        }
      })();
    } catch (e) {}
  }, [indexPlace]);
  return (
    <Card className="flex flex-col gap-4 bg-background/40">
      <CardBody className="p-8 gap-8">
        <h1 className="text-3xl font-bold">Cameras</h1>
        <div className="flex flex-row gap-8">
          <Card className="flex flex-col min-w-[15rem] h-[20rem] sm:h-full gap-4 p-4">
            <Input
              type="text"
              placeholder="Search..."
              endContent={<BiSearch className="h-12" />}
            />
            <AddNewZoneButton
              places={stream.places}
              indexplace={indexPlace}
              text={"Add new place"}
              streamtype={"line"}
            />

            <div className="flex flex-col gap-2 overflow-auto scrollbar scrollbar-thumb-default-200 dark:scrollbar-thumb-default-100">
              {stream?.places?.map((item, index) => (
                <div className="flex  w-full">
                  <Button
                    key={index}
                    variant={index == indexPlace ? "solid" : "light"}
                    color={index == indexPlace ? "primary" : "default"}
                    onClick={() => setIndexPlace(index)}
                    className="flex justify-between font-bold min-h-10 w-full rounded-r-none"
                    endContent={index == indexPlace ? <IoLocation /> : ""}
                  >
                    {item.name}
                  </Button>
                  <Button
                    className="flex justify-center items-center font-bold min-h-10 w-auto rounded-l-none "
                    key={item.id}
                    onClick={() => handleDeletePlace(item.id)}
                    variant={index == indexPlace ? "solid" : "light"}
                    color={index == indexPlace ? "danger" : "default"}
                    endContent={index == indexPlace ? <IoTrash /> : ""}
                  ></Button>
                </div>
              ))}
            </div>
          </Card>
          <div className="flex flex-col gap-8">
            <AddNewStreamLineButton
              places={stream.places}
              indexplace={indexPlace}
              text={"Add new stream"}
              streamtype={"line"}
            />

            <div className="flex flex-wrap gap-4 overflow-auto scrollbar scrollbar-thumb-default-200 dark:scrollbar-thumb-default-100">
              {stream?.streams?.map((item, index) => (
                <CameraCard
                  key={index}
                  image={item}
                  places={stream.places}
                  indexplace={indexPlace}
                  streamtype={"line"}
                />
              ))}
            </div>
          </div>
        </div>
      </CardBody>
    </Card>
  );
};
