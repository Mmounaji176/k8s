import { Button } from "@nextui-org/button"
import {
    useDisclosure,
    Modal, ModalContent, ModalHeader, ModalBody, Input, ModalFooter
} from "@nextui-org/react"
import { useState } from "react";
import useAxios from "../../../services/axios";
import { IoPersonAdd } from "react-icons/io5";
import { useProfilesStore } from "../../../store/profiles";
import { toast } from 'react-hot-toast'
export const AddPerson = () => {
    const axios = useAxios();
    const profiles = useProfilesStore()
    const { isOpen, onOpen, onOpenChange } = useDisclosure();
    const [name, setName] = useState<undefined | string>();
    const [cin, setCin] = useState<undefined | string>();
    const [company_id, setCompany_id] = useState<undefined | string>();
    const [pictures, setPictures] = useState<any | null>(null);
    // const handleImage = (e) => {
    //     const images = Array.from(e.target.files)
    //     setPictures(images)
    // }

    const handleImage = (e) => {
        console.log(e)
        const images = Array.from(e.target.files)
        setPictures(images)

    }
    const handleSubmit = async () => {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('cin', cin);
        formData.append('company_id', company_id)
        pictures.forEach((image) => {
            formData.append(`uploaded_images`, image);
        });

        const res = await axios.post("api/profile/",
            formData
            , {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            })
        profiles.setProfiles(res.data.results)


    }
    return (
        <>
            <Button
                onPress={onOpen}
                radius="sm"
                color="primary"
                className="text-black"
                startContent={<IoPersonAdd className="text-lg text-black" />}

            >
                Add Person
            </Button>
            <Modal
                isOpen={isOpen}
                onOpenChange={onOpenChange}
                placement="top-center"
            >

                <ModalContent className="dark">
                    {(onClose) => (
                        <>
                            <ModalHeader className="flex flex-col gap-1 text-white">Add person</ModalHeader>
                            <ModalBody>
                                <Input
                                    className="text-white"
                                    autoFocus
                                    onChange={(e) => setName(e.target.value)}
                                    label="Name"
                                    placeholder="Enter stream titile"
                                    variant="bordered" />
                                <Input
                                    className="text-white"
                                    onChange={(e) => setCin(e.target.value)}
                                    label="CIN"
                                    placeholder="Enter stream titile"
                                    variant="bordered" />
                                <Input
                                    className="text-white"
                                    onChange={(e) => setCompany_id(e.target.value)}
                                    label="Company ID"
                                    placeholder="Enter stream titile"
                                    variant="bordered" />

                                <input
                                    className="text-white border-2 border-zinc-700 focus:border-gray-300 rounded-xl p-2 w-full"
                                    placeholder="image"
                                    type="file"
                                    multiple
                                    onChange={handleImage}
                                    accept="image/*"
                                />

                            </ModalBody>
                            <ModalFooter>
                                <Button color="danger" variant="flat" onPress={onClose}>
                                    Close
                                </Button>
                                <Button color="primary" onClick={() => toast.promise(handleSubmit(), {
                                    loading: "Loading...",
                                    success: "Success!",
                                    error: "Error!"
                                })}>
                                    Submit
                                </Button>
                            </ModalFooter>
                        </>
                    )}
                </ModalContent>
            </Modal></>
    )
}