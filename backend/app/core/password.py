import re

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>\[\]/_+=\-]).+$"
)
PASSWORD_REQUIREMENTS_MESSAGE = (
    "Password must be at least 12 characters and include uppercase, "
    "lowercase, number, and special character"
)


def validate_password_strength(password: str) -> None:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
    if len(password) > PASSWORD_MAX_LENGTH:
        raise ValueError(f"Password must be at most {PASSWORD_MAX_LENGTH} characters")
    if not PASSWORD_PATTERN.match(password):
        raise ValueError(PASSWORD_REQUIREMENTS_MESSAGE)
