from pydantic import BaseModel


class WindowBoundsDataSerializer(BaseModel):
    east_lng: float
    north_lat: float
    south_lat: float
    west_lng: float


class WindowBoundsSerializer(BaseModel):
    msgType: str
    data: WindowBoundsDataSerializer


class BusSerializer(BaseModel):
    busId: str
    lat: float
    lng: float
    route: str
