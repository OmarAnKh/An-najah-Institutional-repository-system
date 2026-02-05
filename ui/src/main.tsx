import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

// Clear localStorage on dev start for fresh state
if (import.meta.env.DEV) {
  localStorage.removeItem('ir-chat-conversations');
  localStorage.removeItem('ir-active-conversation');
}

createRoot(document.getElementById("root")!).render(<App />);
