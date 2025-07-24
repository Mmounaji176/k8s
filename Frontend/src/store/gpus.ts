import {create} from 'zustand'

type GpuInfo = {
    gpu_id: number;
    pod: string;
    service: string;
    status: string;
    // Add other fields as needed from the registry
};

type STORE = {
    gpus: number;
    gpuList: GpuInfo[];
};

type ACTION = {
    setGpu: (data: number) => void;
    setGpuList: (list: GpuInfo[]) => void;
};

export const useGpuStore = create<STORE & ACTION>((set) => ({
    gpus: 4, // Default to 4 GPUs
    gpuList: [],
    setGpu(data) {
        set({gpus: data});
    },
    setGpuList(list) {
        set({gpuList: list});
    }
}));