import {create} from 'zustand'

type STORE = {
    user:any
  }
  type ACTION = {
    selectedUser : (data:any) => void,
  }

export const useDetectionStore = create<STORE & ACTION>( (set) => ({
    user : null,
    selectedUser(data) {
        set(({user:data}))
 }    
 }))