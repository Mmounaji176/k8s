import { Tabs, Tab } from "@nextui-org/react";
import { useState, useEffect, useRef } from "react";
import { useFilterStore } from "../store/filterstore";
import useAxios from "../../../services/axios";
import { useProfilesStore } from "../../../store/profiles";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from 'react-hot-toast';

export function FilterRange() {
    const { filter_range , id} = useParams()

    const [str, setStr] = useState(filter_range ? filter_range : "known");
    const [isLoading, setIsLoading] = useState(false);
    const filterStore = useFilterStore();
    const profileStore = useProfilesStore();
    const axios = useAxios();
    const navigate = useNavigate();
    const controllerRef = useRef(null);
    const loadingToastIdRef = useRef(null);

    // Cancel any ongoing request when component unmounts
    useEffect(() => {
        return () => {
            if (controllerRef.current) {
                controllerRef.current.abort();
            }
            if (loadingToastIdRef.current) {
                toast.dismiss(loadingToastIdRef.current);
            }

        };

    }, []);

    const handleTabChange = async (newStr) => {
        // If there's a loading toast, dismiss it
        profileStore.setProfiles([])
        filterStore.setGlobalCount(1)
        if (loadingToastIdRef.current) {
            toast.dismiss(loadingToastIdRef.current);
        }

        // If there's an ongoing request, cancel it
        if (controllerRef.current) {
            controllerRef.current.abort();
        }

        // Create new AbortController
        controllerRef.current = new AbortController();

        // Show loading toast and store its ID
        loadingToastIdRef.current = toast.loading("Loading...");

        try {
            setIsLoading(true);
            var places = filterStore.selectedKeys.join(",");


            if (filterStore.selectedKeys.length === 0) {
                places = "-1"
            }
            let url;
            let res;
            if ( !filterStore.person_id || filterStore.person_id == "-1" || id == "-1") {
                url = `/overview/-1/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${newStr}?page=1`;
                navigate(`/face-recognition/overview/1/-1/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${newStr}`);
                filterStore.setPersonId(-1);
                res = await axios.get(url, {
                    signal: controllerRef.current.signal
                });
                profileStore.setProfiles(res.data.results);

            } else {                
                url = `/overview/detailed_extra/${filterStore.person_id}/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${newStr}?page=1`;
                navigate(`/face-recognition/overview/1/${filterStore.person_id}/${filterStore.start_date_time}/${filterStore.end_date_time}/${places}/${newStr}`);
                res = await axios.get(url, {
                    signal: controllerRef.current.signal
                });
                filterStore.setGlobalExtraDetections(res.data.results)

            }

           
            filterStore.setGlobalCount(Math.ceil(res.data.count / 20))
            setStr(newStr);
            filterStore.setFilterRange(newStr);

            // Success toast
            toast.success("Success!", {
                id: loadingToastIdRef.current
            });

        } catch (error) {
            if (error.name === 'CanceledError' || error.name === 'AbortError') {
                // Request was cancelled, dismiss the loading toast silently
                toast.dismiss(loadingToastIdRef.current);
            } else {
                // Show error toast
                toast.error("Error occurred!", {
                    id: loadingToastIdRef.current
                });
                console.error("Error fetching data:", error);
            }
        } finally {
            setIsLoading(false);
            loadingToastIdRef.current = null;
        }
    };

    return (
        <Tabs
            className="flex flex-col gap-4 mb-4"
            aria-label="Options"
            color="primary"
            selectedKey={str}
            onSelectionChange={handleTabChange}
            isDisabled={isLoading}
        >
            <Tab
                key="known"
                className="text-white text-bold"
                title="Known"
            />
            <Tab
                key="high"
                className="text-white text-bold"
                title="High"
            />
            <Tab
                key="unknown"
                className="text-white text-bold"
                title="Unknowns"
            />
        </Tabs>
    );
}