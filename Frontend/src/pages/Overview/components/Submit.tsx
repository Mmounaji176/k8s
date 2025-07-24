
import { Button } from "@nextui-org/react";
import { useState, useEffect } from "react";
import { useFilterStore } from "../store/filterstore";
import useAxios from "../../../services/axios";
import { useProfilesStore } from "../../../store/profiles";
import { useNavigate } from "react-router-dom";
import { toast } from 'react-hot-toast'

export const Submit = () => {
    const filterStore = useFilterStore();
    const profiles = useProfilesStore();
    const navigate = useNavigate();
    const axios = useAxios();
    const [loading, setLoading] = useState(false);

    const handleClick = async () => {
        var places = filterStore.selectedKeys.join(",");
        if (filterStore.selectedKeys.length === 0) {
            places = "-1"
        }
        // toast.success(`s ` ,filterStore.filter_range)
        filterStore.setSelectedPlaces(places)
        setLoading(true)
        try {
            var res;
            if (filterStore.filter_range === "unknown" && !filterStore.person_id) {
                navigate(`/face-recognition/overview/1/-1/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${filterStore.filter_range}`)
                filterStore.setPersonId(-1)
                res = await axios.get(`/overview/detailed_extra/-1/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${filterStore.filter_range}?page=1`);
                filterStore.setGlobalExtraDetections(res.data.results)
            }
            else if (filterStore.filter_range === "unknown") {
                navigate(`/face-recognition/overview/1/${filterStore.person_id}/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${filterStore.filter_range}`)
                res = await axios.get(`/overview/detailed_extra/${filterStore.person_id}/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${filterStore.filter_range}?page=1`)
                filterStore.setGlobalExtraDetections(res.data.results)
            }
            else if (!filterStore.person_id) {
                navigate(`/face-recognition/overview/1/-1/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${filterStore.filter_range}`)
                filterStore.setPersonId(-1)
                res = await axios.get(`/overview/-1/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${filterStore.filter_range}?page=1`)
                profiles.setProfiles(res.data.results)     
            }
            else {
                navigate(`/face-recognition/overview/1/${filterStore.person_id}/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${filterStore.filter_range}`)
                res = await axios.get(`/overview/${filterStore.person_id}/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${filterStore.filter_range}?page=1`)
                profiles.setProfiles(res.data.results)

            }
            filterStore.setGlobalCount(Math.ceil(res.data.count / 20))

        } catch (e) {
            console.log(e)
        }
        setLoading(false)

    }
    return (
        <>

            {!loading ?
                (<Button variant="ghost" color="primary" onClick={handleClick}>
                    Search
                </Button>)
                :
                (<Button variant="ghost" color="primary" isLoading>
                    Search
                </Button>)
            }

        </>
    )
}