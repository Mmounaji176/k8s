import {
  Button,
  Card,
  CardBody,

  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
} from "@nextui-org/react";
import { HardwareUsage } from "./components/HardwareUsage";
import { IoLocation, IoTrash } from "react-icons/io5";
import { useEffect, useState } from "react";
import { AddNewZoneButton } from "./components/AddNewZoneButton";
import { AddNewStreamButton } from "./components/AddNewStreamButton";
import { CameraCard } from "./components/CameraCard";
import useAxios from "../../services/axios";
import { useStreamStore } from "../../store/stream";
import { BiSearch } from "react-icons/bi";
import { useNavigate } from "react-router-dom";
import { toast } from "react-hot-toast";
import { FaceAnalytics } from '../FaceAnalytics/components/FaceAnalytics'

export function FaceRecognitionPage() {
  const navigate = useNavigate();
  const [indexPlace, setIndexPlace] = useState(0);
  const [placeId, setPlaceId] = useState(0);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [placeToDelete, setPlaceToDelete] = useState(null);
  const stream = useStreamStore();
  const axios = useAxios();

  const handleDeletePlace = async (key) => {
    try {
      await axios.delete(`/api/zones/${key}`);
      const res1 = await axios.get("/api/zones/face");
      stream.setPlaces(res1.data);
      setIsDeleteModalOpen(false);
    } catch (error) {
      console.error("Error deleting place:", error);
    }
  };

  const openDeleteModal = (placeId) => {
    setPlaceToDelete(placeId);
    setIsDeleteModalOpen(true);
  };

  const closeDeleteModal = () => {
    setIsDeleteModalOpen(false);
    setPlaceToDelete(null);
  };

  useEffect(() => {
    // Fetch places and streams
    try {
      (async () => {
        if (stream.places) {
          const res1 = await axios.get("/api/zones/face");
          stream.setPlaces(res1.data);
          if (res1.data[indexPlace]?.id) {
            setPlaceId(res1.data[indexPlace]?.id);
            const res = await axios.get(
              `/api/streamfilter/${res1.data[indexPlace]?.id}/face`
            );
            stream.load(res.data);
          } else {
            stream.load([]);
          }
        }
      })();
    } catch (e) { }
  }, [indexPlace]);

  

  return (
    <div className="flex flex-col w-full gap-4">
      <HardwareUsage />




      <Card className="flex flex-col gap-4 bg-background/40">
        <CardBody className="p-8 gap-8">
          <h1 className="text-3xl font-bold">Cameras</h1>
          <div className="flex flex-row gap-8">
            <Card className="flex flex-col min-w-[15rem] h-[20rem] sm:h-full gap-4 p-4">
              <div className="flex w-full">
                <Button
                  className="w-52 text-foreground font-bold w-full"
                  variant="bordered"
                  color="warning"
                  onClick={() =>
                    navigate("/face-recognition/analytics")
                  }
                >
                  Analytics
                </Button>
              </div>
              <div className="flex w-full">
                <Button
                  className="w-52 text-foreground font-bold w-full"
                  variant="bordered"
                  color="warning"
                  onClick={() =>
                    navigate("/face-recognition/overview/1/1/1/1/-1/known")
                  }
                >
                  Overview
                </Button>
              </div>


              <AddNewZoneButton
                places={stream.places}
                indexplace={indexPlace}
                text={"Add new place"}
                streamtype={"face"}
              />
              <div className="flex flex-col gap-2 overflow-auto scrollbar scrollbar-thumb-default-200 dark:scrollbar-thumb-default-100">
                {stream?.places?.map((item, index) => (
                  <div key={index} className="flex w-full">
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
                      className="flex justify-center items-center font-bold min-h-10 w-auto rounded-l-none"
                      onClick={() => openDeleteModal(item.id)}
                      variant={index == indexPlace ? "solid" : "light"}
                      color={index == indexPlace ? "danger" : "default"}
                      endContent={index == indexPlace ? <IoTrash /> : ""}
                    />
                  </div>
                ))}
              </div>
            </Card>
            <div className="flex flex-col gap-8">
              <AddNewStreamButton
                places={stream.places}
                indexplace={indexPlace}
                text={"Add new stream"}
                streamtype="face"
              />
              <div className="flex flex-wrap gap-4 overflow-auto scrollbar scrollbar-thumb-default-200 dark:scrollbar-thumb-default-100">
                {stream?.streams?.map((item, index) => (
                  <CameraCard
                    key={index}
                    image={item}
                    places={stream.places}
                    indexplace={indexPlace}
                    streamtype={"face"}
                  />
                ))}
              </div>
            </div>
          </div>
        </CardBody>
      </Card>

      <Modal
        isOpen={isDeleteModalOpen}
        onClose={closeDeleteModal}
        isDismissable={false}
        isKeyboardDismissDisabled={true}
      >
        <ModalContent>
          <ModalHeader>Confirm Deletion</ModalHeader>
          <ModalBody>
            Are you sure you want to delete this place? This action cannot be
            undone.
          </ModalBody>
          <ModalFooter>
            <Button color="default" onClick={closeDeleteModal}>
              Cancel
            </Button>
            <Button
              color="danger"
              onClick={() => {
                toast.promise(handleDeletePlace(placeToDelete), {
                  loading: "Deleting place...",
                  success: <b>Place deleted!</b>,
                  error: <b>Could not delete place.</b>,
                });
              }}
            >
              Delete
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}
