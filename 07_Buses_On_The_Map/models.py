import dataclasses


@dataclasses.dataclass
class WindowBounds:
    south_lat: float = None
    north_lat: float = None
    east_lng: float = None
    west_lng: float = None

    def update(self, south_lat, north_lat, east_lng, west_lng):
        self.south_lat = south_lat
        self.north_lat = north_lat
        self.east_lng = east_lng
        self.west_lng = west_lng


@dataclasses.dataclass
class Bus:
    busId: str
    lat: float
    lng: float
    route: str

    def is_inside(self, bounds: WindowBounds):
        if bounds.is_null():
            return

        is_lat_inside = bounds.south_lat < self.lat < bounds.north_lat
        is_lng_inside = bounds.west_lng < self.lng < bounds.east_lng

        return all((is_lat_inside, is_lng_inside))
