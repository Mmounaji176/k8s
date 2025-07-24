import create from 'zustand';
import { immer } from 'zustand/middleware/immer';



export const useLocalDetectionStore = create(immer((set,get) => ({
    detections: [],
    setDetections: (detections) => set(state => {
        state.detections = detections;
    }),
    updateDetectionPerson: (detectionId, personId, newValue) => set(state => {
        const detection = state.detections.find(item => item.id === detectionId);
        if (detection) {
            const person = detection.detection_persons.find(p => p.person.id === personId);
            if (person) {
                person.marked_person = newValue;
            }
        }
    }),
    getDetections: () => get().detections,

})));
