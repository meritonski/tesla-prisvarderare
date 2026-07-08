import numpy as np


def calculate_similarity_weights(comparison_df, target_year, target_mileage_km):
    temp = comparison_df.copy()

    year_diff = abs(temp["year"].astype(float) - float(target_year))
    mileage_diff = abs(temp["mileage_km"].astype(float) - float(target_mileage_km))

    year_scale = 2.0
    mileage_scale = 50000.0

    distance = np.sqrt(
        (year_diff / year_scale) ** 2
        + (mileage_diff / mileage_scale) ** 2
    )

    weights = np.exp(-0.5 * distance ** 2)

    return weights
