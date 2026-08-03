import AssetForm from "./AssetForm";
import type { AssetSummary } from "@/shared/types/asset";

interface AssetCreateFormProps {
  projectId: string;
  parentAssets?: AssetSummary[];
  onCreated?: () => void;
}

export default function AssetCreateForm({ onCreated, ...props }: AssetCreateFormProps) {
  return <AssetForm mode="create" {...props} onSuccess={onCreated} />;
}
