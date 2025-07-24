



import {
  Avatar,
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
  useDisclosure,
} from "@nextui-org/react";

import Slider from "react-slick";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";
import { Pagination } from "@nextui-org/react";
import { useEffect, useRef, useState } from "react";
import useAxios from "../../../../services/axios";
import { useParams, useNavigate } from "react-router-dom";
import { convertDateTime } from "../../../../services/dateconverter";

export const Detections = () => {
  const { _, id, start, end, zones } = useParams();
  const [page, setPage] = useState(1);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { isOpen: isOpen2, onOpen: onOpen2, onClose: onClos2 } = useDisclosure();
  // const { isOpen, onOpen, onClose } = useDisclosure();
  const [size, setSize] = useState("4xl");
  const [user, setUser] = useState(null);
  const [detections, setDetections] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [count, setCount] = useState(1);
  const axios = useAxios();
  const navigate = useNavigate();
  const refImages = useRef<HTMLImageElement>(null);
  const refImages2 = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (isOpen && refImages.current) {
      refImages.current.focus();
      refImages.current.click();
    }
  }, [isOpen]);
  useEffect(() => {
    if (isOpen2 && refImages2.current) {
      refImages2.current.focus();
      refImages2.current.click();
    }
  }, [isOpen2]);
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
  };

  const handleOpen = (item) => {
    setSelectedItem(item);
    setSize("4xl");
    onOpen();
  };
  const handleOpen2 = (item) => {
    setSelectedItem(item);
    setSize("4xl");
    onOpen2();
  };
  useEffect(() => {
    (async () => {
      const res = await axios.get(`api/profile/${id}`);
      setUser(res.data.results[0]);
    })();
  }, [id]);

  useEffect(() => {
    (async () => {
      const res = await axios.get(`/overview/detailed/${id}/01-09-2020-00-00/04-09-2044-17-38/-1/known?page=${page}`);

      setDetections(res.data.results);
      setCount(Math.ceil(res.data.count / 20));
    })();
  }, [page,id]);

  return (
    <>
      <div className="flex justify-between"></div>
      <Table
        removeWrapper
        selectionMode="single"
        aria-label="Collection Detection Table"
        isStriped
      >
        <TableHeader>
          <TableColumn>Picture</TableColumn>
          <TableColumn>Name</TableColumn>
          <TableColumn>Last Detection</TableColumn>
          <TableColumn>Frame</TableColumn>
          <TableColumn>Boxed Frame</TableColumn>
          <TableColumn>Place</TableColumn>
          <TableColumn>Camera</TableColumn>
        </TableHeader>
        <TableBody>
          {detections?.map((item, index) => (
            <TableRow>
              <TableCell onClick={() => handleOpen2(item)} className="w-48">
                <Avatar
                  radius="md"
                  size="lg"
                  src={`${import.meta.env.VITE_APP_BACKEND}${user?.images[0]?.image}`}
                />
              </TableCell>
              <TableCell key={index} onClick={() => handleOpen(item)}>{user?.name}</TableCell>
              <TableCell key={index} onClick={() => handleOpen(item)}>
                {item?.last_detection?.created
                  ? convertDateTime(item?.last_detection?.created)
                  : "No Detections yet"}
              </TableCell>
              <TableCell key={index} onClick={() => handleOpen(item)} className="max-w-56 min-w-28">
                <img
                  className="flex rounded w-68 object-fill"
                  src={`${import.meta.env.VITE_APP_BACKEND}${item?.last_detection?.detection_frame}`}
                />
              </TableCell>
              <TableCell key={index} onClick={() => handleOpen(item)} className="max-w-56 min-w-28">
                <img
                  className="flex rounded w-68 object-fill"
                  src={`${import.meta.env.VITE_APP_BACKEND}${item?.last_detection?.detection_frame_with_box}`}
                />
              </TableCell>
              <TableCell key={index} onClick={() => handleOpen(item)}>{item?.last_detection?.place}</TableCell>
              <TableCell key={index} onClick={() => handleOpen(item)}>{item?.last_detection?.camera}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Modal size={size} isOpen={isOpen} onClose={onClose} className="overflow-hidden">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1">images</ModalHeader>
              <ModalBody>
                <Slider className="flex" {...settings} w-full>
                  <div className="flex justify-items-center justify-center w-full">
                    <img
                      tabIndex={0}
                      ref={refImages}
                      className="w-full object-cover object-center"
                      src={`${import.meta.env.VITE_APP_BACKEND}${selectedItem?.last_detection?.detection_frame}`}
                    />
                  </div>
                  <div>
                    <img
                      className="w-full object-cover object-center"
                      src={`${import.meta.env.VITE_APP_BACKEND}${selectedItem?.last_detection?.detection_frame_with_box}`}
                    />
                  </div>
                  {
                    user?.images?.map((person: any, index: number) => (
                      <div className="!flex justify-center items-center h-full w-full" key={index}>
                        <img
                          className="  object-cover object-center"
                          src={`${import.meta.env.VITE_APP_BACKEND}${person.image}`}
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
      <Modal size={size} isOpen={isOpen2} onClose={onClos2} className="overflow-hidden">
        <ModalContent>
          {(onClose2) => (
            <>
              <ModalHeader className="flex flex-col gap-1">images</ModalHeader>
              <ModalBody>
                <Slider className="flex" {...settings} w-full>
                  {
                    user?.images?.map((person: any, index: number) => (
                      <div className="!flex justify-center items-center h-full w-full" key={index}>
                        <img tabIndex={0} ref={refImages2}
                          className="  object-cover object-center"
                          src={`${import.meta.env.VITE_APP_BACKEND}${person.image}`}
                        />
                      </div>
                    ))
                  }
                  <div className="flex justify-items-center justify-center w-full">
                    <img
                      tabIndex={0}
                      ref={refImages}
                      className="w-full object-cover object-center"
                      src={`${import.meta.env.VITE_APP_BACKEND}${selectedItem?.last_detection?.detection_frame}`}
                    />
                  </div>
                  <div>
                    <img
                      className="w-full object-cover object-center"
                      src={`${import.meta.env.VITE_APP_BACKEND}${selectedItem?.last_detection?.detection_frame_with_box}`}
                    />
                  </div>
                </Slider>
              </ModalBody>
              <ModalFooter>
                <Button color="danger" variant="light" onPress={onClose2}>
                  Close
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
      <div className="flex item-center justify-center">
        <Pagination
          showControls
          color={"secondary"}
          total={count}
          initialPage={1}
          onChange={(page) => setPage(page)}
        />
      </div>
    </>
  );
};
