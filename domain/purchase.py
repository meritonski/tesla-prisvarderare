from __future__ import annotations

from dataclasses import dataclass

from domain.models import MarketEstimate


@dataclass(slots=True, frozen=True)
class ReliabilityBreakdown:
    sample_score: float
    variance_score: float
    similarity_score: float
    freshness_score: float
    effective_sample_score: float

    @property
    def reliability(self) -> float:
        score = (
            self.sample_score
            * self.variance_score
            * self.similarity_score
            * self.freshness_score
            * self.effective_sample_score
        )

        return max(0.0, min(100.0, score))


class PurchaseEvaluator:
    """
    Beräknar ett numeriskt Purchase Score.

    Denna klass känner INTE till
    'Bra köp'
    'Fantastiskt köp'

    Den returnerar endast ett värde mellan 0 och 100.
    """

    def calculate(
        self,
        asking_price: float,
        market: MarketEstimate,
    ) -> float:

        estimated = market.estimated_price

        if estimated <= 0:
            return 0.0

        difference_percent = (
            (estimated - asking_price)
            / estimated
        ) * 100.0

        #
        # 100 = extremt billigt
        # 50 = marknadspris
        # 0 = kraftigt överpris
        #

        score = 50.0 + difference_percent * 2.5

        score = max(0.0, min(100.0, score))

        return score

    def reliability(
        self,
        sample_size: int,
        effective_sample_size: float,
        variance_ratio: float,
        average_similarity: float,
        freshness: float = 1.0,
    ) -> ReliabilityBreakdown:

        sample_score = min(sample_size / 30.0, 1.0)

        effective_sample_score = min(
            effective_sample_size / 20.0,
            1.0,
        )

        similarity_score = max(
            0.0,
            min(
                average_similarity,
                1.0,
            ),
        )

        variance_score = max(
            0.0,
            min(
                1.0 - variance_ratio,
                1.0,
            ),
        )

        freshness_score = max(
            0.0,
            min(
                freshness,
                1.0,
            ),
        )

        return ReliabilityBreakdown(
            sample_score=sample_score,
            variance_score=variance_score,
            similarity_score=similarity_score,
            freshness_score=freshness_score,
            effective_sample_score=effective_sample_score,
        )
