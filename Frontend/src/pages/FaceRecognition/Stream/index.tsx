import {
  Button,
  Card,
  CardBody,
  CardFooter,
  CardHeader,
  Image,
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
  Spinner,
  Tabs,
  Tab,
  Pagination,
  Progress,
} from "@nextui-org/react";
import "./style/index.css";
import { useEffect, useRef, useState, memo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useDetectionStore } from "../../../store/detection";
import useAxios from "../../../services/axios";
import { convertDateTime } from "../../../services/dateconverter";
import { ImagesModal } from "./components/ImagesModal";
import JanusStreaming from "./components/StreamWebRtc";
import toast, { Toaster } from "react-hot-toast";
import { useLocalDetectionStore } from "./store";
// import { FaceAnalyticsPage } from "../../FaceAnalytics";
import { FaceAnalytics } from '../../FaceAnalytics/components/FaceAnalytics'
const ITEMS_PER_PAGE = 20;
const BACKEND_URL = import.meta.env.VITE_APP_BACKEND;

export const getColor = (value) => {
  if (value >= 0 && value <= 45) return 'danger';
  if (value > 45 && value <= 54) return 'warning';
  return 'primary';
};

export const getPersonIndex = (obj, id) => {
  return obj.findIndex(item => id === item.detection_persons[0].person.id) || 0;
};

