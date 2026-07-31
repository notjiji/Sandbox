"""Assets feature tests — expand as the module grows."""


def test_assets_module_imports() -> None:
    from app.assets.enums import AssetCriticality, AssetEnvironment, AssetStatus, AssetType, ROOT_ASSET_TYPES
    from app.assets.service import asset_service

    assert AssetType.WEBSITE.value == "website"
    assert AssetType.PUBLIC_IP.value == "public_ip"
    assert AssetType.WEBSITE in ROOT_ASSET_TYPES
    assert AssetStatus.PENDING.value == "pending"
    assert AssetStatus.ACTIVE.value == "active"
    assert AssetEnvironment.PRODUCTION.value == "production"
    assert AssetCriticality.CRITICAL.value == "critical"
    assert callable(asset_service.list_for_project)
    assert callable(asset_service.get_scan_target)
    assert callable(asset_service.resolve_plugin_targets)


def test_asset_hierarchy_validation() -> None:
    from app.assets.enums import AssetType
    from app.assets.validators import validate_asset_scannable, validate_hierarchy, validate_parent_type
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


def test_metadata_helpers() -> None:
    from app.assets.enums import AssetCriticality, AssetEnvironment, AssetStatus, AssetType
    from app.assets.metadata import PRIMARY_METADATA_KEYS, resolve_primary_value

    class StubAsset:
        type = AssetType.WEBSITE
        name = "Main site"

    assert PRIMARY_METADATA_KEYS[AssetType.WEBSITE] == "url"
    assert resolve_primary_value(StubAsset(), {"url": "https://example.com"}) == "https://example.com"
    assert resolve_primary_value(StubAsset(), {}) == "Main site"


def test_risk_criticality_multiplier() -> None:
    from app.risk.calculator import RiskCalculator

    calculator = RiskCalculator()
    base = calculator.score_findings([{"severity": "medium"}])
    weighted = calculator.score_findings(
        [{"severity": "medium", "criticality": "critical"}]
    )
    assert weighted > base


def test_website_url_validation() -> None:
    from app.assets.type_validators import validate_website_url
    from app.core.exceptions import ValidationAppError

    assert validate_website_url("https://vinca.family") == "https://vinca.family"
    assert validate_website_url("http://vinca.family/") == "http://vinca.family/"

    for invalid in ("abc", "example", "google", "vinca.family", "ftp://vinca.family"):
        try:
            validate_website_url(invalid)
            raise AssertionError(f"expected ValidationAppError for {invalid!r}")
        except ValidationAppError:
            pass


def test_domain_validation() -> None:
    from app.assets.type_validators import validate_domain_name
    from app.core.exceptions import ValidationAppError

    assert validate_domain_name("vinca.family") == "vinca.family"

    for invalid in ("https://vinca.family", "google", "abc"):
        try:
            validate_domain_name(invalid)
            raise AssertionError(f"expected ValidationAppError for {invalid!r}")
        except ValidationAppError:
            pass


def test_public_ip_validation() -> None:
    from app.assets.type_validators import validate_public_ipv4
    from app.core.exceptions import ValidationAppError

    assert validate_public_ipv4("203.0.113.10") == "203.0.113.10"
    assert validate_public_ipv4("10.0.0.5", allow_private=True) == "10.0.0.5"

    try:
        validate_public_ipv4("10.0.0.5")
        raise AssertionError("expected ValidationAppError")
    except ValidationAppError:
        pass

    try:
        validate_public_ipv4("not-an-ip")
        raise AssertionError("expected ValidationAppError")
    except ValidationAppError:
        pass


def test_server_metadata_validation() -> None:
    from app.assets.enums import AssetType
    from app.assets.type_validators import validate_asset_metadata
    from app.core.exceptions import ValidationAppError

    validate_asset_metadata(
        AssetType.SERVER,
        {
            "hostname": "prod-server",
            "os": "Ubuntu 24.04",
            "connection_type": "ssh",
        },
    )

    try:
        validate_asset_metadata(AssetType.SERVER, {"hostname": "prod-server"})
        raise AssertionError("expected ValidationAppError")
    except ValidationAppError:
        pass
