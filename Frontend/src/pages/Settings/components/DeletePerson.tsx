import { Button } from "@nextui-org/react"
import useAxios from "../../../services/axios"
import { IoPersonRemove } from "react-icons/io5"
import { useProfilesStore } from "../../../store/profiles"

export const DeletePerson = ({id,page}:any) => {
    const axios = useAxios()
    const profiles = useProfilesStore()

    const handleDelete = () => {   
        try{
            (async () => {
                await axios.delete(`api/profile/${id}`)
                const res = await axios.get(`/api/profile/?page=${page}`)
                profiles.setProfiles(res.data.results)
            })()
      
        }catch(e){
            console.log(e)
        }
    }
    return (
        <Button
                    radius="sm"
                    variant="ghost"
                    color="danger"
                    startContent={<IoPersonRemove className="text-lg" />}
                    className="hover:text-foreground"
                    onPress={handleDelete}
                  >
                    Delete
                  </Button>
    )
}