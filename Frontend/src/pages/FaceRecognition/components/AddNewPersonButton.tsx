import {
  Button,
  Input,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  useDisclosure,
} from "@nextui-org/react";
import { IoMdPersonAdd } from "react-icons/io";

export function AddNewPersonButton() {
  const { isOpen, onOpenChange } = useDisclosure();

  return (
    <>
      <Button
        variant="ghost"
        color="primary"
        onClick={onOpenChange}
        endContent={<IoMdPersonAdd />}
      >
        <p className="text-tiny">Add Person</p>
      </Button>
      <Modal
      isDismissable={false} isKeyboardDismissDisabled={true}
        backdrop="blur"
        isOpen={isOpen}
        onOpenChange={onOpenChange}
        placement="center"
      >
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1">
                Add person
              </ModalHeader>
              <ModalBody>
                <Input
                  autoFocus
                  label="Name"
                  placeholder="Enter stream titile"
                  variant="bordered"
                />
                <Input
                  placeholder="image"
                  type="file"
                  multiple
                  variant="bordered"
                />
              </ModalBody>
              <ModalFooter>
                <Button color="danger" variant="flat" onPress={onClose}>
                  Close
                </Button>
                <Button color="primary" onPress={onClose}>
                  Submit
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </>
  );
}
