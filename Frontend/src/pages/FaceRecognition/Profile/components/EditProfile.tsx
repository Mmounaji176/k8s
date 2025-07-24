import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
  useDisclosure,
  Input,
  Image,
  Card,
  CardHeader,
} from "@nextui-org/react";
import { useState } from "react";
import { FaEdit } from "react-icons/fa";
import { IoIosRemoveCircle, IoMdAddCircle } from "react-icons/io";
import { RiEdit2Fill } from "react-icons/ri";
import useAxios from "../../../../services/axios";
export const EditProfileModal = ({ user }: any) => {
  const axios = useAxios();
  const { isOpen, onOpen, onOpenChange } = useDisclosure();
  const [name, setName] = useState(user.name);
  const [cin, setCin] = useState(user.cin);
  const [company_id, setCompany_id] = useState(user.company_id);
  const handleSave = async () => {
    try {
      const formdata = new FormData();
      formdata.append("name", name);
      formdata.append("cin", cin);
      formdata.append("company_id", company_id);
      await axios.patch(`/api/profile/${user.id}`, formdata)
    }
    catch (e) {
    }
  }
  return (
    <>
      <Button onPress={onOpen} className="text-black" startContent={<RiEdit2Fill /> } color="primary">
      Edit Profile
    </Button >
      <Modal isOpen={isOpen} onOpenChange={onOpenChange}>
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex items-center gap-4">
                <FaEdit />
                <h1 className="text-xl">Edit Profile</h1>
              </ModalHeader>
              <ModalBody>
                <h1>Profile Images</h1>
                <div className="flex gap-8 w-full overflow-auto py-4 scrollbar scrollbar-thumb-default-200 dark:scrollbar-thumb-default-100">
                  {user?.images?.map((item: any, index: number) => (
                    <div key={index} className="relative">
                      {/* <Button
                        color="danger"
                        className="flex absolute justify-center items-center -top-4 -right-4 z-10 w-8 h-8"
                        endContent={<IoIosRemoveCircle />}
                        isIconOnly
                      /> */}
                      <Image
                        key={index}
                        src={`${import.meta.env.VITE_APP_BACKEND}${item.image}`}
                        className="z-0 min-w-28 w-28 h-28 object-cover object-center"
                      />
                    </div>
                  ))}
                  <Card
                    as="button"
                    className="flex justify-center items-center w-28 h-28 brightness-125"
                  >
                    <CardHeader className="flex justify-center items-center w-full h-full">
                      <IoMdAddCircle className="w-12 h-12" />
                    </CardHeader>
                  </Card>
                </div>
                <h1>Profile Fullname</h1>
                <Input type="text" value={name} label="Fullname" onChange={(e) => setName(e.target.value)} />
                <h1>Profile CNI</h1>
                <Input type="text" label="CNI" value={cin} onChange={(e) => setCin(e.target.value)} />
                <h1>Profile Company</h1>
                <Input type="text" label="Company" value={company_id} onChange={(e) => setCompany_id(e.target.value)} />
              </ModalBody>
              <ModalFooter>
                <Button color="danger" variant="light" onPress={onClose}>
                  Close
                </Button>
                <Button color="primary" onPress={onClose} onClick={handleSave}>
                  Save
                </Button>
                <Input type="file" multiple className="hidden" />
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </>
  );
};
