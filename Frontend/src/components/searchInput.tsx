import { Autocomplete, AutocompleteItem, Avatar } from "@nextui-org/react";

import { useRef, useState } from "react";
import { useDebounce } from "../hooks/useDebounce";
import useAxios from "../services/axios";
import { Link } from "react-router-dom";

export const SearchInput = (props:any) => {
  const {className} = props
  const [users, setUsers] = useState([]);
  const loading = useRef<boolean>();
  loading.current = false;
  const axios = useAxios();
  const valueChange = async (str: string) => {
    const res = await axios.get(`api/profile/${str}`);
    setUsers(res.data.results);
    loading.current = false;
  };

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
    >
      {(users) => (
        <AutocompleteItem key={users.id} textValue={users.name}>
          <Link to={`face-recognition/profiles/${users.id}`}>
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
          </Link>
        </AutocompleteItem>
      )}
    </Autocomplete>
  );
};
