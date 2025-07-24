import { create } from "zustand";

interface PeopleCountingState {
  streamTypes: Array<"line" | "zone">;
}

interface PeopleCountingActions {
  setStreamType: (index: number, type: "line" | "zone") => void;
}

export const usePeopleCountingStore = create<
  PeopleCountingState & PeopleCountingActions
>((set) => ({
  streamTypes: ["line", "zone", "zone", "line", "zone"],

  setStreamType: (index, type) =>
    set((state) => {
      const updatedStreamTypes = [...state.streamTypes];
      updatedStreamTypes[index] = type;
      return { streamTypes: updatedStreamTypes };
    }),
}));
