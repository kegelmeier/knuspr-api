from pydantic_settings import BaseSettings, SettingsConfigDict


class KnusprConfig(BaseSettings):
    username: str = ""
    password: str = ""
    base_url: str = "https://www.knuspr.de"
    language: str = "de-DE,de;q=0.9,en;q=0.8"
    min_request_interval: float = 0.1
    request_timeout: float = 10.0
    debug: bool = False

    model_config = SettingsConfigDict(
        env_prefix="KNUSPR_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
