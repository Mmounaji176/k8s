import { Autocomplete, AutocompleteItem, Avatar } from "@nextui-org/react";
import { useDetectionStore } from "../../../store/detection";
import { useRef, useState } from "react";
import { useDebounce } from "../../../hooks/useDebounce";
import useAxios from "../../../services/axios";
export const SearchInput = () => {
  const userStore = useDetectionStore();
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
    userStore.selectedUser(event.target.value);
  };
  const checker = (value : string) => {
    if (value === "" || !value)
        userStore.selectedUser(null)
  }
  return (
    <Autocomplete
      defaultItems={users}
      onKeyDown={() => (loading.current = true)}
      isLoading={loading.current}
      variant="bordered"
      placeholder="Search..."
      aria-label="Search"
      labelPlacement="inside"
      className="max-w-xs"
      menuTrigger="input"
      allowsCustomValue={true}
      onInputChange={useDebounce(valueChange)}
    //   onClear={()=>{console.log("clicked")}}
      isClearable={false}
      onValueChange={checker}
    >
      {(users) => (
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
