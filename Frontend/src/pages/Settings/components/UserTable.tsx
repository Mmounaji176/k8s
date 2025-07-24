import {
  Avatar,
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/react";
import { EditProfileModal } from "../../FaceRecognition/Profile/components/EditProfile";
import { Pagination } from "@nextui-org/react";
import { useEffect, useState, useRef } from "react";
import useAxios from "../../../services/axios";
import { Link } from "react-router-dom";
import { convertDateTime } from "../../../services/dateconverter";
import { AddPerson } from "./AddPerson";
import { DeletePerson } from "./DeletePerson";
import { useProfilesStore } from "../../../store/profiles";
import { SearchInput } from "../../FaceRecognition/components/SearchProfilesInput";
import { useDetectionStore } from "../../../store/detection";
export const UsersTable = () => {
  const [page, setPage] = useState(1)
  const count = useRef(0)
  // const [ init , setInit] = useState(2)
  const axios = useAxios()
  const profiles = useProfilesStore()
  const selectedUser = useDetectionStore()
  useEffect(() => {
    (async () => {
      if (selectedUser.user) {
        const res = await axios.get(`/api/profile/${selectedUser.user}`)
        profiles.setProfiles(res.data.results)
        count.current = (Math.ceil(res.data.count / 20))
      }
      else {
        const res = await axios.get(`/api/profile/?page=${page}`)
        profiles.setProfiles(res.data.results)
        count.current = (Math.ceil(res.data.count / 20))
      }
      // setInit(1)
      console.log(selectedUser.user)
    })()

  },
    [page, selectedUser.user]
  )
  return (
    <>
      <div className="flex justify-between">
        <SearchInput />
        <div className="flex gap-4">
          <AddPerson />
        </div>
      </div>
      <Table
        removeWrapper
        selectionMode="single"
        aria-label="Collection Detection Table"
      >
        <TableHeader>
          <TableColumn>Picture</TableColumn>
          <TableColumn>Name</TableColumn>
          <TableColumn>Profile</TableColumn>
          <TableColumn>Total Detections</TableColumn>
          <TableColumn>Last Detection</TableColumn>
          <TableColumn className="w-8"> </TableColumn>
        </TableHeader>
        <TableBody>
          {profiles?.profiles?.map((item: any, index: number) => (
            <TableRow key={index}>
              <TableCell className="w-48">
                <Avatar
                  radius="md"
                  size="lg"
                  src={`${import.meta.env.VITE_APP_BACKEND}${item?.images[0]?.image}`}
                />
              </TableCell>
              <TableCell>{item.name}</TableCell>
              <TableCell><Link className="text-primary underline" to={`/face-recognition/profiles/${item.id}`}>See Profile</Link></TableCell>
              <TableCell>{item.total_detections}</TableCell>
              <TableCell>{item?.last_detection?.created ? (convertDateTime(item?.last_detection?.created)) : "No Detections yet"}</TableCell>
              <TableCell>
                <div className="flex gap-4">
                  <EditProfileModal user={item} />
                  <DeletePerson id={item.id} page={page} />
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <div className="flex items-center justify-center">
        <Pagination
          showControls
          color="primary"
          initialPage={1}
          total={count.current}
          onChange={(page) => setPage(page)}
        />
      </div>
    </>
  )
}