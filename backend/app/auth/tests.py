"""Auth feature tests — expand as the module grows."""


def test_auth_module_imports() -> None:
    from app.auth.models import RefreshToken
    from app.auth.schemas import normalize_email
    from app.auth.services import auth_service, session_service

    assert RefreshToken.__tablename__ == "refresh_tokens"
    assert normalize_email("  Foo@Bar.COM ") == "foo@bar.com"
    assert callable(auth_service.login_user)
    assert callable(session_service.list_user_sessions)
