// Create a new store for the WebSocket connection
import { create } from "zustand";

// WebSocket store
export const useWebSocketStore = create((set, get) => ({
  socket: null,
  message: "",
  isConnected: false,
  
  // Connect to WebSocket if not already connected
  connect: () => {
    const { socket } = get();
    if (!socket || socket.readyState === WebSocket.CLOSED) {
      const newSocket = new WebSocket(`ws://${import.meta.env.VITE_APP_SOCKET}/wsStat/`);
      
      newSocket.onopen = () => {
        set({ isConnected: true });
      };
      
      newSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        set({ message: data.message });
      };
      
      newSocket.onclose = () => {
        set({ isConnected: false });
      };
      
      set({ socket: newSocket });
    }
  },
  
  // Disconnect WebSocket
  disconnect: () => {
    const { socket } = get();
    if (socket) {
      socket.close();
      set({ socket: null, isConnected: false });
    }
  },
  
  setMessage: (message) => set({ message })
}));