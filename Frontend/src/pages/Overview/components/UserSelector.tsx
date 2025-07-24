import { Autocomplete, AutocompleteItem, Avatar } from "@nextui-org/react";
import { useFilterStore } from "../store/filterstore";
import { useEffect, useRef, useState } from "react";
import { useDebounce } from "../../../hooks/useDebounce";
import { useParams } from "react-router-dom";
import useAxios from "../../../services/axios";
export const UserSelector = ({className}) => {
  
  const filterStore = useFilterStore()
  const [users, setUsers] = useState([]);
  const loading = useRef<boolean>();
  loading.current = false;
  const axios = useAxios();
  const valueChange = async (str: string) => {
    const res = await axios.get(`api/profile/${str}`);
    setUsers(res.data.results);
    loading.current = false;
  };
  const handleChange = (event: any) => {
    filterStore.setPersonId(event.target.value);
    console.log(event.target.value)
  };
  const checker = (value : string) => {
    if (value === "" || !value)
        filterStore.setPersonId(null)
      console.log("cleared")
  }
  useEffect(() => {
    return () => {
      filterStore.setPersonId(null)
    }
  }, [])
  return (
    <Autocomplete
      defaultItems={users}
      onKeyDown={() => (loading.current = true)}
      isLoading={loading.current}
      variant="bordered"
      placeholder="Search..."
      aria-label="Search"
      labelPlacement="inside"
      className={`max-w-xs ${className}`}
      menuTrigger="input"
      allowsCustomValue={true}
      onInputChange={useDebounce(valueChange)}
      onClear={()=>{console.log("clicked")}}
      isClearable={false}
      onValueChange={checker}
    >
      {(users:any) => (
        <AutocompleteItem
          value={users.id}
          key={users.id}
          textValue={users.name}
          onPress={handleChange}
          
        >
          <div className="flex gap-2 items-center">
            <Avatar
              alt={users.name}
              className="flex-shrink-0"
              size="sm"
              src={`${import.meta.env.VITE_APP_BACKEND}${
                users.images[0].image
              }`}
            />
            <div className="flex flex-col">
              <span className="text-small">{users.name}</span>
            </div>
          </div>
        </AutocompleteItem>
      )}
    </Autocomplete>
  );
};
