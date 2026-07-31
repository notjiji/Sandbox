"""Assets feature tests — expand as the module grows."""


def test_assets_module_imports() -> None:
    from app.assets.enums import AssetStatus, AssetType, ROOT_ASSET_TYPES
    from app.assets.service import asset_service

    assert AssetType.WEBSITE.value == "website"
    assert AssetType.PUBLIC_IP.value == "public_ip"
    assert AssetType.WEBSITE in ROOT_ASSET_TYPES
    assert AssetStatus.ACTIVE.value == "active"
    assert callable(asset_service.list_for_project)
    assert callable(asset_service.get_scan_target)
    assert callable(asset_service.resolve_plugin_targets)


def test_asset_hierarchy_validation() -> None:
    from app.assets.enums import AssetType
    from app.assets.validators import validate_hierarchy, validate_parent_type
    from app.core.exceptions import ValidationAppError

    validate_hierarchy(AssetType.WEBSITE, None)
    validate_hierarchy(AssetType.CLOUD_ACCOUNT, None)
    validate_hierarchy(AssetType.PUBLIC_IP, "00000000-0000-4000-8000-000000000001")
    validate_hierarchy(AssetType.EMAIL_DOMAIN, "00000000-0000-4000-8000-000000000002")
    validate_hierarchy(AssetType.S3_BUCKET, "00000000-0000-4000-8000-000000000003")

    validate_parent_type(AssetType.PUBLIC_IP, AssetType.WEBSITE)
    validate_parent_type(AssetType.EMAIL_DOMAIN, AssetType.DOMAIN)
    validate_parent_type(AssetType.S3_BUCKET, AssetType.CLOUD_ACCOUNT)

    for child_type in (AssetType.PUBLIC_IP, AssetType.EMAIL_DOMAIN, AssetType.S3_BUCKET):
        try:
            validate_hierarchy(child_type, None)
            raise AssertionError("expected ValidationAppError")
        except ValidationAppError:
            pass

    try:
        validate_hierarchy(AssetType.WEBSITE, "00000000-0000-4000-8000-000000000001")
        raise AssertionError("expected ValidationAppError")
    except ValidationAppError:
        pass

    try:
        validate_parent_type(AssetType.PUBLIC_IP, AssetType.DOMAIN)
        raise AssertionError("expected ValidationAppError")
    except ValidationAppError:
        pass
