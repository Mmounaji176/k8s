import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
  useDisclosure,
  Image,
  Card,
} from "@nextui-org/react";
import { forwardRef, useImperativeHandle } from "react";
import useAxios from "../../../services/axios";

const getColor = (value) => {
  if (value >= 0 && value <= 45) return `danger`;
  if (value > 45 && value <= 54) return `warning`;
  else return `primary`;
};

export const ImagesModal = forwardRef(({ users }, ref) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const axios = useAxios();

  useImperativeHandle(ref, () => ({
    openModal: () => {
      onOpen();
    }
  }));

  return (
    <Modal 
      size="5xl" 
      isOpen={isOpen} 
      onClose={onClose} 
      className="overflow-hidden"
      scrollBehavior="inside"
    >
      <ModalContent>
        {(onClose) => (
          <>
            <ModalHeader className="flex flex-col gap-1">
              <h1 className="text-3xl font-bold">Detected Faces</h1>
            </ModalHeader>
            <ModalBody>
              <div className="flex flex-wrap gap-4 p-4">
                {users?.map((item, index) => (
                  <Card
                    key={index}
                    className="flex items-center w-[12.5rem] h-60 hover:bg-zinc-800 border border-yellow-700 rounded-xl"
                  >
                    <Image
                      src={`${import.meta.env.VITE_APP_BACKEND}${item.person.images[0].image}`}
                      radius="none"
                      className="w-[12.5rem] h-48 object-cover object-center"
                    />
                    <div className="flex w-full h-full justify-between items-center gap-2 font-semibold">
                      <p className="mx-2 text-white/80">
                        {item.person.name}
                      </p>
                      <div 
                        className={`flex items-center py-1 px-2 mx-1 rounded-lg bg-${getColor(
                          100 - item.conf_value * 100
                        )}`}
                      >
                        <p>
                          {(100 - item.conf_value * 100).toFixed(2)}%
                        </p>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </ModalBody>
            <ModalFooter>
              <Button 
                color="danger" 
                variant="light" 
                onPress={onClose}
              >
                Close
              </Button>
            </ModalFooter>
          </>
        )}
      </ModalContent>
    </Modal>
  );
});