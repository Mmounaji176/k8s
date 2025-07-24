import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
  useDisclosure,
  Image,
} from "@nextui-org/react";
import { useEffect, useRef, useState } from "react";
import Slider from "react-slick";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";
import useAxios from "../../../../services/axios";
export const ImagesModal = ({ users }: any) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [size, setSize] = useState("4xl");
  const refImages = useRef<HTMLImageElement>(null);
  const axios = useAxios();
  const handleOpen = (size: string) => {
    setSize(size);
    onOpen();
  
  };
  useEffect(() => {
    if (isOpen && refImages.current) {
      refImages.current.focus();
      refImages.current.click();
    }
  }, [isOpen]);

  const settings = {
    dots: false,
    infinite: true,
    speed: 500,
    slidesToShow: 1,
    slidesToScroll: 1,
    fade: true,
    arrows: true,
    centerMode: true,
    centerPadding: "0px",
    className:"flex"
  };
  return (
    <div className="overflow-hidden flex flex-wrap">
      <div className="flex gap-4" onClick={() => handleOpen(size)}>
        <Image
          src={`${import.meta.env.VITE_APP_BACKEND}${users.detection_frame}`}
          radius="lg"
          className="w-full h-52 object-cover object-center"
        />
        <Image
          src={`${import.meta.env.VITE_APP_BACKEND}${
            users.detection_frame_with_box
          }`}
          radius="lg"
          className="w-full h-52 object-cover object-center"
        />
      </div>
      <Modal size={size} isOpen={isOpen} onClose={onClose} className="overflow-hidden">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1">images</ModalHeader>
              <ModalBody className="flex">
                <Slider className="flex" {...settings} w-full>
                  <div className="flex justify-items-center justify-center w-full">
                    <img ref={refImages}  tabIndex={0}
                      className="w-full  object-cover object-center"
                      src={`${import.meta.env.VITE_APP_BACKEND}${users.detection_frame}`}
                    />
                  </div>
                  <div>
                    <img 
                      className="w-full  object-cover object-center"
                      src={`${import.meta.env.VITE_APP_BACKEND}${
                        users.detection_frame_with_box
                      }`}
                    />
                  </div>
                  {
                    users?.detection_persons?.map((person: any,index:number) => (
                      <div className="!flex justify-center items-center h-full w-full" key={index} >
                        <img 
                          className="  object-cover object-center"
                          src={`${import.meta.env.VITE_APP_BACKEND}${person.person.images[0].image}`}
                        />
                      </div>
                    ))
                  }
                </Slider>
              </ModalBody>
              <ModalFooter>
                <Button color="danger" variant="light" onPress={onClose}>
                  Close
                </Button>
               
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </div>
  );
};
