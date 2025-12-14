from enum import Enum


class CartEnum(str, Enum):
    ACTIVE = "active"
    ORDERED = "ordered"
