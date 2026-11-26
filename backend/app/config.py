from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    admin_username: str = "admin"
    admin_password: str = "admin123"
    jwt_secret: str = "change-me-in-production"
    frontend_url: str = "http://localhost:5173"


config = AppConfig()
DB_PATH = BASE_DIR / "bungai.db"
CHAT_DB_PATH = BASE_DIR / "chat_sessions.db"
