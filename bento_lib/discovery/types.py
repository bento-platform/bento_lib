from typing import Literal, TypeAlias

__all__ = ["WarningsTuple", "DiscoveryEntity"]

WarningsTuple: TypeAlias = tuple[tuple[tuple[int | str, ...], str], ...]

DiscoveryEntity: TypeAlias = Literal["phenopacket", "individual", "biosample", "experiment"]
