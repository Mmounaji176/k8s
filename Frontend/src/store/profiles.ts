import {create} from 'zustand'



type STORE = {
  profiles : any[]
}
type ACTION = {
    setProfiles : (data:any) => void,   
}
export const useProfilesStore = create<STORE & ACTION>( (set) => ({
    profiles:[],
    setProfiles : (data) => set(({profiles:data})),

}))