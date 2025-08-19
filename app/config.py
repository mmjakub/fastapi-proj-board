from enum import Enum

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class PgSettings(BaseModel):
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    dbname: str = "projects_app_dev"


class JwtAlg(str, Enum):
    HS256 = "HS256"


class JwtSettings(BaseModel):
    secret_key: str
    expires_minutes: int = 60
    algorithm: JwtAlg = JwtAlg.HS256


class S3Settings(BaseModel):
    bucket: str | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="_",
        env_nested_max_split=1,
        extra="ignore",
    )
    jwt: JwtSettings
    s3: S3Settings
    pg: PgSettings = PgSettings()


settings = Settings()  # type: ignore
