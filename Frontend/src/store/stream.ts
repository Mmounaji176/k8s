import { create } from "zustand";
import { STREAM_TYPE } from "../src/types";

type STORE = {
  streams: STREAM_TYPE[];
  places: string[];
  models: string[];
  model: string;
  cuda_device: number,
};
type ACTION = {
  load: (data: STREAM_TYPE[]) => void;
  setPlaces: (data: any) => void;
  setModel: (data: any) => void;
  setCudaDevice: (data: any) => void;
  
};
export const useStreamStore = create<STORE & ACTION>((set) => ({
  streams: [],
  places: [],
  models: [{ name: "people" }, { name: "cars" }],
  model : "",
  cuda_device: 0,
  async load(streams) {
    set({ streams: streams });
  },
  setPlaces(data) {
    set({ places: data });
  },
  setModel(data) {
    set({ model: data });
  },
  setCudaDevice(data){
    set({model: data});
  }
}));
