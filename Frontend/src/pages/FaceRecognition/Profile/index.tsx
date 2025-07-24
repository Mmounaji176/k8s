import { Detections } from "./components/Detections";
import { ProfileHeader } from "./components/ProfileHeader";
import useAxios from "../../../services/axios";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
export function ProfilePage() {
  const axios = useAxios();
  const { id } = useParams();
  const [profile, setProfile] = useState(null);
  useEffect(() => {
    (async () => {
      const res = await axios.get(`api/profileDetections/${id}`);
      setProfile(res.data);
    })();
  }, [id]);
  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-4xl font-bold">Profile</h1>
      {profile && <ProfileHeader profile={profile} id={id} />}
      <Detections id={id} profile={profile} />
    </div>
  );
}
