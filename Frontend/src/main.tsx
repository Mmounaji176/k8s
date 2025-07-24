import ReactDOM from "react-dom/client";
import { Providers } from "./providers";
import { Routers } from "./routes";
import "./styles/index.css";
import { Toaster } from 'react-hot-toast';

// Initialize WebRTC adapter
ReactDOM.createRoot(document.getElementById("root")!).render(
  // <React.StrictMode>
  <Providers themeProps={{ attribute: "class", defaultTheme: "dark" }}>
    <Toaster
      position="top-center"
      reverseOrder={false}
      toastOptions={{ className: `bg-[#333] dark:bg-background/80 dark:text-white rounded-lg` }}


    />
    <Routers />
  </Providers>
  //  </React.StrictMode>
);
