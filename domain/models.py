from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class PurchaseVerdict(Enum):
    EXCELLENT = "Fantastiskt köp"
    GOOD = "Bra köp"
    FAIR = "Rimligt pris"
    HIGH = "Lite dyr"
    OVERPRICED = "Överpris"


class AdjustmentCategory(Enum):
    AGE = "Ålder"
    MILEAGE = "Miltal"
    WARRANTY = "Garanti"
    BATTERY = "Batteri"
    EQUIPMENT = "Utrustning"
    MARKET = "Marknad"
    SERVICE = "Servicehistorik"
    CONDITION = "Skick"
    OTHER = "Övrigt"


@dataclass(slots=True, frozen=True)
class VersionInfo:
    application_version: str = "2.0.0"
    valuation_algorithm: str = "Hybrid"
    model_version: str = "Hybrid-2.0"
    data_snapshot: str = "unknown"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True, frozen=True)
class VehicleSpec:
    make: str
    model: str
    variant: str
    year: int
    mileage_km: int
    display_name: str | None = None
    drivetrain: str | None = None
    battery_size_kwh: float | None = None
    body_type: str | None = None
    registration_date: datetime | None = None
    color: str | None = None

    def normalized_display_name(self) -> str:
        if self.display_name:
            return self.display_name.strip()
        parts = [self.make, self.model, self.variant]
        return " ".join(part.strip() for part in parts if part and part.strip())


@dataclass(slots=True, frozen=True)
class CarListing:
    spec: VehicleSpec
    asking_price: float
    condition: str | None = None
    service_history: bool | None = None
    battery_health_percent: float | None = None
    warranty_remaining_months: int | None = None
    equipment: tuple[str, ...] = ()
    notes: str | None = None


@dataclass(slots=True, frozen=True)
class MarketListing:
    spec: VehicleSpec
    listing_price: float
    source: str = "unknown"
    url: str = ""
    listing_date: datetime | None = None
    id: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class Comparable:
    listing: MarketListing
    distance: float
    similarity: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ComparableSet:
    comparables: tuple[Comparable, ...]
    removed_outliers: tuple[MarketListing, ...] = ()
    statistics: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def size(self) -> int:
        return len(self.comparables)

    @property
    def prices(self) -> tuple[float, ...]:
        return tuple(c.listing.listing_price for c in self.comparables)

    @property
    def weights(self) -> tuple[float, ...]:
        return tuple(c.similarity for c in self.comparables)

    @property
    def distances(self) -> tuple[float, ...]:
        return tuple(c.distance for c in self.comparables)


@dataclass(slots=True, frozen=True)
class Adjustment:
    name: str
    category: AdjustmentCategory
    delta: float
    description: str
    weight: float = 1.0
    applied: bool = True


@dataclass(slots=True, frozen=True)
class MarketEstimate:
    estimated_price: float
    weighted_median: float
    weighted_mean: float
    market_interval_low: float
    market_interval_high: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    sample_size: int
    effective_sample_size: float
    reliability: float


@dataclass(slots=True, frozen=True)
class PurchaseScore:
    raw_score: float
    normalized_score: int
    reliability: float
    reasons: tuple[str, ...]
    verdict: PurchaseVerdict | None = None


@dataclass(slots=True, frozen=True)
class PriceExplanation:
    base_market_value: float
    final_market_value: float
    adjustments: tuple[Adjustment, ...]
    calculation_steps: tuple[str, ...] = ()

    @property
    def total_adjustment(self) -> float:
        return sum(adjustment.delta for adjustment in self.adjustments if adjustment.applied)


@dataclass(slots=True, frozen=True)
class DataQualityReport:
    sample_size: int
    effective_sample_size: float
    outliers_removed: int
    median_age_days: float
    coverage: float
    reliability: float


@dataclass(slots=True, frozen=True)
class Diagnostics:
    execution_time_ms: float
    estimator_version: str
    similarity_distribution: tuple[float, ...]
    warnings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ValuationResult:
    version: VersionInfo
    listing: CarListing
    comparable_set: ComparableSet
    market_estimate: MarketEstimate
    purchase_score: PurchaseScore
    explanation: PriceExplanation
    data_quality: DataQualityReport
    diagnostics: Diagnostics
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
