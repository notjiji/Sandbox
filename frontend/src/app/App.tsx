import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AppRoutes from "./routes";
import AppToaster from "@/shared/components/AppToaster";
import { ConfirmProvider } from "@/shared/hooks/useConfirm";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: true,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ConfirmProvider>
          <AppRoutes />
          <AppToaster />
        </ConfirmProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
