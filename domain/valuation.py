from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

import numpy as np
import pandas as pd

from domain.adjustments import AdjustmentEngine
from domain.models import (
    CarListing,
    ComparableSet,
    DataQualityReport,
    Diagnostics,
    MarketEstimate,
    MarketListing,
    PriceExplanation,
    PurchaseScore,
    PurchaseVerdict,
    ValuationResult,
    VersionInfo,
)
from domain.purchase import PurchaseEvaluator
from domain.similarity import SimilarityEngine
from domain.statistics import (
    effective_sample_size,
    remove_price_outliers_df,
    robust_price_summary,
    weighted_mean,
    weighted_median,
)


@dataclass(slots=True)
class ComparableSelector:
    """
    Väljer den bästa jämförelsegruppen.

    Prioritet:

    1. Samma bil + årsmodell
    2. Samma bil
    3. Samma modell
    4. Samma märke
    """

    minimum_same_year: int = 5
    minimum_same_variant: int = 8
    minimum_same_model: int = 8
    minimum_same_make: int = 8

    def select(
        self,
        target: CarListing,
        market: list[MarketListing],
    ) -> list[MarketListing]:

        spec = target.spec

        #
        # Samma variant + årsmodell
        #

        same_year = [
            listing
            for listing in market
            if (
                listing.spec.display_name == spec.display_name
                and listing.spec.year == spec.year
            )
        ]

        if len(same_year) >= self.minimum_same_year:
            return same_year

        #
        # Samma variant
        #

        same_variant = [
            listing
            for listing in market
            if listing.spec.display_name == spec.display_name
        ]

        if len(same_variant) >= self.minimum_same_variant:
            return same_variant

        #
        # Samma modell
        #

        same_model = [
            listing
            for listing in market
            if (
                listing.spec.make == spec.make
                and listing.spec.model == spec.model
            )
        ]

        if len(same_model) >= self.minimum_same_model:
            return same_model

        #
        # Samma märke
        #

        same_make = [
            listing
            for listing in market
            if listing.spec.make == spec.make
        ]

        if len(same_make) >= self.minimum_same_make:
            return same_make

        return market