export function StreamPage() {
  const controller = new AbortController();
  const navigate = useNavigate();
  const axios = useAxios();
  const userStore = useDetectionStore();
  const [stream, setStream] = useState(null);
  const detectionStore = useLocalDetectionStore();
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);
  const [selectedDetection, setSelectedDetection] = useState(null);
  const { id, str } = useParams();
  const ws = useRef(null);
  const animateKnownRef = useRef(false);
  const animateHighRef = useRef(false);
  const animateUnknownRef = useRef(false);
  const testRef = useRef(null);
  const [loadingState, setLoadingState] = useState("idle");
  const [streamStat, setStreamStat] = useState("Stream");
  const [faceStats, setFaceStats] = useState(null);

  const ChangeStream = (event: any) => {
    setStreamStat(event);
  }
  const [animate, setAnimate] = useState({
    known: false,
    high: false,
    unknown: false,
  });

  const toggle = (event: any) => {
    if (str !== event) navigate(`/face-recognition/${id}/${event}`);
  };
  useEffect(() => {
    const fetchDetections = async () => {
      setLoadingState("loading");
      try {
        const res = await axios.get(
          `/api/stream_detections/${userStore.user || id}/${str}?page=${page}`,
          { signal: controller.signal }
        );
        detectionStore.setDetections(res.data.results);
        setCount(Math.ceil(res.data.count / ITEMS_PER_PAGE));
      } catch (error) {
        console.error("Error fetching detections:", error);
      }
      setLoadingState("idle");
    };

    fetchDetections();
    return () => {
      detectionStore.setDetections([]);
      controller.abort();
    };
  }, [id, page, str, userStore.user]);

  useEffect(() => {
    setPage(1);
  }, [str]);

  useEffect(() => {
    const fetchFaceStats = async () => {
      try {
        const response = !id
          ? await axios.get("/faceanalyzer/face_stats")
          : await axios.get(`/faceanalyzer/face_stats/${id}`);
        setFaceStats(response.data);
      } catch (error) {
        console.error("Error fetching face stats:", error);
      }
    };
    fetchFaceStats();
    const fetchStream = async () => {
      try {
        setLoadingState("loading");
        const res = await axios.get(`/api/stream_page/${id}`);
        setStream(res.data);
      } catch (error) {
        console.error("Error fetching stream:", error);
      }
      setLoadingState("idle");
    };

    fetchStream();
    testRef.current?.click();
  }, []);

  useEffect(() => {
    ws.current = new WebSocket(
      `ws://${import.meta.env.VITE_APP_SOCKET}/wsNotification/`
    );

    ws.current.onmessage = function (event) {
      const data = JSON.parse(event.data);

      // Handle face analytics data
      // console.log(data)
      if (data.message.faceanalytics) {
        const detections = detectionStore.getDetections();
        const updatedDetections = detections.map(detection => {
          // console.log(`${detection.id} | ${data.message.detection_ids}`)
          if (detection.id === data.message.detection_ids) {
            // console.log("done inside ")
            if (data.message?.error) {
              return {
                ...detection,

                deep_face_processed: true
              };
            }
            else {
              return {
                ...detection,
                json_result: {
                  results: [{
                    age: data.message.age,
                    dominant_gender: data.message.dominant_gender,
                    dominant_emotion: data.message.dominant_emotion,
                    dominant_race: data.message.dominant_race
                  }]
                },
                deep_face_processed: true
              };
            }
          }

          return detection;
        });
        detectionStore.setDetections(updatedDetections);
        return;
      }

      // Handle detection data
      const confValue = parseFloat(data.message.detection_persons[0].conf_value);
      const confThreshold = parseFloat(import.meta.env.VITE_APP_CONF_VALUE);
      const highConfThreshold = parseFloat(import.meta.env.VITE_APP_CONF_HIGH_VALUE);

      // Update animation states
      if (confValue >= confThreshold && confValue < highConfThreshold && str !== "high" && id == data.message.video_source) {
        animateHighRef.current = true;
      }
      if (confValue > confThreshold && str !== "unknowns" && id == data.message.video_source) {
        animateUnknownRef.current = true;
      }
      if (confValue <= confThreshold && str !== "known" && id == data.message.video_source) {
        animateKnownRef.current = true;
      }

      setAnimate({
        high: animateHighRef.current,
        unknown: animateUnknownRef.current,
        known: animateKnownRef.current
      });

      // Update detections based on confidence values
      if (page === 1 && id == data.message.video_source) {
        const currentDetections = detectionStore.getDetections();
        let newDetections;

        if (currentDetections.length >= 20) {
          newDetections = [data.message, ...currentDetections.slice(0, 19)];
        } else {
          newDetections = [data.message, ...currentDetections];
        }

        const shouldUpdate = (
          (confValue > highConfThreshold && str === "unknowns") ||
          (confValue > confThreshold && confValue <= highConfThreshold && str === "high") ||
          (confValue < confThreshold && str === "known")
        );

        if (shouldUpdate) {
          detectionStore.setDetections(newDetections);
        }
      }
    };

    // Reset animation flags based on current tab
    if (str === "known") animateKnownRef.current = false;
    if (str === "high") animateHighRef.current = false;
    if (str === "unknowns") animateUnknownRef.current = false;

    setAnimate({
      high: animateHighRef.current,
      unknown: animateUnknownRef.current,
      known: animateKnownRef.current
    });

    return () => {
      detectionStore.setDetections([]);
      ws.current?.close();
    };
  }, [str]);

  const handleMarkPerson = async (person, idx) => {
    try {
      await axios.post("/api/marked_person", {
        person_id: person.person.id,
        detection_id: idx,
      });

      detectionStore.updateDetectionPerson(idx, person.person.id, true);
      setSelectedDetection(detectionStore.getDetections().find((item) => item.id === selectedDetection.id));
    } catch (error) {
      console.error("Error marking person:", error);
    }
  };

  const handleOpenModal = async (detection) => {
    try {
      await axios.post(`/api/mark_read`, { id: detection.id });
      const updatedDetections = detectionStore.getDetections().map(item =>
        item.id === detection.id ? { ...item, is_read: true } : item
      );
      detectionStore.setDetections(updatedDetections);
    } catch (error) {
      console.error("Error updating detection:", error);
    }
    setSelectedDetection(detection);
  };

  const handleCloseModal = () => {
    setSelectedDetection(null);
  };
  return (
    <div className="flex w-full flex-col lg:flex-row" ref={testRef}>
      <Toaster />

      <div className="flex flex-col lg:flex-row w-full">
        <div className="flex flex-col w-full ">
          <h1 className="text-4xl font-bold">{stream?.title}</h1>
          <Card className="bg-background/80 w-full p-4 ">
            <CardHeader className=" ">
              <h1 className="text-3xl font-bold">Live Stream</h1>
            </CardHeader>
            <Tabs
              aria-label="Options"
              color="primary"
              selectedKey={streamStat}
              onSelectionChange={ChangeStream}
            >

              <Tab
                key="Stream"

                className={`text-white text-bold`}
                title="Stream"
              />
              <Tab key="Ai Stream" className={`text-white text-bold`} title="Ai Stream" />


            </Tabs>
            {
              id && streamStat === "Ai Stream" && <CardBody className="pt-24"><JanusStreaming id={id} /></CardBody>

            }
            {
              id && streamStat === "Stream" && <CardBody className="pt-24"> <JanusStreaming id={(2147483647 - id)} /></CardBody>
            }

          </Card>
          <div className="mt-8">
            {/* <FaceAnalyticsPage id={id} /> */}
            <FaceAnalytics faceStats={faceStats} />

          </div>
        </div>
      </div>

      {/* Single Modal outside the loop */}
      {selectedDetection && (
        <Modal
          isOpen={!!selectedDetection}
          onOpenChange={handleCloseModal}
          size="3xl"
          className="p-4"
        >
          <ModalContent>
            <ModalHeader className="text-3xl">Detections</ModalHeader>
            <ModalBody className="flex flex-col justify-center items-center gap-4">
              <ImagesModal users={selectedDetection} />
              <div className="flex justify-between w-full gap-x-4">
                <div className="relative flex flex-col gap-2">
                  <h1 className="text-xl font-bold">Most Accurate</h1>
                  <div className="relative">
                    <Card radius="lg" className="flex flex-wrap border-none" >
                      <Image alt="Detection de" onClick={() => handleMarkPerson(selectedDetection.detection_persons[0], parseInt(selectedDetection.id))}
                        src={`${BACKEND_URL}${selectedDetection.detection_persons[0].person.images[0].image}`}
                        className={`w-52 h-52 min-w-36 object-cover object-center ${selectedDetection.detection_persons[0].marked_person ? "border-green-500 border-8 border-spacing-10" : "border-4 border-danger"}`}
                      />
                      <CardFooter className="justify-between bg-background/80 overflow-hidden py-1 absolute bottom-1 w-[calc(100%_-_8px)] shadow-small ml-1 z-10">
                        <p className="text-xl text-white/80">
                          {selectedDetection.detection_persons[0].person.name}
                        </p>
                        <p
                          className={`text-lg text-${getColor(
                            100 -
                            selectedDetection.detection_persons[0]
                              .conf_value *
                            100
                          )}`}
                        >
                          {(
                            100 -
                            selectedDetection.detection_persons[0].conf_value *
                            100
                          ).toFixed(2)}
                          %
                        </p>
                      </CardFooter>
                    </Card>
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  <h1 className="text-xl font-bold">Probabilities</h1>
                  <div className="flex flex-wrap gap-8">
                    {selectedDetection?.detection_persons
                      .slice(1)
                      .map((person, idx) => (
                        <Card key={idx} radius="lg" className="border-none ">
                          <Image onClick={() => handleMarkPerson(person, parseInt(selectedDetection.id))}
                            src={`${BACKEND_URL}${person.person.images[0].image}`}
                            alt="Detection as"
                            className={`w-52 h-52 object-cover object-center ${person.marked_person ? "border-green-500 border-8 border-spacing-10" : "border-4 border-danger"}`}
                          />
                          <CardFooter className="justify-between bg-background/80 overflow-hidden py-1 absolute bottom-1 w-[calc(100%_-_8px)] shadow-small ml-1 z-10">
                            <p className="text-xl text-white/80">
                              {person.person.name}
                            </p>
                            <p
                              className={`text-lg text-${getColor(
                                100 - person.conf_value * 100
                              )}`}
                            >
                              {(100 - person.conf_value * 100).toFixed(2)}%
                            </p>
                          </CardFooter>
                        </Card>
                      ))}
                  </div>
                </div>
              </div>
            </ModalBody>
          </ModalContent>
        </Modal>
      )}

      <div className="flex flex-col w-full lg:w-1/2 p-4 bg-background/80">
        <Card className="flex flex-col w-full p-4 bg-background/80">
          <CardHeader>
            <h1 className="text-4xl font-bold">Recognized People</h1>
          </CardHeader>
          <CardBody className="flex flex-col gap-4">
            {/* <SearchInput /> */}
            <Tabs
              aria-label="Options"
              color="primary"
              selectedKey={str}
              onSelectionChange={toggle}
            >
              <Tab
                onClick={() =>
                  toast.success("Stream loaded successfully", { duration: 4000 })
                }
                key="known"
                aria-label="Known persons tab"
                className={`text-white text-bold ${animate.known
                  ? "flex space-x-4 p-4 bg-gradient-to-r from-blue-500 via-transparent to-transparent animate-gradient"
                  : ""
                  }`}
                title="Known"
              />
              <Tab
                key="high"
                aria-label="high persons tab"
                className={`text-white text-bold ${animate.high
                  ? "flex space-x-4 p-4 bg-gradient-to-r from-blue-500 via-transparent to-transparent animate-gradient"
                  : ""
                  }`}
                title="High"
              />
              <Tab
                key="unknowns"
                aria-label="unknown persons tab"
                className={`text-white text-bold ${animate.unknown
                  ? "flex space-x-4 p-4 bg-gradient-to-r from-blue-500 via-transparent to-transparent animate-gradient"
                  : ""
                  }`}
                title="Unknowns"
              />
            </Tabs>
            <Table
              removeWrapper
              isHeaderSticky
              selectionMode="single"
              aria-label="Collection Detection Table"
              className="overflow-auto scrollbar scrollbar-thumb-default-200 h-[45rem]"
            >
              <TableHeader>
                <TableColumn aria-label="Detection image" className="w-[240px]">DETECTION</TableColumn>
                <TableColumn aria-label="Detection face" className="w-[160px]">FACE</TableColumn>
                <TableColumn aria-label="Detection name" className="w-[150px]">NAME</TableColumn>
                <TableColumn aria-label="Detection analyt" className="w-[280px]">ANALYTICS</TableColumn>
                <TableColumn aria-label="Detection date" className="w-[120px]">DATE</TableColumn>
                <TableColumn aria-label="Detection actions" className="w-[100px]">ACTIONS</TableColumn>
              </TableHeader>
              <TableBody
                className=""
                items={detectionStore?.detections ?? []}
                loadingContent={<Spinner />}
                loadingState={loadingState}
              >
                {detectionStore && detectionStore.detections && detectionStore.detections.length && detectionStore.detections.map((item: any, index: number) => (
                  <TableRow
                    onClick={() => handleOpenModal(item)}
                    key={index}
                    className={`${!item.is_read
                      ? "bg-gradient-to-r from-blue-500 via-transparent to-transparent animate-gradient my-10"
                      : ""
                      }`}
                  >
                    <TableCell>
                      <Image
                        alt="Detection frame"
                        src={`${BACKEND_URL}${item.detection_frame}`}
                        className="w-52 h-20 min-w-40 object-cover object-center rounded-lg"
                      />
                    </TableCell>
                    <TableCell>
                      <Image
                        alt="Detection face"
                        src={`${BACKEND_URL}${item?.detection_persons[0].person.images[0].image}`}
                        className="w-26 h-20 min-w-20 object-cover object-center rounded-lg"
                      />
                    </TableCell>
                    <TableCell>
                      <span className="font-medium">{item.detection_persons[0].person.name}</span>
                    </TableCell>
                    <TableCell>
                      {!item.json_result?.results?.[0] && item?.deep_face_processed && (
                        <div className="flex flex-col space-y-1 justify-center items-center">
                          Could not analyze face
                        </div>
                      )}
                      {!item.json_result?.results?.[0] && !item?.deep_face_processed && (

                        <div>
                          <Progress isIndeterminate aria-label="Loading..." className="max-w-md" size="sm" />

                        </div>

                      )}
                      {item.json_result?.results?.[0] && (
                        <div className="flex flex-col space-y-1">
                          <div className="flex items-start w-full">
                            <div className="w-24 flex-shrink-0 text-sm text-gray-400">Age:</div>
                            <div className="text-sm font-medium flex-1">{item.json_result.results[0].age}</div>
                          </div>
                          <div className="flex items-start w-full">
                            <div className="w-24 flex-shrink-0 text-sm text-gray-400">Emotion:</div>
                            <div className="text-sm font-medium flex-1 capitalize">{item.json_result.results[0].dominant_emotion}</div>
                          </div>
                          <div className="flex items-start w-full">
                            <div className="w-24 flex-shrink-0 text-sm text-gray-400">Gender:</div>
                            <div className="text-sm font-medium flex-1">{item.json_result.results[0].dominant_gender}</div>
                          </div>

                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <span className="text-sm whitespace-nowrap">{convertDateTime(item.created)}</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-2">
                        <Button
                          size="sm"
                          variant="solid"
                          color="primary"
                          className="text-black"
                          onClick={() => handleOpenModal(item)}
                        >
                          Details
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          color="primary"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/face-recognition/profiles/${item.detection_persons[0].person.id}`);
                          }}
                        >
                          Profile
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div className="flex item-center justify-center">
              <Pagination
                showControls
                color="primary"
                total={count}
                initialPage={1}
                onChange={setPage}
              />
            </div>
          </CardBody>
        </Card>

      </div>
    </div>
  );
}

