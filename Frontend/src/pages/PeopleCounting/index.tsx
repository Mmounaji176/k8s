import React, { useEffect, useState } from 'react';
import {
  Button,
  Card,
  CardBody,
  Input,
  Radio,
  RadioGroup,
} from "@nextui-org/react";
import { BiSearch } from "react-icons/bi";
import { IoLocation, IoTrash } from "react-icons/io5";
import useAxios from "../../services/axios";
import { AddNewZoneButton } from "../FaceRecognition/components/AddNewZoneButton";
import { AddStreamCountingButton } from "./components/AddCounting";
import { useStreamStore } from "../../store/stream";
import { usePeopleCountingStore } from "./store/usePeopleCountingStore";
import { HardwareUsage } from "../FaceRecognition/components/HardwareUsage";
import { CameraCard } from "./components/CameraCard";
import { useWebSocketStore } from "./store/useSocket";

const STREAM_COUNTING_TYPE = [
  { "Gates": { "line": "DEFAULT_TYPE" } },
  { "Queue": { "zone": "DEFAULT_TYPE", "line": "QUEUE" } },
  { "Sitting": { "zone": "SITTING", "line": "SITTING" } },
  { "External flow": { "line": "EXTERNAL", "zone": "EXTERNAL" } },
  { "Stations": { "zone": "STATION_CASHIER" } }
];

export const PeopleCountingPage = () => {
  const [streamTypes, setStreamType] = usePeopleCountingStore((state) => [
    state.streamTypes,
    state.setStreamType,
  ]);

  const stream = useStreamStore();
  const axios = useAxios();
  const [indexPlace, setIndexPlace] = useState(0);
  const [searchText, setSearchText] = useState("");

  useEffect(() => {
    console.log("stream.streams effect []")
    console.log(stream.streams)
    const fetchInitialData = async () => {
      try {
        const res = await axios.get("/api/zones/line");
        stream.setPlaces(res.data);
      } catch (error) {
        console.error("Error fetching initial data:", error);
      }
    };
    fetchInitialData();
  }, []);
  useEffect(() => {
    console.log("stream.streams effect [indexPlace]")
    console.log(stream.streams)
    const fetchPlaceData = async () => {
      try {
        // if (stream.places && stream.places.length > 0) {
        const placeRes = await axios.get("/api/zones/line");
        stream.setPlaces(placeRes.data);

        const currentPlace = placeRes.data[indexPlace];
        if (currentPlace?.id) {
          const streamRes = await axios.get(
            `/peoplecounting/streamCounting/${currentPlace.id}`
          );
          stream.load(streamRes.data);
        } else {
          stream.load([]);
        }
        // }
      } catch (error) {
        console.error("Error fetching place data:", error);
        stream.load([]);
      }
    };
    fetchPlaceData();
  }, [indexPlace]);
  const webSocketStore = useWebSocketStore();
  
  // Connect to WebSocket when the app loads
  useEffect(() => {
    webSocketStore.connect();
    
    // Clean up WebSocket when the app unmounts
    return () => {
      webSocketStore.disconnect();
    };
  }, []);
  const handleDeletePlace = async (key) => {
    try {
      await axios.delete(`/api/zones/${key}`);
      const res = await axios.get("/api/zones/line");
      stream.setPlaces(res.data);
    } catch (error) {
      console.error("Error deleting place:", error);
    }
  };

  const filteredPlaces = stream.places.filter(place =>
    place.name.toLowerCase().includes(searchText.toLowerCase())
  );

  return (
    <div className="w-full p-4">
      <HardwareUsage />

      <Card className="w-full">
        <CardBody className="p-8">
          <h1 className="text-3xl font-bold mb-8">Cameras</h1>

          <div className="flex flex-row gap-8">
            {/* Left sidebar */}
            <Card className="w-64 h-[calc(100vh-300px)]">
              <CardBody className="p-4 flex flex-col gap-4">
                <Input
                  type="text"
                  placeholder="Search places..."
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  startContent={<BiSearch className="text-xl" />}
                />

                <AddNewZoneButton
                  places={stream.places}
                  indexplace={indexPlace}
                  text="Add new place"
                  streamtype="line"
                />

                <div className="flex-1 overflow-y-auto">
                  {filteredPlaces?.map((item, index) => (
                    <div className="flex mb-2" key={item.id}>
                      <Button
                        variant={index == indexPlace ? "solid" : "light"}
                        color={index == indexPlace ? "primary" : "default"}
                        onClick={() => setIndexPlace(index)}
                        className={`flex justify-between font-bold min-h-10 w-full rounded-r-none ${index == indexPlace ? "text-black" : "text-white"
                          }`}
                        endContent={index == indexPlace ? <IoLocation /> : ""}
                      >
                        {item.name}
                      </Button>
                      <Button
                        onClick={() => handleDeletePlace(item.id)}
                        variant={index === indexPlace ? "solid" : "light"}
                        color={index === indexPlace ? "danger" : "default"}
                        className="px-3 rounded-l-none"
                      >
                        <IoTrash />
                      </Button>
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>

            {/* Main content */}
            <div className="flex-1">
              <div className="space-y-8">
                {STREAM_COUNTING_TYPE?.map((typeObj, index) => {
                  const typeName = Object.keys(typeObj)[0];
                  const typeConfig = typeObj[typeName];
                  const hasLine = 'line' in typeConfig;
                  const hasZone = 'zone' in typeConfig;

                  return (
                    <div key={typeName} className="space-y-4">
                      <h2 className="text-2xl font-bold">{typeName}</h2>

                      <div className="flex items-center gap-4">
                        <AddStreamCountingButton
                          places={stream.places}
                          indexplace={indexPlace}
                          text={`Add ${typeName}`}
                          streamtype={streamTypes[index]}
                          category_name={typeName}
                          model_type={stream.model}
                          camera_type={
                            streamTypes[index] === 'zone' ? typeConfig.zone :
                              streamTypes[index] === 'line' ? typeConfig.line :
                                null
                          }
                        />

                        <RadioGroup
                          orientation="horizontal"
                          value={streamTypes[index]}
                          onValueChange={(newType) => setStreamType(index, newType)}
                          defaultValue={hasLine ? "line" : "zone"}
                        >
                          <Radio value="line" isDisabled={!hasLine}>Line</Radio>
                          <Radio value="zone" isDisabled={!hasZone}>Zone</Radio>
                        </RadioGroup>
                      </div>

                      <div className="flex flex-wrap gap-4 overflow-auto scrollbar scrollbar-thumb-default-200 dark:scrollbar-thumb-default-100">
                        {stream.streams
                          .filter(item => item.category_name === typeName)
                          .map((item, i) => (
                            <CameraCard
                              key={`${item.id}-${i}`}
                              image={item}
                              places={stream.places}
                              indexplace={indexPlace}
                              streamtype={streamTypes[index]}
                            />
                          ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};