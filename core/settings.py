from pydantic_settings import SettingsConfigDict, BaseSettings

class Settings(BaseSettings):
    secret_key: str
    token_duration: int
    stripe_webhook_secret: str
    database_url: str
    tests_database_url: str
    stripe_secret_key: str
    algorithm: str
    debug: bool = False
    postgres_user: str
    postgres_password: str
    postgres_name: str
    tests_postgres_name: str
    
    model_config= SettingsConfigDict(env_file=".env")


settings = Settings()