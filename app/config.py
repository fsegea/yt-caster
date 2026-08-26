from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    descargas_dir: str = "/descargas"
    chromecast_ip: str = "10.10.0.44"
    static_dir: str = "static"
    ruta_version: str = "VERSION"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def ruta_video(self) -> str:
        return f"{self.descargas_dir}/video.mp4"

    @property
    def ruta_info(self) -> str:
        return f"{self.descargas_dir}/video.info.json"

    @property
    def historico_dir(self) -> str:
        return f"{self.descargas_dir}/historico"
