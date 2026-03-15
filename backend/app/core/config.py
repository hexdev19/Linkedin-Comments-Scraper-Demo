from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    linkedin_email: str = ""
    linkedin_password: str = ""
    openai_api_key: str = ""
    chrome_profile_path: str = "./chrome_profile"
    
    max_comments: int = 50
    max_scroll: int = 20
    scroll_delay: int = 2

settings = Settings()
