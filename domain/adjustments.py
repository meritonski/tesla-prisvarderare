def calculate_risk_adjustment(year, mileage_km):
    current_year = 2026
    car_age = current_year - int(year)

    adjustment = 0
    warnings = []

    if mileage_km > 80000:
        extra_km = mileage_km - 80000
        adjustment += min(extra_km / 1000 * 250, 15000)
        warnings.append(
            "Bilen har passerat 80 000 km. Kalkylen lägger därför in en försiktig riskjustering."
        )

    if mileage_km > 120000:
        extra_km = mileage_km - 120000
        adjustment += min(extra_km / 1000 * 450, 25000)
        warnings.append(
            "Bilen har passerat 120 000 km. Osäkerheten ökar och priset bör granskas mer kritiskt."
        )

    if mileage_km > 160000:
        extra_km = mileage_km - 160000
        adjustment += 35000 + min(extra_km / 1000 * 500, 30000)
        warnings.append(
            "Bilen har passerat 160 000 km. Det ger ett större riskavdrag eftersom batteri, drivlina och andrahandsvärde blir mer osäkra."
        )

    if car_age >= 8:
        adjustment += 30000
        warnings.append(
            "Bilen är 8 år eller äldre. Kalkylen lägger in åldersrisk eftersom garanti och framtida reparationsrisk kan påverka värdet."
        )

    return adjustment, warnings
