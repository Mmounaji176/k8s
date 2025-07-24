import { Tabs, Tab } from "@nextui-org/react";
import { useState, useEffect } from "react";
import useAxios from "../../../services/axios";
import { useNavigate , useParams } from "react-router-dom";
export const FilterRange = () => {
    const [str, setStr] = useState("known");
    const filterStore = useFilterStore();
    const axios = useAxios()
    const navigate = useNavigate()
    const { id , filter_type } = useParams()
    const toggle = (event: any) => {
        setStr(event);
        filterStore.setFilterRange(event);
        const f = async () => {
            try {
                var res;
                const places = filterStore.place_ids.join(",")
                if (!filterStore.person_id) {
                    // navigate(`/face-recognition/overview/1/-1/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${event}`)
                    // filterStore.setPersonId(-1)
                    // res = await axios.get(`/overview/-1/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${event}?page=1`)
                }
                else {
                    // navigate(`/face-recognition/overview/1/${filterStore.person_id}/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${event}`)
                    // res = await axios.get(`/overview/${filterStore.person_id}/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${event}?page=1`)
                }
            } catch (e) {
                console.log(e)
            }
        }
        f()
    };


    return (
        <Tabs
            className="flex flex-col gap-4 mb-4"
            aria-label="Options"
            color="primary"
            selectedKey={str}
            onSelectionChange={toggle}
        >
            <Tab

                key="Present"
                className="text-white text-bold"
                title="Present"
            />
            <Tab
                key="Absent"
                className="text-white text-bold "
                title="Absent"
            />
           
        </Tabs>
    );
};