import { Button, Card, CardFooter, CardHeader, Modal, ModalBody, ModalContent, ModalFooter, ModalHeader } from "@nextui-org/react";
import { RiDeleteBin6Fill } from "react-icons/ri";
import { useNavigate } from "react-router-dom";
import useAxios from "../../../services/axios";
import { useStreamStore } from "../../../store/stream";
import { useState } from "react";
export function CameraCard(image: any, streamtype = "face") {
    const navigate = useNavigate();
    const stream = useStreamStore();
    const axios = useAxios();
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

    const openDeleteModal = () => {
        setIsDeleteModalOpen(true);
    };

    const closeDeleteModal = () => {
        setIsDeleteModalOpen(false);
    };

    const deleteStream = async () => {
        try {
            await axios.delete(`/peoplecounting/streamDelete/${image.image.id}/${image.places[image.indexplace]?.id}`);
            if (image.places[image.indexplace]?.id) {
                const res = await axios.get(`/peoplecounting/streamCounting/${image.places[image.indexplace]?.id}`);
                stream.load(res.data)
            } else {
                stream.load([])
            }
            closeDeleteModal();
        } catch (error) {
            console.error("Error deleting stream:", error);
        }
    };

    return (
        <>
            <Card isFooterBlurred className="w-full sm:w-[17.5rem] group h-64">
                <CardHeader className="hidden group-hover:flex absolute z-10 top-1 justify-end">
                    <Button
                        variant="light"
                        color="danger"
                        onClick={openDeleteModal}
                        className="text-primary-foreground hover:text-danger-200"
                        isIconOnly
                    >
                        <RiDeleteBin6Fill className="w-4 h-4" />
                    </Button>
                </CardHeader>
                <img
                    alt="NextUI hero Image"
                    // src={stream.thumbnailUrl}
                    src={`${import.meta.env.VITE_APP_BACKEND}${image.image.thumbnail}`}
                    className="z-0 w-full h-full object-cover object-center"
                />
                <CardFooter className="absolute bg-black/40 bottom-0 z-10 border-t-1 border-default-600 dark:border-default-100">
                    <div className="flex flex-grow gap-2 items-center">
                        <div className="flex flex-col">
                            <p className="text-tiny text-white/60">
                                Camera {image.image.title}
                            </p>
                        </div>
                    </div>
                    <Button
                        radius="sm"
                        size="sm"
                        className="bg-[#23A653]"
                        onClick={() => navigate(`/people-counting/${image.image.id}`)}
                    >
                        See Stream
                    </Button>
                </CardFooter>
            </Card>
            <Modal isOpen={isDeleteModalOpen} onClose={closeDeleteModal}> isDismissable={false} isKeyboardDismissDisabled={true}
                <ModalContent>
                    <ModalHeader>Confirm Deletion</ModalHeader>
                    <ModalBody>
                        Are you sure you want to delete this camera stream?
                    </ModalBody>
                    <ModalFooter>
                        <Button color="default" onClick={closeDeleteModal}>
                            Cancel
                        </Button>
                        <Button color="danger" onClick={deleteStream}>
                            Delete
                        </Button>
                    </ModalFooter>
                </ModalContent>
            </Modal>
        </>
    );
}
