from pydantic import BaseModel, Field


class SolicitudVideo(BaseModel):
    url: str


class DeltaVolumen(BaseModel):
    delta: int = Field(default=10, ge=1, le=100)


class DeltaTiempo(BaseModel):
    time: int = Field(default=30, ge=1)


class SolicitudSeek(BaseModel):
    time: str


class SolicitudIP(BaseModel):
    ip: str
