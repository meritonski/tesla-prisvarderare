import numpy as np
import pandas as pd
import streamlit as st

from domain.statistics import (
    weighted_percentile,
    remove_price_outliers,
)

from domain.similarity import calculate_similarity_weights

from domain.adjustments import calculate_risk_adjustment

DATA_FILE = "ev_market_ranked.csv"


st.set_page_config(
    page_title="Elbilsvärderaren",
    page_icon="⚡",
    layout="wide"
)


CUSTOM_CSS = """
<style>
.block-container {
    max-width: 1180px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

.main-title {
    font-size: 3.2rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    margin-bottom: 0.2rem;
}

.subtitle {
    font-size: 1.08rem;
    color: #6b7280;
    max-width: 860px;
    margin-bottom: 2rem;
    line-height: 1.55;
}

.section-title {
    font-size: 1.45rem;
    font-weight: 850;
    margin-top: 1.2rem;
    margin-bottom: 0.8rem;
    letter-spacing: -0.02em;
}

.verdict-good {
    background: linear-gradient(135deg, #16a34a, #22c55e);
    color: white;
    padding: 1.2rem 1.4rem;
    border-radius: 18px;
    font-size: 1.35rem;
    font-weight: 900;
    margin-bottom: 0.8rem;
}

.verdict-ok {
    background: linear-gradient(135deg, #2563eb, #38bdf8);
    color: white;
    padding: 1.2rem 1.4rem;
    border-radius: 18px;
    font-size: 1.35rem;
    font-weight: 900;
    margin-bottom: 0.8rem;
}

.verdict-warning {
    background: linear-gradient(135deg, #f59e0b, #f97316);
    color: white;
    padding: 1.2rem 1.4rem;
    border-radius: 18px;
    font-size: 1.35rem;
    font-weight: 900;
    margin-bottom: 0.8rem;
}

.verdict-bad {
    background: linear-gradient(135deg, #dc2626, #ef4444);
    color: white;
    padding: 1.2rem 1.4rem;
    border-radius: 18px;
    font-size: 1.35rem;
    font-weight: 900;
    margin-bottom: 0.8rem;
}

.verdict-text {
    color: #374151;
    font-size: 1.05rem;
    line-height: 1.55;
    margin-bottom: 0.8rem;
}

.mini-card {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 1rem 1.1rem;
    height: 100%;
}

.mini-label {
    color: #6b7280;
    font-size: 0.9rem;
    font-weight: 650;
    margin-bottom: 0.25rem;
}

.mini-value {
    color: #111827;
    font-size: 1.45rem;
    font-weight: 900;
    letter-spacing: -0.03em;
    overflow-wrap: anywhere;
}

.warning-box {
    padding: 0.95rem 1rem;
    border-radius: 15px;
    background: #fff7ed;
    border: 1px solid #fed7aa;
    color: #9a3412;
    margin-bottom: 0.65rem;
    line-height: 1.45;
}

.info-box {
    padding: 0.95rem 1rem;
    border-radius: 15px;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #1e40af;
    margin-bottom: 0.65rem;
    line-height: 1.45;
}

.ad-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 20px;
    padding: 1.1rem 1.15rem;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
    height: 100%;
}

.ad-title {
    color: #111827;
    font-size: 1.05rem;
    font-weight: 850;
    margin-bottom: 0.55rem;
}

.ad-price {
    color: #111827;
    font-size: 1.65rem;
    font-weight: 950;
    letter-spacing: -0.035em;
    margin-bottom: 0.25rem;
}

.ad-meta {
    color: #4b5563;
    font-size: 0.95rem;
    margin-bottom: 0.85rem;
}

.ad-link {
    display: inline-block;
    text-decoration: none !important;
    background: #111827;
    color: #ffffff !important;
    padding: 0.55rem 0.8rem;
    border-radius: 999px;
    font-size: 0.9rem;
    font-weight: 750;
}

.method-box {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 20px;
    padding: 1.1rem 1.2rem;
    color: #374151;
    line-height: 1.6;
    font-size: 0.98rem;
}

.badge {
    display: inline-block;
    padding: 0.35rem 0.65rem;
    border-radius: 999px;
    background: #eef2ff;
    color: #3730a3;
    font-weight: 800;
    font-size: 0.85rem;
    margin-bottom: 0.8rem;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)

    df["price_sek"] = pd.to_numeric(df["price_sek"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["mileage_km"] = pd.to_numeric(df["mileage_km"], errors="coerce")

    required_columns = ["make", "model", "variant", "display_name", "url"]
    for col in required_columns:
        if col not in df.columns:
            df[col] = "Okänd"

    df = df.dropna(subset=["price_sek", "year", "mileage_km", "display_name"])
    df = df[df["price_sek"].between(50000, 2500000)]
    df = df[df["year"].between(2015, 2027)]

    if "url" in df.columns:
        df = df[df["url"].astype(str).str.contains("/mobility/item/", na=False)]

    return df


def kr(value):
    return f"{value:,.0f} kr".replace(",", " ")


def km(value):
    return f"{value:,.0f} km".replace(",", " ")


def choose_comparison_group(df, display_name, year):
    same_car = df[df["display_name"] == display_name].copy()
    same_car_year = same_car[same_car["year"].astype(int) == int(year)].copy()

    selected_row = same_car.iloc[0] if len(same_car) else None

    if len(same_car_year) >= 5:
        return same_car_year, f"{display_name}, {int(year)}", "Hög"

    if len(same_car) >= 8:
        return same_car, f"{display_name}, alla årsmodeller", "Medel"

    if selected_row is not None:
        same_make_model = df[
            (df["make"] == selected_row["make"])
            & (df["model"] == selected_row["model"])
        ].copy()

        if len(same_make_model) >= 8:
            return same_make_model, f"{selected_row['make']} {selected_row['model']}, alla varianter", "Låg"

        same_make = df[df["make"] == selected_row["make"]].copy()

        if len(same_make) >= 8:
            return same_make, f"{selected_row['make']}, alla modeller", "Låg"

    return df.copy(), "Hela datasetet", "Mycket låg"


def estimate_market_value_from_comps(comparison_df, target_year, target_mileage_km):
    temp = comparison_df.copy()
    temp = remove_price_outliers(temp)

    if len(temp) == 0:
        return None

    weights = calculate_similarity_weights(temp, target_year, target_mileage_km)

    weighted_median_price = weighted_percentile(temp["price_sek"], weights, 50)
    weighted_low = weighted_percentile(temp["price_sek"], weights, 25)
    weighted_high = weighted_percentile(temp["price_sek"], weights, 75)

    simple_median = temp["price_sek"].median()
    median_mileage = temp["mileage_km"].median()
    median_year = temp["year"].median()

    km_difference = float(target_mileage_km) - float(median_mileage)
    year_difference = float(target_year) - float(median_year)

    if km_difference < 0:
        km_adjustment = abs(km_difference / 1000) * 450
    else:
        km_adjustment = -(km_difference / 1000) * 900

    year_adjustment = year_difference * 22000

    estimated_price = weighted_median_price + km_adjustment + year_adjustment

    spread = max(
        weighted_high - weighted_low,
        estimated_price * 0.06,
        25000
    )

    fair_low = estimated_price - spread
    fair_high = estimated_price + spread

    return {
        "cleaned_df": temp,
        "weights": weights,
        "estimated_price": estimated_price,
        "fair_low": fair_low,
        "fair_high": fair_high,
        "weighted_median_price": weighted_median_price,
        "simple_median": simple_median,
        "median_mileage": median_mileage,
        "median_year": median_year,
        "km_adjustment": km_adjustment,
        "year_adjustment": year_adjustment,
        "spread": spread,
        "outliers_removed": len(comparison_df) - len(temp),
    }



def calculate_confidence_score(cleaned_df, comparison_quality, fair_low, fair_high, estimated_price):
    n = len(cleaned_df)

    if n >= 25:
        sample_score = 40
    elif n >= 15:
        sample_score = 32
    elif n >= 8:
        sample_score = 24
    elif n >= 5:
        sample_score = 16
    else:
        sample_score = 8

    if comparison_quality == "Hög":
        group_score = 35
    elif comparison_quality == "Medel":
        group_score = 25
    elif comparison_quality == "Låg":
        group_score = 15
    else:
        group_score = 8

    interval_width_percent = (fair_high - fair_low) / estimated_price

    if interval_width_percent <= 0.12:
        spread_score = 25
    elif interval_width_percent <= 0.20:
        spread_score = 18
    elif interval_width_percent <= 0.30:
        spread_score = 10
    else:
        spread_score = 5

    score = sample_score + group_score + spread_score
    return int(max(0, min(100, score)))


def calculate_fair_price(df, display_name, year, mileage_km):
    comparison_df, comparison_label, comparison_quality = choose_comparison_group(
        df,
        display_name,
        year
    )

    market = estimate_market_value_from_comps(
        comparison_df,
        year,
        mileage_km
    )

    if market is None:
        st.error("Det finns inte tillräckligt med data för att göra en värdering.")
        st.stop()

    risk_adjustment, warnings = calculate_risk_adjustment(year, mileage_km)

    estimated_fair_price = market["estimated_price"] - risk_adjustment
    fair_low = market["fair_low"] - risk_adjustment
    fair_high = market["fair_high"] - risk_adjustment

    confidence_score = calculate_confidence_score(
        market["cleaned_df"],
        comparison_quality,
        fair_low,
        fair_high,
        estimated_fair_price
    )

    if confidence_score >= 75:
        confidence_label = "Hög"
    elif confidence_score >= 55:
        confidence_label = "Medel"
    elif confidence_score >= 35:
        confidence_label = "Låg"
    else:
        confidence_label = "Mycket låg"

    if comparison_quality in ["Låg", "Mycket låg"]:
        warnings.append(
            "Jämförelsegruppen är bred. Värderingen är därför mer osäker än om fler annonser fanns för exakt samma biltyp och årsmodell."
        )

    if market["outliers_removed"] > 0:
        warnings.append(
            f"{market['outliers_removed']} extremannons har tagits bort från beräkningen för att undvika att enstaka avvikande priser styr värderingen."
        )

    return {
        "comparison_df": market["cleaned_df"],
        "comparison_label": comparison_label,
        "comparison_quality": comparison_quality,
        "median_price": market["simple_median"],
        "median_mileage": market["median_mileage"],
        "median_year": market["median_year"],
        "weighted_median_price": market["weighted_median_price"],
        "mileage_adjustment": market["km_adjustment"],
        "year_adjustment": market["year_adjustment"],
        "risk_penalty": risk_adjustment,
        "warnings": warnings,
        "estimated_fair_price": estimated_fair_price,
        "fair_low": fair_low,
        "fair_high": fair_high,
        "confidence_score": confidence_score,
        "confidence_label": confidence_label,
        "outliers_removed": market["outliers_removed"],
    }


def verdict_for_price(asking_price, fair_price, fair_low, fair_high):
    if asking_price < fair_low * 0.97:
        return {
            "label": "Bra pris",
            "class": "verdict-good",
            "text": "Priset ligger under det beräknade marknadsintervallet. Det kan vara ett bra köp, men kontrollera skick, historik och utrustning.",
        }

    if fair_low * 0.97 <= asking_price <= fair_high * 1.03:
        return {
            "label": "Rimligt pris",
            "class": "verdict-ok",
            "text": "Priset ligger inom eller nära det beräknade marknadsintervallet.",
        }

    if asking_price <= fair_high * 1.10:
        return {
            "label": "Lite högt pris",
            "class": "verdict-warning",
            "text": "Priset ligger över marknadsintervallet, men inte extremt. Det kan vara motiverat om bilen har stark utrustning, garanti eller mycket gott skick.",
        }

    return {
        "label": "Högt pris",
        "class": "verdict-bad",
        "text": "Priset ligger tydligt över det beräknade marknadsintervallet. Begärt pris bör förhandlas eller motiveras av ovanligt stark utrustning eller skick.",
    }


df = load_data()

if len(df) == 0:
    st.error("Ingen giltig data hittades. Kontrollera att ev_market_ranked.csv finns.")
    st.stop()


st.markdown('<div class="main-title">Elbilsvärderaren</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Värdera en elbil genom en robust marknadsmodell som väger jämförbara annonser efter årsmodell och miltal, filtrerar bort extrema prisavvikelser och visar ett beräknat marknadsintervall.</div>',
    unsafe_allow_html=True,
)


left, right = st.columns([0.34, 0.66], gap="large")


with left:
    st.markdown('<div class="section-title">Bilens uppgifter</div>', unsafe_allow_html=True)

    with st.container(border=True):
        makes = sorted(df["make"].dropna().unique())
        make = st.selectbox("Märke", makes)

        model_options = sorted(df[df["make"] == make]["model"].dropna().unique())
        model = st.selectbox("Modell", model_options)

        display_options = sorted(
            df[
                (df["make"] == make)
                & (df["model"] == model)
            ]["display_name"].dropna().unique()
        )

        display_name = st.selectbox("Variant", display_options)

        available_years = sorted(
            df[df["display_name"] == display_name]["year"].dropna().astype(int).unique()
        )

        year = st.selectbox("Årsmodell", available_years)

        mileage_km = st.number_input(
            "Miltal i kilometer",
            min_value=0,
            max_value=500000,
            value=75000,
            step=1000
        )

        asking_price = st.number_input(
            "Pris i kronor",
            min_value=50000,
            max_value=2500000,
            value=400000,
            step=5000
        )

    st.markdown('<div class="section-title">Databas</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.metric("Antal annonser", f"{len(df)}")
        st.metric("Antal biltyper", f"{df['display_name'].nunique()}")
        st.caption(
            f"Prisintervall: {kr(df['price_sek'].min())} – {kr(df['price_sek'].max())}"
        )


result = calculate_fair_price(df, display_name, year, mileage_km)

estimated_fair_price = result["estimated_fair_price"]
comparison_df = result["comparison_df"]
median_price = result["median_price"]
median_mileage = result["median_mileage"]
mileage_adjustment = result["mileage_adjustment"]
year_adjustment = result["year_adjustment"]
risk_penalty = result["risk_penalty"]
warnings = result["warnings"]
fair_low = result["fair_low"]
fair_high = result["fair_high"]
confidence_score = result["confidence_score"]
confidence_label = result["confidence_label"]
outliers_removed = result["outliers_removed"]

difference = asking_price - estimated_fair_price
difference_percent = difference / estimated_fair_price * 100

verdict = verdict_for_price(
    asking_price,
    estimated_fair_price,
    fair_low,
    fair_high
)


with right:
    st.markdown('<div class="section-title">Bedömning</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="{verdict["class"]}">{verdict["label"]}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(f'<div class="verdict-text">{verdict["text"]}</div>', unsafe_allow_html=True)

    metric_cols = st.columns(3)

    with metric_cols[0]:
        st.markdown(
            f"""
            <div class="mini-card">
                <div class="mini-label">Angivet pris</div>
                <div class="mini-value">{kr(asking_price)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with metric_cols[1]:
        st.markdown(
            f"""
            <div class="mini-card">
                <div class="mini-label">Uppskattat marknadsvärde</div>
                <div class="mini-value">{kr(estimated_fair_price)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with metric_cols[2]:
        st.markdown(
            f"""
            <div class="mini-card">
                <div class="mini-label">Skillnad</div>
                <div class="mini-value">{kr(difference)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write(
        f"Priset är **{abs(difference_percent):.1f}%** "
        f"{'över' if difference > 0 else 'under'} uppskattat marknadsvärde."
    )

    st.write(
        f"Beräknat marknadsintervall: **{kr(fair_low)} – {kr(fair_high)}**."
    )

    st.write(
        f"Datakvalitet: **{confidence_label}** ({confidence_score}/100)."
    )

    st.markdown(
        f"""
        <div class="info-box">
        Modellen anger inte ett exakt facit, utan ett sannolikt marknadsintervall. 
        Ett pris inom intervallet räknas därför som marknadsmässigt rimligt.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if warnings:
        st.markdown('<div class="section-title">Viktiga varningar</div>', unsafe_allow_html=True)
        for warning in warnings:
            st.markdown(
                f'<div class="warning-box">⚠️ {warning}</div>',
                unsafe_allow_html=True,
            )


st.markdown('<div class="section-title">Jämförelsegrund</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="mini-label">Vald bil</div>
            <div class="mini-value">{display_name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="mini-label">Jämförelsegrupp</div>
            <div class="mini-value" style="font-size:1.15rem;">{result["comparison_label"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="mini-label">Medianpris</div>
            <div class="mini-value">{kr(median_price)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="mini-label">Medianmiltal</div>
            <div class="mini-value">{km(median_mileage)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown('<div class="section-title">Beräkningsdetaljer</div>', unsafe_allow_html=True)

d1, d2, d3, d4 = st.columns(4)

with d1:
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="mini-label">Viktad median</div>
            <div class="mini-value">{kr(result["weighted_median_price"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with d2:
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="mini-label">Årsjustering</div>
            <div class="mini-value">{kr(year_adjustment)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with d3:
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="mini-label">Miltalsjustering</div>
            <div class="mini-value">{kr(mileage_adjustment)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with d4:
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="mini-label">Riskjustering</div>
            <div class="mini-value">-{kr(risk_penalty)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown('<div class="section-title">Tre närmaste jämförelseannonser</div>', unsafe_allow_html=True)

similar = comparison_df.copy()

similar["similarity_score"] = (
    abs(similar["year"].astype(float) - float(year)) * 2.0
    + abs(similar["mileage_km"].astype(float) - float(mileage_km)) / 25000
)

similar = similar.sort_values("similarity_score").head(3).copy()

ad_cols = st.columns(3)

for col, (_, row) in zip(ad_cols, similar.iterrows()):
    with col:
        st.markdown(
            f"""
            <div class="ad-card">
                <div class="badge">{row["display_name"]}</div>
                <div class="ad-title">{row["display_name"]}</div>
                <div class="ad-price">{kr(row["price_sek"])}</div>
                <div class="ad-meta">
                    Årsmodell: <b>{int(row["year"])}</b><br>
                    Miltal: <b>{km(row["mileage_km"])}</b>
                </div>
                <a class="ad-link" href="{row["url"]}" target="_blank">Öppna annons</a>
            </div>
            """,
            unsafe_allow_html=True,
        )


st.markdown('<div class="section-title">Prisnivå i databasen</div>', unsafe_allow_html=True)

year_summary = (
    df.groupby(["display_name", "year"])["price_sek"]
    .agg(["count", "median", "min", "max"])
    .reset_index()
)

year_summary["year"] = year_summary["year"].astype(int)
year_summary["median"] = year_summary["median"].apply(kr)
year_summary["min"] = year_summary["min"].apply(kr)
year_summary["max"] = year_summary["max"].apply(kr)

year_summary = year_summary.rename(
    columns={
        "display_name": "Bil",
        "year": "Årsmodell",
        "count": "Antal",
        "median": "Medianpris",
        "min": "Lägsta pris",
        "max": "Högsta pris",
    }
)

st.dataframe(year_summary, use_container_width=True, hide_index=True)


st.markdown('<div class="section-title">Metod och begränsningar</div>', unsafe_allow_html=True)

st.markdown(
    """
<div class="method-box">
Modellen bygger på annonserade begärpriser från ett insamlat marknadsurval. Först väljs den mest relevanta
jämförelsegruppen: samma biltyp och årsmodell om tillräckligt många annonser finns, annars samma biltyp över flera
årsmodeller eller en bredare grupp.
<br><br>
För att göra värderingen mer robust tas extrema prisavvikelser bort med IQR-metoden. Därefter viktas varje jämförelseannons
efter hur nära den ligger den valda bilen i årsmodell och miltal. Annonser som liknar bilen mer får därför större påverkan
på uppskattningen.
<br><br>
Appen visar både ett uppskattat marknadsvärde och ett marknadsintervall. Intervallet är viktigt eftersom begagnatmarknaden
inte har ett exakt facit. Pris, skick, utrustning, vinterhjul, dragkrok, servicehistorik, antal ägare, importhistorik,
garanti och finansieringsvillkor behöver alltid granskas separat innan köp.
</div>
""",
    unsafe_allow_html=True,
)
