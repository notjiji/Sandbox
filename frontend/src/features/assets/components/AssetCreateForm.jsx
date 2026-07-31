import AssetForm from "./AssetForm";

export default function AssetCreateForm(props) {
  return <AssetForm mode="create" {...props} onSuccess={props.onCreated} />;
}
