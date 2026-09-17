from typing import Literal

__all__ = ["WarningsTuple", "DiscoveryEntity"]

type WarningsTuple = tuple[tuple[tuple[int | str, ...], str], ...]

type DiscoveryEntity = Literal["phenopacket", "individual", "biosample", "experiment", "experiment_result"]
