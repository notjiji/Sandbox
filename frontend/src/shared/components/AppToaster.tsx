import { Toaster } from "sonner";

export default function AppToaster() {
  return (
    <Toaster
      position="top-right"
      closeButton
      toastOptions={{
        classNames: {
          toast:
            "glass-panel border-brand-700/50 bg-void-100/95 text-brand-100 shadow-crt backdrop-blur-md",
          title: "text-brand-100 font-medium",
          description: "text-brand-400",
          success: "border-emerald-500/30",
          error: "border-rose-500/30",
          closeButton: "text-brand-400 border-brand-700/50 bg-brand-950/50",
        },
      }}
    />
  );
}
