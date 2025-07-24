import { create } from 'zustand';

// Helper function to get current date components
const getCurrentDateComponents = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    
    return { year, month, day, hours, minutes };
};

type STORE = {
    start_date_time: string;
    end_date_time: string;
    person_id: number | null;
    place_ids: string[];
    places: string[];
    selectedKeys: string[];
    selectedPlaces: string;
    filter_range: string;
    pagestore: number;
    global_count: number;
    global_extra_detetections:object[];
};

type ACTION = {
    setStartDate: (data: string) => void;
    setEndDate: (data: string) => void;
    setPersonId: (data: number) => void;
    setPlaceIds: (data: string[]) => void;
    setPlaces: (data: string[]) => void;
    setSelectedKeys: (data: string[]) => void;
    setSelectedPlaces: (data: string) => void;
    setFilterRange: (data: string) => void;
    setPageStore: (data: number) => void;
    initializeDates: (start?: string, end?: string) => void;
    setGlobalCount: (data: number) => void;
    setGlobalExtraDetections:(data:object[]) => void;
};

export const useFilterStore = create<STORE & ACTION>((set) => {
    const { year, month, day, hours, minutes } = getCurrentDateComponents();
    
    // Initialize default dates in the exact format specified
    const defaultStartDate = `01-${month}-${year}-00-00`;
    const defaultEndDate = `${day}-${month}-${year}-${hours}-${minutes}`;
    
    return {
        // Initial state
        start_date_time: defaultStartDate,
        end_date_time: defaultEndDate,
        person_id: -1,
        place_ids: ["-1"],
        places: [],
        selectedKeys: [],
        selectedPlaces: "-1",
        filter_range: "known",
        pagestore: 1,
        global_count: 0,
        global_extra_detetections:[],
        // Actions
        setStartDate: (data) => set({ start_date_time: data }),
        setEndDate: (data) => set({ end_date_time: data }),
        setPersonId: (data) => set({ person_id: data }),
        setPlaceIds: (data) => set({ place_ids: data }),
        setPlaces: (data) => set({ places: data }),
        setSelectedKeys: (data) => set({ selectedKeys: data }),
        setSelectedPlaces: (data) => set({ selectedPlaces: data }),
        setFilterRange: (data) => set({ filter_range: data }),
        setPageStore: (data) => set({ pagestore: data }),
        setGlobalCount: (data) => set({ global_count: data }),
        setGlobalExtraDetections: (data) => set({global_extra_detetections:data}),
        // Initialize dates with the exact format used in the original code
        initializeDates: (start?: string, end?: string) => {
            if (start && end && start !== "1" && end !== "1") {
                set({
                    start_date_time: start,
                    end_date_time: end
                });
            } else {
                const { year, month, day, hours, minutes } = getCurrentDateComponents();
                set({
                    start_date_time: `01-${month}-${year}-00-00`,
                    end_date_time: `${day}-${month}-${year}-${hours}-${minutes}`
                });
            }
        }
    };
});