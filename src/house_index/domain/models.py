from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from house_index.domain.enums import (
    Condition,
    PropertyType,
    Status,
    TransitKind,
)


@dataclass
class TransitStop:
    kind: TransitKind
    distance_m: int
    name: str | None = None
    id: int | None = None
    property_id: int | None = None


@dataclass
class Link:
    url: str
    label: str | None = None
    id: int | None = None
    property_id: int | None = None


@dataclass
class Photo:
    file_name: str
    is_primary: bool = False
    sort_order: int = 0
    id: int | None = None
    property_id: int | None = None


@dataclass
class Property:
    title: str
    property_type: PropertyType = PropertyType.APARTMENT
    primary_link: str | None = None
    multi_floor: bool = False

    price_pln: int | None = None
    area_m2: float | None = None
    distance_km: float | None = None
    rooms: int | None = None

    floor: int | None = None
    has_elevator: bool = False

    has_balcony: bool = False
    balcony_m2: float | None = None
    has_terrace: bool = False
    terrace_m2: float | None = None
    has_garden: bool = False
    garden_m2: float | None = None
    plot_m2: float | None = None

    has_garage: bool = False
    garage_spots: int = 0
    has_parking_spot: bool = False
    parking_spot_count: int = 0

    year_built: int | None = None
    has_cellar: bool = False
    cellar_m2: float | None = None

    condition: Condition | None = None

    nearest_supermarket_m: int | None = None
    nearest_kindergarten_state_m: int | None = None
    nearest_kindergarten_private_m: int | None = None
    nearest_hospital_m: int | None = None

    living_room_m2: float | None = None
    kitchen_m2: float | None = None
    bathroom_largest_m2: float | None = None
    bedroom_master_m2: float | None = None
    has_pantry: bool = False
    separate_wc_count: int = 0

    status: Status = Status.INTERESTED
    notes: str | None = None

    index_score: float | None = None
    index_breakdown: dict[str, Any] | None = None

    id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None

    transit_stops: list[TransitStop] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    photos: list[Photo] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    @property
    def price_per_m2(self) -> float | None:
        if self.price_pln is None or self.area_m2 is None or self.area_m2 == 0:
            return None
        return self.price_pln / self.area_m2

    @property
    def primary_photo(self) -> Photo | None:
        for p in self.photos:
            if p.is_primary:
                return p
        return self.photos[0] if self.photos else None

    @property
    def nearest_transit_m(self) -> int | None:
        if not self.transit_stops:
            return None
        return min(s.distance_m for s in self.transit_stops)

    def nearest_by_kind(self, kind: TransitKind) -> int | None:
        vals = [s.distance_m for s in self.transit_stops if s.kind == kind]
        return min(vals) if vals else None

    @property
    def nearest_mhd_m(self) -> int | None:
        vals = [
            s.distance_m
            for s in self.transit_stops
            if s.kind in (TransitKind.BUS, TransitKind.TRAM)
        ]
        return min(vals) if vals else None

    @property
    def nearest_train_m(self) -> int | None:
        return self.nearest_by_kind(TransitKind.TRAIN)

    @property
    def nearest_regional_bus_m(self) -> int | None:
        return self.nearest_by_kind(TransitKind.REGIONAL_BUS)
