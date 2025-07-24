import { Button } from "@nextui-org/button";
import {
  useDisclosure,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  Input,
  ModalFooter,
} from "@nextui-org/react";
import { useState } from "react";
import useAxios from "../../../services/axios";
import { useStreamStore } from "../../../store/stream";
import { HTMLElementEvent } from "../../../types/types";
export const AddNewZoneButton = ({ places, indexplace, text, streamtype = "face" }: any) => {
  const axios = useAxios();
  const stream = useStreamStore();
  const { isOpen, onOpen, onOpenChange } = useDisclosure();
  const [place, setPlace] = useState<undefined | string>();

  const handlePlaceChange = (e: HTMLElementEvent<HTMLInputElement>) => {
    setPlace(e.target.value);
  };

  const handleSubmit = async () => {
    await axios.post("/api/zones/", {
      name: `${place}`,
      type: `${streamtype}`,
    });
    if (places[indexplace]?.id) {
      const res = await axios.get(
        `/api/streamfilter/${places[indexplace]?.id}/${streamtype}`
      );
      stream.load(res.data);

    } else {
      stream.load([])
    }
    const res1 = await axios.get(`/api/zones/${streamtype}`);
    stream.setPlaces(res1.data);
  };
  return (
    <>
      <Button
        onPress={onOpen}
        color="primary"
        className="w-52 text-foreground font-bold w-full"
        variant="bordered"
      >
        {text}
      </Button>
      <Modal isOpen={isOpen} onOpenChange={onOpenChange} placement="top-center" isDismissable={false} isKeyboardDismissDisabled={true}>
        <ModalContent className="dark">
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1 text-white">
                Add Stream
              </ModalHeader>
              <ModalBody>

                <Input
                  className="text-white"
                  autoFocus
                  onChange={handlePlaceChange}
                  label="Place"
                  placeholder="Enter stream place"
                  variant="bordered"
                />


              </ModalBody>
              <ModalFooter>
                <Button color="danger" variant="flat" onPress={onClose}>
                  Close
                </Button>
                <Button
                  color="primary"
                  onClick={handleSubmit}
                  onPress={onClose}
                  className="text-black"
                >
                  Add
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </>
  );
};
