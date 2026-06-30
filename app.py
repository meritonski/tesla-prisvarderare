import pandas as pd
import streamlit as st


DATA_FILE = "ranked_tesla_deals.csv"


st.set_page_config(
    page_title="Tesla Prisvärderare",
    page_icon="🚗",
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
    max-width: 780px;
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
    font-size: 1.55rem;
    font-weight: 900;
    letter-spacing: -0.03em;
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

hr {
    margin-top: 1.4rem;
    margin-bottom: 1.4rem;
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

    if "variant" not in df.columns:
        df["variant"] = "Performance"

    df = df.dropna(subset=["price_sek", "year", "mileage_km", "variant"])
    df = df[df["price_sek"].between(200000, 900000)]

    if "url" in df.columns:
        df = df[df["url"].astype(str).str.contains("/mobility/item/", na=False)]

    return df


def kr(value):
    return f"{value:,.0f} kr".replace(",", " ")


def km(value):
    return f"{value:,.0f} km".replace(",", " ")


def calculate_warranty_penalty(year, mileage_km):
    current_year = 2026
    car_age = current_year - int(year)

    penalty = 0
    warnings = []

    if mileage_km >= 80000:
        penalty += 15000
        warnings.append(
            "Bilen har passerat 80 000 km. Det kan påverka trygghetsvärde, vagnskadegaranti och andrahandsvärde."
        )

    if mileage_km >= 120000:
        penalty += 20000
        warnings.append(
            "Bilen har passerat 120 000 km. Högt miltal bör ge tydligare prisavdrag."
        )

    if mileage_km >= 160000:
        penalty += 50000
        warnings.append(
            "Bilen har passerat 160 000 km. Batteri- eller drivlinegaranti kan vara förbrukad på miltal."
        )

    if car_age >= 8:
        penalty += 40000
        warnings.append(
            "Bilen är 8 år eller äldre. Batteri- eller drivlinegaranti kan vara förbrukad på ålder."
        )

    return penalty, warnings


def calculate_fair_price(df, variant, year, mileage_km):
    same_variant = df[df["variant"] == variant].copy()
    same_variant_year = same_variant[same_variant["year"].astype(int) == int(year)].copy()

    if len(same_variant_year) >= 5:
        comparison_df = same_variant_year
        comparison_label = f"{variant}, {int(year)}"
    elif len(same_variant) >= 5:
        comparison_df = same_variant
        comparison_label = f"{variant}, alla årsmodeller"
    else:
        comparison_df = df.copy()
        comparison_label = "Hela datasetet"

    median_price = comparison_df["price_sek"].median()
    median_mileage = comparison_df["mileage_km"].median()

    km_difference = mileage_km - median_mileage

    if km_difference < 0:
        mileage_adjustment = abs(km_difference / 1000) * 350
    else:
        mileage_adjustment = -(km_difference / 1000) * 1200

    warranty_penalty, warnings = calculate_warranty_penalty(year, mileage_km)

    estimated_fair_price = median_price + mileage_adjustment - warranty_penalty

    return {
        "comparison_df": comparison_df,
        "comparison_label": comparison_label,
        "median_price": median_price,
        "median_mileage": median_mileage,
        "mileage_adjustment": mileage_adjustment,
        "warranty_penalty": warranty_penalty,
        "warnings": warnings,
        "estimated_fair_price": estimated_fair_price,
    }


def verdict_for_price(asking_price, fair_price):
    ratio = asking_price / fair_price

    if ratio <= 0.92:
        return {
            "label": "Bra pris",
            "class": "verdict-good",
            "text": "Priset ligger tydligt under uppskattat marknadsvärde för vald variant och årsmodell.",
        }

    if ratio <= 1.03:
        return {
            "label": "Rimligt pris",
            "class": "verdict-ok",
            "text": "Priset ligger nära uppskattat marknadsvärde.",
        }

    if ratio <= 1.08:
        return {
            "label": "Lite högt pris",
            "class": "verdict-warning",
            "text": "Priset ligger något över uppskattat marknadsvärde.",
        }

    return {
        "label": "Högt pris",
        "class": "verdict-bad",
        "text": "Priset ligger tydligt över uppskattat marknadsvärde.",
    }


df = load_data()

if len(df) == 0:
    st.error("Ingen giltig data hittades. Kontrollera att ranked_tesla_deals.csv finns.")
    st.stop()


st.markdown('<div class="main-title">Tesla Prisvärderare</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Värdera en Tesla Model Y genom att jämföra pris, årsmodell och miltal mot ett insamlat marknadsurval.</div>',
    unsafe_allow_html=True,
)


left, right = st.columns([0.34, 0.66], gap="large")


with left:
    st.markdown('<div class="section-title">Bilens uppgifter</div>', unsafe_allow_html=True)

    with st.container(border=True):
        variant = st.selectbox(
            "Variant",
            sorted(df["variant"].dropna().unique())
        )

        available_years = sorted(
            df[df["variant"] == variant]["year"].dropna().astype(int).unique()
        )

        year = st.selectbox(
            "Årsmodell",
            available_years
        )

        mileage_km = st.number_input(
            "Miltal i kilometer",
            min_value=0,
            max_value=300000,
            value=75000,
            step=1000
        )

        asking_price = st.number_input(
            "Pris i kronor",
            min_value=100000,
            max_value=1000000,
            value=400000,
            step=5000
        )

    st.markdown('<div class="section-title">Databas</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.metric("Antal annonser", f"{len(df)}")

        variant_counts = df["variant"].value_counts()

        for name, count in variant_counts.items():
            st.metric(name, f"{count}")

        st.caption(
            f"Prisintervall: {kr(df['price_sek'].min())} – {kr(df['price_sek'].max())}"
        )


result = calculate_fair_price(df, variant, year, mileage_km)

estimated_fair_price = result["estimated_fair_price"]
comparison_df = result["comparison_df"]
median_price = result["median_price"]
median_mileage = result["median_mileage"]
mileage_adjustment = result["mileage_adjustment"]
warranty_penalty = result["warranty_penalty"]
warnings = result["warnings"]

difference = asking_price - estimated_fair_price
difference_percent = difference / estimated_fair_price * 100

verdict = verdict_for_price(asking_price, estimated_fair_price)


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
                <div class="mini-label">Uppskattat rimligt pris</div>
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
            <div class="mini-label">Variant</div>
            <div class="mini-value">{variant}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="mini-label">Jämförelsegrupp</div>
            <div class="mini-value" style="font-size:1.25rem;">{result["comparison_label"]}</div>
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


st.markdown('<div class="section-title">Tre närmaste jämförelseannonser</div>', unsafe_allow_html=True)

similar = comparison_df.copy()

similar["similarity_score"] = (
    abs(similar["price_sek"] - asking_price) / 10000
    + abs(similar["mileage_km"] - mileage_km) / 10000
)

similar = similar.sort_values("similarity_score").head(3).copy()

ad_cols = st.columns(3)

for col, (_, row) in zip(ad_cols, similar.iterrows()):
    with col:
        st.markdown(
            f"""
            <div class="ad-card">
                <div class="badge">{row["variant"]}</div>
                <div class="ad-title">Tesla Model Y {row["variant"]}</div>
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
    df.groupby(["variant", "year"])["price_sek"]
    .agg(["count", "median", "min", "max"])
    .reset_index()
)

year_summary["year"] = year_summary["year"].astype(int)
year_summary["median"] = year_summary["median"].apply(kr)
year_summary["min"] = year_summary["min"].apply(kr)
year_summary["max"] = year_summary["max"].apply(kr)

year_summary = year_summary.rename(
    columns={
        "variant": "Variant",
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
Modellen bygger på annonserade begärpriser från ett insamlat marknadsurval. Bilen jämförs först
med annonser för samma variant och, när det finns tillräckligt många träffar, samma årsmodell.
Därefter justeras det uppskattade värdet utifrån miltal. Högre miltal ger prisavdrag och extra
riskavdrag läggs till vid viktiga gränser som 80 000 km, 120 000 km och 160 000 km.
<br><br>
Resultatet ska ses som en marknadsindikator, inte som ett exakt värde. Skick, utrustning,
vinterhjul, dragkrok, servicehistorik, antal ägare, importhistorik och kvarvarande garanti
behöver kontrolleras separat innan köp.
</div>
""",
    unsafe_allow_html=True,
)
