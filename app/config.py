from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Aliasgar AI"
    app_env: str = "development"
    app_api_token: str = "change-me"
    database_url: str = "sqlite:///./data/aliasgar_ai.db"
    ai_provider: str = "gemini"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    openai_model: str = "gemini-2.5-flash-lite"
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
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def allowed_phones(self) -> set[str]:
        return {p.strip().replace("+", "").replace(" ", "") for p in self.whatsapp_allowed_phones.split(",") if p.strip()}

settings = Settings()
