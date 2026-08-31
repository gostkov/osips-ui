from pydantic import BaseModel, Field


class RtpengineRowIn(BaseModel):
    socket: str = Field(min_length=1, max_length=255)
    set_id: int = Field(default=0, ge=0)


class RtpengineRowUpdate(BaseModel):
    socket: str | None = Field(default=None, min_length=1, max_length=255)
    set_id: int | None = Field(default=None, ge=0)


class RtpengineEnableIn(BaseModel):
    enabled: bool


class RtpengineReloadIn(BaseModel):
    # soft-перезагрузка не рвёт уже установленные соединения с работающими сокетами
    soft: bool = False
