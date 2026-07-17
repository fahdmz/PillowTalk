import os

from dotenv import load_dotenv

load_dotenv()


def _positive_int(name: str, default: int, maximum: int | None = None) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    if maximum is not None and value > maximum:
        raise RuntimeError(f"{name} must not exceed {maximum}")
    return value


def _bounded_float(name: str, default: float, *, minimum: float, maximum: float) -> float:
    raw_value = os.getenv(name, str(default))
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a number") from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(f"{name} must be between {minimum} and {maximum}")
    return value


def _boolean(name: str, default: bool) -> bool:
    raw_value = os.getenv(name, str(default)).strip().casefold()
    if raw_value in {"true", "1", "yes", "on"}:
        return True
    if raw_value in {"false", "0", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be true or false")


class Settings:
    """Server-side configuration for Supabase and the PillowTalk API."""

    def __init__(self) -> None:
        self.supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.supabase_jwks_cache_seconds = _positive_int(
            "SUPABASE_JWKS_CACHE_SECONDS", 600, maximum=600
        )
        self.supabase_jwks_timeout_seconds = _positive_int(
            "SUPABASE_JWKS_TIMEOUT_SECONDS", 10
        )

        self.azure_ai_foundry_endpoint = os.getenv(
            "AZURE_AI_FOUNDRY_ENDPOINT", ""
        ).rstrip("/")
        self.azure_ai_foundry_api_key = os.getenv("AZURE_AI_FOUNDRY_API_KEY", "")
        self.azure_ai_foundry_chat_deployment = os.getenv(
            "AZURE_AI_FOUNDRY_CHAT_DEPLOYMENT", ""
        )
        self.azure_ai_foundry_classifier_deployment = os.getenv(
            "AZURE_AI_FOUNDRY_CLASSIFIER_DEPLOYMENT", ""
        )
        self.azure_ai_foundry_recap_deployment = os.getenv(
            "AZURE_AI_FOUNDRY_RECAP_DEPLOYMENT",
            self.azure_ai_foundry_classifier_deployment,
        )
        self.azure_ai_foundry_timeout_seconds = _positive_int(
            "AZURE_AI_FOUNDRY_TIMEOUT_SECONDS", 30
        )
        self.azure_ai_foundry_max_retries = _positive_int(
            "AZURE_AI_FOUNDRY_MAX_RETRIES", 2
        )

        self.emotion_model_id = os.getenv(
            "EMOTION_MODEL_ID", "mrezadit/indobert-emotion-classification"
        )
        self.emotion_model_revision = os.getenv("EMOTION_MODEL_REVISION", "main")
        self.hf_token = os.getenv("HF_TOKEN") or None
        self.emotion_model_device = os.getenv("EMOTION_MODEL_DEVICE", "cpu")
        self.emotion_local_confidence_threshold = _bounded_float(
            "EMOTION_LOCAL_CONFIDENCE_THRESHOLD", 0.65, minimum=0, maximum=1
        )
        self.emotion_fallback_enabled = _boolean(
            "EMOTION_FALLBACK_ENABLED", True
        )

        self.chat_recent_message_limit = _positive_int(
            "CHAT_RECENT_MESSAGE_LIMIT", 12, maximum=50
        )
        self.chat_memory_session_limit = _positive_int(
            "CHAT_MEMORY_SESSION_LIMIT", 3, maximum=10
        )
        self.chat_memory_lookback_days = _positive_int(
            "CHAT_MEMORY_LOOKBACK_DAYS", 14, maximum=90
        )
        self.chat_max_output_tokens = _positive_int(
            "CHAT_MAX_OUTPUT_TOKENS", 800, maximum=4000
        )
        self.chat_rate_limit_requests = _positive_int(
            "CHAT_RATE_LIMIT_REQUESTS", 20, maximum=1000
        )
        self.chat_rate_limit_window_seconds = _positive_int(
            "CHAT_RATE_LIMIT_WINDOW_SECONDS", 60, maximum=3600
        )
        # Hard backstop so a check-in always ends even if the model never
        # signals should_close — counts the user's own messages, not AI replies.
        self.chat_max_user_turns = _positive_int(
            "CHAT_MAX_USER_TURNS", 8, maximum=50
        )
        self.recap_max_output_tokens = _positive_int(
            "RECAP_MAX_OUTPUT_TOKENS", 500, maximum=4000
        )
        self.recap_generation_input_limit = _positive_int(
            "RECAP_GENERATION_INPUT_LIMIT", 200, maximum=1000
        )
        self.crisis_resource_name = os.getenv("CRISIS_RESOURCE_NAME", "Healing119")
        self.crisis_resource_phone = os.getenv(
            "CRISIS_RESOURCE_PHONE", "119 ext. 8"
        )
        self.crisis_resource_url = os.getenv(
            "CRISIS_RESOURCE_URL", "https://www.healing119.id"
        )

        origins = os.getenv("ALLOWED_ORIGINS", "*")
        self.allowed_origins = [
            origin.strip() for origin in origins.split(",") if origin.strip()
        ]

    @property
    def supabase_auth_issuer(self) -> str:
        return f"{self.supabase_url}/auth/v1"

    @property
    def supabase_jwks_url(self) -> str:
        return f"{self.supabase_auth_issuer}/.well-known/jwks.json"

    def validate(self) -> None:
        self._require(
            ("SUPABASE_URL", self.supabase_url),
            ("SUPABASE_SERVICE_ROLE_KEY", self.supabase_service_role_key),
        )

    def validate_ai(self) -> None:
        self._require(
            ("EMOTION_MODEL_ID", self.emotion_model_id),
            ("EMOTION_MODEL_REVISION", self.emotion_model_revision),
        )
        if self.emotion_fallback_enabled:
            self._require(
                ("AZURE_AI_FOUNDRY_ENDPOINT", self.azure_ai_foundry_endpoint),
                ("AZURE_AI_FOUNDRY_API_KEY", self.azure_ai_foundry_api_key),
                (
                    "AZURE_AI_FOUNDRY_CLASSIFIER_DEPLOYMENT",
                    self.azure_ai_foundry_classifier_deployment,
                ),
            )

    def validate_chat(self) -> None:
        self._require(
            ("AZURE_AI_FOUNDRY_ENDPOINT", self.azure_ai_foundry_endpoint),
            ("AZURE_AI_FOUNDRY_API_KEY", self.azure_ai_foundry_api_key),
            (
                "AZURE_AI_FOUNDRY_CHAT_DEPLOYMENT",
                self.azure_ai_foundry_chat_deployment,
            ),
            ("CRISIS_RESOURCE_NAME", self.crisis_resource_name),
            ("CRISIS_RESOURCE_PHONE", self.crisis_resource_phone),
            ("CRISIS_RESOURCE_URL", self.crisis_resource_url),
        )

    def validate_recap(self) -> None:
        self._require(
            ("AZURE_AI_FOUNDRY_ENDPOINT", self.azure_ai_foundry_endpoint),
            ("AZURE_AI_FOUNDRY_API_KEY", self.azure_ai_foundry_api_key),
            (
                "AZURE_AI_FOUNDRY_RECAP_DEPLOYMENT",
                self.azure_ai_foundry_recap_deployment,
            ),
        )

    @staticmethod
    def _require(*entries: tuple[str, str]) -> None:
        missing = [name for name, value in entries if not value]
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Copy backend/.env.example to backend/.env and fill in the values."
            )


settings = Settings()
