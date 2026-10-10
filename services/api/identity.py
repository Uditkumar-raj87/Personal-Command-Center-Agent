from fastapi import Header


DEVELOPMENT_USER_ID = "development-user"


def current_user_id(x_user_id: str | None = Header(default=None)) -> str:
    """Development identity boundary; replace this dependency with production auth."""
    return x_user_id or DEVELOPMENT_USER_ID