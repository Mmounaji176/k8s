import { Card, CardBody, CardHeader, Image } from "@nextui-org/react";
import { getColor } from "./DetectionModal";
import { useEffect, useState , useRef} from "react";
import { useDetectionStore } from "../../../../store/detection";
import useAxios from "../../../../services/axios";
import { useParams } from "react-router-dom";
export const getPersonIndex = (obj: any, id: number) => {
    for (let i = 0; i < obj.length; ++i) {
      if (id === obj[i].detection_persons[0].person.id) {
        return i;
      }
    }
    return 0;
  };
export const DetectedFaces = ({page:number}) => {
    const [detections, setDetections] = useState([]);
    const userStore = useDetectionStore();
    const axios = useAxios();
    let { id, str } = useParams();
    const imgRef = useRef<any>(null);
    useEffect(() => {
        (async () => {
          let res: any;
          if (userStore.user === null)
            res = await axios.get(
              `/api/stream_detections/${id}/${str}?page=${page}`
            );
          else
            res = await axios.get(
              `/api/stream_detections/${userStore.user}/${id}/${str}?page=${page}`
            );
          setDetections(res.data.results);
        })();
      }, [id, page, str, userStore.user]);
    return (
        <Card className="flex flex-col gap-4 bg-background/80 p-4">
        <CardHeader>
          <h1 className="text-3xl font-bold">Detected Faces</h1>
        </CardHeader>
        <CardBody>
          <div className="flex flex-wrap gap-4 overflow-auto scrollbar scrollbar-thumb-default-200 h-[20rem]">
            {detections?.map((item, index) => (
              <div
                key={index}
                onClick={() => {
                  imgRef.current.src = `${import.meta.env.VITE_APP_BACKEND
                    }${item.detection_frame}`;
                  socket.current.close();
                }}
              >
                <Card
                  key={index}
                  className="flex items-center w-[12.5rem] h-60 hover:bg-zinc-800"
                >
                  <Image
                    src={`${import.meta.env.VITE_APP_BACKEND}${item.detection_persons[
                        getPersonIndex(item, userStore.user)
                      ].person.images[0].image
                      }`}
                    radius="none"
                    className="w-[12.5rem] h-48 object-cover object-center"
                  />
                  <div className="flex w-full h-full justify-between  items-center gap-2 font-semibold">
                    <p className="mx-2">
                      {
                        item.detection_persons[
                          getPersonIndex(item, userStore.user)
                        ].person.name
                      }
                    </p>
                    <div className={`flex items-center py-1 px-2 mx-1 rounded-lg bg-${getColor((
                      100 -
                      item.detection_persons[
                        getPersonIndex(item, userStore.user)
                      ].conf_value *
                      100
                    ))}`}>

                      <p>
                        {(
                          100 -
                          item.detection_persons[
                            getPersonIndex(item, userStore.user)
                          ].conf_value *
                          100
                        ).toFixed(2)}
                        %
                      </p>
                    </div>
                  </div>
                </Card>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    )
}