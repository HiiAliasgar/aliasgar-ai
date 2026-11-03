from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Aliasgar AI"
    app_env: str = "development"
    app_api_token: str = "change-me"
    database_url: str = "sqlite:///./data/aliasgar_ai.db"

    ai_provider: str = "gemini"
    gemini_api_key: str = ""
    google_api_key: str = ""
    openai_api_key: str = ""
    openai_model: str = "gemini-3.8-flash"
    openai_max_tool_rounds: int = 5

    github_token: str = ""
    github_owner: str = "HiiAliasgar"
    whatsapp_verify_token: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_allowed_phones: str = ""
    meta_app_secret: str = ""
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    @property
    def normalized_ai_provider(self) -> str:
        return self.ai_provider.strip().lower()

    @property
    def api_key_env_name(self) -> str:
        if self.normalized_ai_provider == "gemini":
            return "GEMINI_API_KEY or GOOGLE_API_KEY"
        if self.normalized_ai_provider == "openai":
            return "OPENAI_API_KEY"
        return "a valid AI provider configuration"

    @property
    def active_api_key(self) -> str:
        if self.normalized_ai_provider == "gemini":
            return self.gemini_api_key.strip() or self.google_api_key.strip()
        if self.normalized_ai_provider == "openai":
            return self.openai_api_key.strip()
        return ""

    @property
    def ai_configured(self) -> bool:
        return bool(self.active_api_key)

    @property
    def model_migrated(self) -> bool:
        return self.normalized_ai_provider == "gemini" and self.openai_model.strip() == "gemini-2.5-flash-lite"

    @property
    def model_name(self) -> str:
        configured = self.openai_model.strip() or "gemini-3.8-flash"
        if self.normalized_ai_provider == "gemini" and configured == "gemini-2.5-flash-lite":
            return "gemini-3.8-flash"
        return configured

    @property
    def allowed_phones(self) -> set[str]:
        return {
            phone.strip().replace("+", "").replace(" ", "")
            for phone in self.whatsapp_allowed_phones.split(",")
            if phone.strip()
        }


settings = Settings()
