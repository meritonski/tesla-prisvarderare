from __future__ import annotations

import math

import numpy as np
import pandas as pd


def clean_numeric_array(values: list[float] | tuple[float, ...] | np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    return array[np.isfinite(array)]


def clean_weighted_arrays(
    values: list[float] | tuple[float, ...] | np.ndarray,
    weights: list[float] | tuple[float, ...] | np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    value_array = np.asarray(values, dtype=float)
    weight_array = np.asarray(weights, dtype=float)

    if value_array.shape != weight_array.shape:
        raise ValueError("values och weights måste ha samma längd.")

    mask = np.isfinite(value_array) & np.isfinite(weight_array) & (weight_array > 0)
    return value_array[mask], weight_array[mask]


def weighted_mean(
    values: list[float] | tuple[float, ...] | np.ndarray,
    weights: list[float] | tuple[float, ...] | np.ndarray,
) -> float:
    value_array, weight_array = clean_weighted_arrays(values, weights)

    if len(value_array) == 0:
        return math.nan

    return float(np.average(value_array, weights=weight_array))


def weighted_percentile(
    values: list[float] | tuple[float, ...] | np.ndarray,
    weights: list[float] | tuple[float, ...] | np.ndarray,
    percentile: float,
) -> float:
    if percentile < 0 or percentile > 100:
        raise ValueError("percentile måste vara mellan 0 och 100.")

    value_array, weight_array = clean_weighted_arrays(values, weights)

    if len(value_array) == 0:
        return math.nan

    sorter = np.argsort(value_array)
    value_array = value_array[sorter]
    weight_array = weight_array[sorter]

    cumulative_weights = np.cumsum(weight_array)
    cutoff = percentile / 100.0 * cumulative_weights[-1]

    return float(value_array[np.searchsorted(cumulative_weights, cutoff)])


def weighted_median(
    values: list[float] | tuple[float, ...] | np.ndarray,
    weights: list[float] | tuple[float, ...] | np.ndarray,
) -> float:
    return weighted_percentile(values, weights, 50)


def effective_sample_size(weights: list[float] | tuple[float, ...] | np.ndarray) -> float:
    weight_array = np.asarray(weights, dtype=float)
    weight_array = weight_array[np.isfinite(weight_array) & (weight_array > 0)]

    if len(weight_array) == 0:
        return 0.0

    numerator = np.sum(weight_array) ** 2
    denominator = np.sum(weight_array ** 2)

    if denominator <= 0:
        return 0.0

    return float(numerator / denominator)


def median_absolute_deviation(
    values: list[float] | tuple[float, ...] | np.ndarray,
    scale: float = 1.4826,
) -> float:
    value_array = clean_numeric_array(values)

    if len(value_array) == 0:
        return math.nan

    median = np.median(value_array)
    mad = np.median(np.abs(value_array - median))

    return float(mad * scale)


def iqr_bounds(
    values: list[float] | tuple[float, ...] | np.ndarray,
    multiplier: float = 1.75,
) -> tuple[float, float]:
    value_array = clean_numeric_array(values)

    if len(value_array) == 0:
        return math.nan, math.nan

    q1 = np.percentile(value_array, 25)
    q3 = np.percentile(value_array, 75)
    iqr = q3 - q1

    if iqr <= 0:
        return float(np.min(value_array)), float(np.max(value_array))

    return float(q1 - multiplier * iqr), float(q3 + multiplier * iqr)


def mad_bounds(
    values: list[float] | tuple[float, ...] | np.ndarray,
    threshold: float = 3.5,
) -> tuple[float, float]:
    value_array = clean_numeric_array(values)

    if len(value_array) == 0:
        return math.nan, math.nan

    median = np.median(value_array)
    mad = median_absolute_deviation(value_array)

    if not np.isfinite(mad) or mad <= 0:
        return float(np.min(value_array)), float(np.max(value_array))

    return float(median - threshold * mad), float(median + threshold * mad)


def combined_outlier_bounds(
    values: list[float] | tuple[float, ...] | np.ndarray,
    iqr_multiplier: float = 1.75,
    mad_threshold: float = 3.5,
) -> tuple[float, float]:
    iqr_low, iqr_high = iqr_bounds(values, multiplier=iqr_multiplier)
    mad_low, mad_high = mad_bounds(values, threshold=mad_threshold)

    if not all(np.isfinite([iqr_low, iqr_high, mad_low, mad_high])):
        return iqr_low, iqr_high

    lower = max(iqr_low, mad_low)
    upper = min(iqr_high, mad_high)

    if lower > upper:
        return iqr_low, iqr_high

    return float(lower), float(upper)


def remove_price_outliers_df(
    df: pd.DataFrame,
    price_column: str = "price_sek",
    min_group_size: int = 8,
    iqr_multiplier: float = 1.75,
    mad_threshold: float = 3.5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if len(df) < min_group_size:
        return df.copy(), df.iloc[0:0].copy()

    prices = pd.to_numeric(df[price_column], errors="coerce")
    lower, upper = combined_outlier_bounds(
        prices.to_numpy(),
        iqr_multiplier=iqr_multiplier,
        mad_threshold=mad_threshold,
    )

    if not np.isfinite(lower) or not np.isfinite(upper):
        return df.copy(), df.iloc[0:0].copy()

    mask = prices.between(lower, upper)
    cleaned = df[mask].copy()
    removed = df[~mask].copy()

    return cleaned, removed


def robust_price_summary(
    prices: list[float] | tuple[float, ...] | np.ndarray,
    weights: list[float] | tuple[float, ...] | np.ndarray | None = None,
) -> dict[str, float]:
    price_array = clean_numeric_array(prices)

    if len(price_array) == 0:
        return {
            "count": 0.0,
            "mean": math.nan,
            "median": math.nan,
            "p25": math.nan,
            "p75": math.nan,
            "p95": math.nan,
            "iqr": math.nan,
            "mad": math.nan,
            "effective_sample_size": 0.0,
        }

    if weights is None:
        weight_array = np.ones_like(price_array, dtype=float)
    else:
        price_array, weight_array = clean_weighted_arrays(price_array, weights)

    p25 = weighted_percentile(price_array, weight_array, 25)
    p50 = weighted_percentile(price_array, weight_array, 50)
    p75 = weighted_percentile(price_array, weight_array, 75)
    p95 = weighted_percentile(price_array, weight_array, 95)

    return {
        "count": float(len(price_array)),
        "mean": weighted_mean(price_array, weight_array),
        "median": p50,
        "p25": p25,
        "p75": p75,
        "p95": p95,
        "iqr": float(p75 - p25),
        "mad": median_absolute_deviation(price_array),
       "effective_sample_size": effective_sample_size(weight_array),
    }
def remove_price_outliers(df):
    if len(df) < 8:
        return df.copy()

    q1 = df["price_sek"].quantile(0.25)
    q3 = df["price_sek"].quantile(0.75)
    iqr = q3 - q1

    if iqr <= 0:
        return df.copy()

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    return df[
        (df["price_sek"] >= lower)
        & (df["price_sek"] <= upper)
    ].copy()
