import { BrowserRouter } from "react-router-dom";
import AppRoutes from "./routes";
import AppToaster from "@/shared/components/AppToaster";
import { ConfirmProvider } from "@/shared/hooks/useConfirm";

export default function App() {
  return (
    <BrowserRouter>
      <ConfirmProvider>
        <AppRoutes />
        <AppToaster />
      </ConfirmProvider>
    </BrowserRouter>
  );
}
