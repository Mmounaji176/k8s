import {
  Avatar,
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/react";
import { useFilterStore } from "../store/filterstore";
import { Pagination } from "@nextui-org/react";
import { useEffect, useState } from "react";
import useAxios from "../../../services/axios";
import { useNavigate, useParams } from "react-router-dom";
import { convertDateTime } from "../../../services/dateconverter";
import { useProfilesStore } from "../../../store/profiles";
import { FilterRange } from "./FilterRange";
import { toast } from 'react-hot-toast'
import { UsersTable as DetailedUserTable } from './UsersTableDetailedExtra'
export const UsersTable = () => {
  const { page, id, start, end, zones, filter_range } = useParams()
  const filterStore = useFilterStore()
  const [count, setCount] = useState(0)
  const axios = useAxios()
  const profiles = useProfilesStore()
  const navigate = useNavigate()

  var places = filterStore.selectedKeys.join(",");
  const handleChange = async (page: any) => {

    if (filterStore.selectedKeys.length === 0) {
      places = "-1"
    }
    filterStore.setSelectedPlaces(places)

    try {
      var res;
      if (!filterStore.person_id) {
        navigate(`/face-recognition/overview/${page}/-1/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${filterStore.filter_range}`)
        filterStore.setPersonId(-1)
        res = await axios.get(`/overview/-1/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${filterStore.filter_range}/?page=${page}`)
        filterStore.setGlobalCount(Math.ceil(res.data.count / 20));

      }
      else {
        navigate(`/face-recognition/overview/${page}/${filterStore.person_id}/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${filterStore.filter_range}`)
        res = await axios.get(`/overview/${filterStore.person_id}/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${filterStore.filter_range}?page=${page}`)
        filterStore.setGlobalCount(Math.ceil(res.data.count / 20));


      }
      profiles.setProfiles(res.data.results)
    } catch (e) {
      console.log(e)
    }
  }
  useEffect(() => {
    // filterStore.setFilterRange(filter_range)
    // if 
    (async () => {
      // toast.success(`id ${id} start ${start} end ${end} places ${places}`);
      // toast.success(`${filterStore.selectedPlaces} ${filterStore.filter_range} ${filterStore.start_date_time} ${filterStore.end_date_time}`)

      if (id == "1" && start == "1" && end == "1") {
        // toast.success(`inside ${places}`)
        try {
          navigate(`/face-recognition/overview/1/-1/${filterStore.start_date_time}/${filterStore.end_date_time}/-1/${filterStore.filter_range}`)
          filterStore.setPersonId(-1)
          const res = await axios.get(`/overview/-1/${filterStore.start_date_time}/${filterStore.end_date_time}/-1/known?page=1`)
          profiles.setProfiles(res.data.results)
          setCount(Math.ceil(res.data.count / 20))
        } catch (e) {
          toast.error(`error is ${e}`)
        }
      }
      else {
        const res = await axios.get(`/overview/${id}/${start}/${end}/${zones}/${filter_range}?page=${page}`)
        profiles.setProfiles(res.data.results)
        filterStore.setGlobalCount(Math.ceil(res.data.count / 20))
      }


    })()
    return () => {
      profiles.setProfiles([])
      setCount(1)
    }

  },
    []
  )
  useEffect(() => {
    return () => {
      filterStore.setGlobalCount(1)
    }
  }, [])
  return (
    <>
      <div className="flex justify-between">
        <FilterRange />
      </div>
      {
        filter_range === "unknown" || id != -1 ? (
          <DetailedUserTable handleChange={handleChange} />
        ) :
          (
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
                  <TableColumn>Total Detections</TableColumn>
                  <TableColumn>Last Detection</TableColumn>
                  <TableColumn>Place</TableColumn>
                  <TableColumn>Camera</TableColumn>
                </TableHeader>
                <TableBody>
                  {profiles?.profiles?.map((item: any, index: number) => (
                    <TableRow key={index} onClick={() => navigate(`/face-recognition/detections/1/${item.id}/${filterStore.start_date_time}/${filterStore.end_date_time}/${filterStore.selectedPlaces}/${filterStore.filter_range}`)}>
                      <TableCell className="w-48">
                        {item?.images?.length > 0 ? (
                          <Avatar
                            radius="md"
                            size="lg"
                            src={`${import.meta.env.VITE_APP_BACKEND}${item?.images[0]?.image}`}
                          />
                        ) : (
                          <Avatar
                            radius="md"
                            size="lg"
                          />
                        )}
                      </TableCell>
                      <TableCell>{item.name}</TableCell>
                      <TableCell>{item.total_detections}</TableCell>
                      <TableCell>{item?.last_detection?.created ? (convertDateTime(item?.last_detection?.created)) : "No Detections yet"}</TableCell>
                      <TableCell>{item?.last_detection?.place}</TableCell>
                      <TableCell>{item?.last_detection?.camera}</TableCell>


                    </TableRow>
                  ))}
                </TableBody>
              </Table >
              <div className="flex items-center justify-center">
                <Pagination
                  showControls
                  color="primary"
                  total={filterStore.global_count}
                  initialPage={1}
                  onChange={(page) => toast.promise(handleChange(page), { loading: "Loading...", success: "Success!", error: "Error!" })}
                />
              </div>
            </>
          )
      }

    </>
  )
}