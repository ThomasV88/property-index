from enum import StrEnum


class PropertyType(StrEnum):
    APARTMENT = "apartment"
    HOUSE = "house"


class Condition(StrEnum):
    SHELL = "shell"
    STANDARD = "standard"
    TURNKEY = "turnkey"


class Status(StrEnum):
    INTERESTED = "interested"
    VISITED = "visited"
    REJECTED = "rejected"
    RESERVED = "reserved"


class TransitKind(StrEnum):
    BUS = "bus"
    TRAM = "tram"
    TRAIN = "train"
    REGIONAL_BUS = "regional_bus"


PROPERTY_TYPE_LABELS_SK = {
    PropertyType.APARTMENT: "Byt",
    PropertyType.HOUSE: "Dom",
}

CONDITION_LABELS_SK = {
    Condition.SHELL: "Holý byt/dom",
    Condition.STANDARD: "V štandarde",
    Condition.TURNKEY: "Na kľúč",
}

STATUS_LABELS_SK = {
    Status.INTERESTED: "Záujem",
    Status.VISITED: "Po obhliadke",
    Status.REJECTED: "Odmietnuté",
    Status.RESERVED: "Rezervované",
}

TRANSIT_LABELS_SK = {
    TransitKind.BUS: "MHD autobus",
    TransitKind.TRAM: "Električka",
    TransitKind.TRAIN: "Vlak",
    TransitKind.REGIONAL_BUS: "Regionálny bus",
}
