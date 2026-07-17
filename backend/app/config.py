import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Reads Supabase project settings from the environment. Auth itself is
    handled entirely by Supabase Auth on the Flutter side — this backend only
    verifies the JWT Supabase already issued (see app/deps.py)."""

    def __init__(self) -> None:
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
        origins = os.getenv("ALLOWED_ORIGINS", "*")
        self.allowed_origins = [o.strip() for o in origins.split(",") if o.strip()]

    def validate(self) -> None:
        missing = [
            name
            for name, value in (
                ("SUPABASE_URL", self.supabase_url),
                ("SUPABASE_SERVICE_ROLE_KEY", self.supabase_service_role_key),
                ("SUPABASE_JWT_SECRET", self.supabase_jwt_secret),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Copy backend/.env.example to backend/.env and fill in your Supabase project values."
            )


settings = Settings()
