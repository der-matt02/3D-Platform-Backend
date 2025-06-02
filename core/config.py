from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str
    DATABASE_NAME: str
    SECRET_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()
