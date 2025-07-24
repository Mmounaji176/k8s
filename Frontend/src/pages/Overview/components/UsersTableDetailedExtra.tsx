import { Avatar, Table, TableBody, TableCell, TableColumn, TableHeader, TableRow, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Button, useDisclosure } from "@nextui-org/react";
import { ImagesModal } from "./ImagesModalUnkowns";
import Slider from "react-slick";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";
import { Pagination } from "@nextui-org/react";
import { useEffect, useRef, useState } from "react";
import useAxios from "../../../services/axios";
import { useParams, useNavigate } from "react-router-dom";
import { convertDateTime } from "../../../services/dateconverter";
import { toast } from 'react-hot-toast';
import { useFilterStore } from "../store/filterstore";
import { useProfilesStore } from "../../../store/profiles";
export function UsersTable() {
  const { page, id, start, end, zones, filter_range } = useParams();
  const filterStore = useFilterStore()
  const profileStore = useProfilesStore()
  const navigate = useNavigate()
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [size, setSize] = useState("4xl");
  const [user, setUser] = useState(null);
  // const [detections, setDetections] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [count, setCount] = useState(1);
  const axios = useAxios();
  const refImages = useRef(null);
  const modalRefs = useRef({});

  useEffect(() => {
    if (isOpen && refImages.current) {
      refImages.current.focus();
      refImages.current.click();
    }
  }, [isOpen]);
  const handlePagination = async (page_param: string) => {
    filterStore.setGlobalExtraDetections([])
    navigate(`/face-recognition/overview/${page_param}/${id}/${start}/${end}/${zones}/${filter_range}`)
    const res = await axios.get(`/overview/detailed_extra/${id}/${start}/${end}/${zones}/${filter_range}?page=${page_param}`);
    filterStore.setGlobalExtraDetections(res.data.results);
    filterStore.setGlobalCount(Math.ceil(res.data.count / 20));
  }
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

  const handleAvatarCellClick = (itemId) => {
    if (modalRefs.current[itemId]) {
      modalRefs.current[itemId].openModal();
    }
  };

  useEffect(() => {
    (async () => {
      const res = await axios.get(`api/profile/${id}`);
      setUser(res.data.results[0]);
    })();
  }, [id]);

  useEffect(() => {
    (async () => {
      var res;
      try {
        if (start != "1" && end != "-1")
          res = await axios.get(`/overview/detailed_extra/${id}/${start}/${end}/${zones}/${filter_range}?page=${page}`);
        else
          throw "error"
      } catch (e) {
        if (page != "1")
          navigate(`/face-recognition/overview/1/${id}/${start}/${end}/${zones}/${filter_range}`)
        // res = await axios.get(`/overview/detailed_extra/${id}/${start}/${end}/${zones}/${filter_range}?page=1`);

      }
      filterStore.setGlobalExtraDetections(res.data.results);
      setCount(Math.ceil(res.data.count / 20));
      filterStore.setGlobalCount(Math.ceil(res.data.count / 20));

    })();
    return () => { filterStore.setGlobalExtraDetections([]); setCount(1); filterStore.setGlobalCount(1) };
  }, [id]);

  return (
    <>
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
          <TableColumn>Most Likely People</TableColumn>
          <TableColumn>Analytics</TableColumn>
          <TableColumn>Place</TableColumn>
          <TableColumn>Camera</TableColumn>
        </TableHeader>
        <TableBody>
          {filterStore?.global_extra_detetections?.map((item, index) => (
            <TableRow key={index}>
              <TableCell onClick={() => handleOpen(item)} className="max-w-56 min-w-28">
                <img
                  className="flex rounded w-68 object-fill"
                  src={`${import.meta.env.VITE_APP_BACKEND}${item?.detection_frame_with_box}`}
                />
              </TableCell>
              <TableCell onClick={() => handleOpen(item)}>
                {item?.detection_persons[0]?.person?.name}
              </TableCell>
              <TableCell onClick={() => handleOpen(item)}>
                {item?.created ? convertDateTime(item?.created) : "No Detections yet"}
              </TableCell>
              <TableCell className="w-48">
                <div
                  className="flex flex-col gap-2 cursor-pointer"
                  onClick={() => handleAvatarCellClick(`modal-${item.id}`)}
                >
                  <div className="flex flex-row gap-1 item-center justify-center justify-items-center">
                    {item?.detection_persons?.slice(0, 3).map((person, index) => (
                      <Avatar
                        key={index}
                        radius="md"
                        size="lg"
                        src={`${import.meta.env.VITE_APP_BACKEND}${person?.person?.images[0]?.image}`}
                      />
                    ))}
                  </div>
                  <div className="text-sm text-primary">
                    View all matches ({item?.detection_persons?.length})
                  </div>
                </div>
                <ImagesModal
                  users={item?.detection_persons}
                  ref={el => (modalRefs.current[`modal-${item.id}`] = el)}
                />
              </TableCell>
              <TableCell>
              {!item.json_result?.results?.[0] && item?.deep_face_processed && (
                  <div className="flex flex-col space-y-1 justify-center items-center">
                    Could not analyze face
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
              <TableCell onClick={() => handleOpen(item)}>
                {item?.detection_persons[0]?.camera || "Unknown"}
              </TableCell>
              <TableCell onClick={() => handleOpen(item)}>
                {item?.detection_persons[0]?.place || "Unknown"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {/* Main modal for detection details */}
      <Modal size={size} isOpen={isOpen} onClose={onClose} className="overflow-hidden">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1">Detection Details</ModalHeader>
              <ModalBody>
                <Slider className="flex" {...settings} w-full>
                  <div className="flex justify-items-center justify-center w-full">
                    <img
                      tabIndex={0}
                      ref={refImages}
                      className="w-full object-cover object-center"
                      src={`${import.meta.env.VITE_APP_BACKEND}${selectedItem?.detection_frame}`}
                    />
                  </div>
                  <div>
                    <img
                      className="w-full object-cover object-center"
                      src={`${import.meta.env.VITE_APP_BACKEND}${selectedItem?.detection_frame_with_box}`}
                    />
                  </div>
                  {selectedItem?.detection_persons?.map((detection, index) => (
                    detection.person?.images?.map((image, imageIndex) => (
                      <div className="!flex justify-center items-center h-full w-full" key={`${index}-${imageIndex}`}>
                        <img
                          className="object-cover object-center"
                          src={`${import.meta.env.VITE_APP_BACKEND}${image.image}`}
                        />
                      </div>
                    ))
                  ))}
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

      <div className="flex items-center justify-center mt-4">
        <Pagination
          showControls
          color="primary"
          total={filterStore.global_count}
          initialPage={1}
          onChange={(page) =>
            toast.promise(handlePagination(page), {
              loading: "Loading...",
              success: "Success!",
              error: "Error!"
            })
          }
        />
      </div>
    </>
  );
}