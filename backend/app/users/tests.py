"""Users feature tests — expand as the module grows."""


def test_users_module_imports() -> None:
    from app.users.models import User
    from app.users.services import user_service

    assert User.__tablename__ == "users"
    assert callable(user_service.get_user_profile)
