import { Card, CardBody, CardHeader, Image } from "@nextui-org/react";
import useAxios from "../../../../services/axios";
import { useState, useEffect } from "react";
import { convertDateTime } from "../../../../services/dateconverter";
import { EditProfileModal } from "./EditProfile";

export function ProfileHeader(obj: any) {
  const axios = useAxios();
  const [count, setCount] = useState(0);
  const { profile, id } = obj;
  const [info, setInfo] = useState(null)
  const [detection, setDetections] = useState(null)
  useEffect(() => {
    (async () => {
      const res = await axios.get(`/api/detectionsProfile/${id}`);
      setCount(res.data.count);
      setDetections(res.data.results[0]);
      const res2 = await axios.get(`/overview/detailed/${id}/01-09-2020-00-00/04-09-2044-17-38/-1/known?page=${1}`)
      setInfo(res2.data.results[0].last_detection)

    })();
  }, []);

  return (
    <Card className="p-2 bg-background/80">
      <CardHeader className="flex justify-between">
        <h1 className="text-3xl font-bold">Profile Info</h1>
        <EditProfileModal user={profile} />
      </CardHeader>
      <CardBody className="flex flex-row w-full gap-4">
        <Image
          src={`${import.meta.env.VITE_APP_BACKEND}${profile?.images[0]?.image
            }`}
          className="w-72 h-72 object-cover object-center rounded-md"
        />
        <div className="flex flex-col gap-4">
          <h1>
            <span className="text-2xl text-primary font-bold">ID: </span>
            <span className="text-2xl">{profile?.name}</span>
          </h1>
          <h1>
            <span className="text-2xl text-primary font-bold">Name: </span>
            <span className="text-2xl">{profile?.name}</span>
          </h1>
          <h1>
            <span className="text-2xl text-primary font-bold">
              Total Detections:{" "}
            </span>
            <span className="text-2xl">{count}</span>
          </h1>
          <h1>
            <span className="text-2xl text-primary font-bold">
              Last Detection:{" "}
            </span>
            <span className="text-2xl">
              {detection && convertDateTime(detection?.created)}
            </span>
          </h1>
          <h1>
            <span className="text-2xl text-primary font-bold">
              Last Place:{" "}
            </span>
            <span className="text-2xl">
              {detection && detection?.detection?.video_source?.place_name}
            </span>
          </h1>
          {/* <h1>
            <span className="text-2xl text-primary font-bold">CIN: </span>
            <span className="text-2xl">
              {info && info.place}
            </span>
          </h1> */}
        </div>
      </CardBody>
    </Card>
  );
}
