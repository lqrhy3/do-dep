from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_prefix='POSTGRES_',
        extra='ignore',
        env_ignore_empty=True,
    )

    user: str
    password: str
    host: str = 'postgres'
    port: int = 5432
    db: str

    @property
    def url(self) -> str:
        return f'postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}'


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    bot_token: str
    game_url: str
    game_short_name: str

    initial_balance: int
    jackpot_multiplier: float


class Settings(BaseModel):
    db: DBSettings = DBSettings()
    app: AppSettings = AppSettings()


settings = Settings()
