import {
  Avatar,
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/react";
import { useFilterStore } from "../../Overview/store/filterstore";
import { Pagination } from "@nextui-org/react";
import { useEffect, useState } from "react";
import useAxios from "../../../services/axios";
import { useNavigate, useParams } from "react-router-dom";
// import { convertDateTime } from "../../../services/dateconverter";
import { useProfilesStore } from "../../../store/profiles";
// import { FilterRange } from "./FilterRange";
export const UserTable = () => {
  const {index, id, filter_type, page } = useParams()
  const filterStore = useFilterStore()
  const [count, setCount] = useState(0)
  const axios = useAxios()
  const profiles = useProfilesStore()
  const navigate = useNavigate()



  useEffect(() => {
    // filterStore.setFilterRange(filter_range)
    (async () => {

      const res = await axios.get(`/api/presentPersons/${id}?page=${page}`)
      profiles.setProfiles(res.data.results)
      setCount(Math.ceil(res.data.count / 20))


    })()
    return () => {
      profiles.setProfiles([])
    }

  },
    [page, id]
  )

  return (
    <>
      <div className="flex justify-between">
        {/* <FilterRange /> */}
      </div>
      <Table
        removeWrapper
        selectionMode="single"
        aria-label="Collection Detection Table"
        isStriped
        isLoading={profiles.profiles.length == 0}
      >
        <TableHeader>
          <TableColumn>Picture</TableColumn>
          <TableColumn>Name</TableColumn>
          <TableColumn>Presence</TableColumn>

        </TableHeader>
        <TableBody>
          {profiles?.profiles?.map((item: any, index: number) => (
            <TableRow key={index} onClick={() => navigate(`/face-recognition/detections/${page}/${item.id}/${filterStore.start_date_time}/${filterStore.end_date_time}/${filterStore.selectedPlaces}/${filterStore.filter_range}`)}>
              <TableCell className="w-48">
                <Avatar
                  radius="md"
                  size="lg"
                  src={`${import.meta.env.VITE_APP_BACKEND}${item.images[0].image}`}
                />
              </TableCell>
              <TableCell>{item.name}</TableCell>
              <TableCell className={`${item.total_detections > 0 ? "text-green-500" : "text-red-500"}`}>{item.total_detections > 0 ? "Present" : "Absent"}</TableCell>



            </TableRow>
          ))}
        </TableBody>
      </Table>
      <div className="flex items-center justify-center">
        <Pagination
          showControls
          color="primary"
          total={count}
          initialPage={1}
          onChange={(page) => console.log(page)}
        />
      </div>
    </>
  )
}