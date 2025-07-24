import {Dropdown, DropdownTrigger, DropdownMenu, DropdownItem, Button} from "@nextui-org/react";
import { useState, useEffect } from "react";
import { useFilterStore } from "../store/filterstore";
import { useParams } from "react-router-dom";
import useAxios from "../../../services/axios";
export const PlacePicker = () => {
    const [selectedKeys, setSelectedKeys] = useState(new Set(["-1"]));
    const {zones} = useParams()
    const filterStore = useFilterStore()
    const axios = useAxios()
    useEffect(() => {
      (async () => {
        const res = await axios.get(`/api/zones/face`)
        // console.log(res.data)
        filterStore.setPlaces(res?.data?.map((item:any) => item.name))
        filterStore.setPlaceIds(res?.data?.map((item:any) => item.id))
      })()
      if (zones != "-1" && zones){
        setSelectedKeys(new Set(zones.split(",")))
      }
    }, [])

    
    const handleSelectChange = (value:any) => {
      console.log(value)
      if (value.anchorKey != "-1" && value.size > 1 && value.has("-1")) {
        value.delete("-1")
      }
      else if (value.anchorKey == "-1") {
        value.clear()
        value.add("-1")
      }

      setSelectedKeys(value)
      const places = Array.from(value).join(", ").replace(/_/g, " ").split(", ")
      filterStore.setSelectedKeys(places)
      console.log(places)
    }
    return (
      <Dropdown>
        <DropdownTrigger>
          <Button 
            variant="bordered" 
            className="capitalize"
          >
            Places
          </Button>
        </DropdownTrigger>
        <DropdownMenu 
          aria-label="Multiple selection dropdown menu"
          variant="flat"
          closeOnSelect={false}
          disallowEmptySelection
          selectionMode="multiple"
          selectedKeys={selectedKeys}
          onSelectionChange={handleSelectChange}
        >
          <DropdownItem key="-1">All Places</DropdownItem>
          {filterStore?.places?.map((item:string,index:number) => (
            <DropdownItem key={filterStore.place_ids[index]}>{item}</DropdownItem>
          ))}
        </DropdownMenu>
      </Dropdown>
    );
};
