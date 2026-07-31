"""Assets feature tests — expand as the module grows."""

def test_assets_module_imports() -> None:
    from app.assets.models import Asset, AssetStatus, AssetType
    from app.assets.services import asset_service

    assert Asset.__tablename__ == "assets"
    assert AssetType.HOST.value == "host"
    assert AssetStatus.ACTIVE.value == "active"
    assert callable(asset_service.list_project_assets)
