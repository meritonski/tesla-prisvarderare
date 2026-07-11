import pandas as pd

INPUT_FILE = "ev_market_database.csv"
OUTPUT_FILE = "ev_market_ranked.csv"

df = pd.read_csv(INPUT_FILE)

df["price_sek"] = pd.to_numeric(df["price_sek"], errors="coerce")
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["mileage_km"] = pd.to_numeric(df["mileage_km"], errors="coerce")

required_columns = ["make", "model", "variant", "display_name", "url"]
for col in required_columns:
    if col not in df.columns:
        df[col] = "Okänd"

df = df.dropna(subset=["price_sek", "year", "mileage_km", "display_name"])

df = df[df["url"].astype(str).str.contains("/mobility/item/", na=False)]

# Grundfilter för rimliga elbilsannonser
df = df[df["price_sek"].between(50000, 2500000)]
df = df[df["year"].between(2015, 2026)]

# Fokusera på verkliga begagnatannonser, inte rena nybils-/lagerannonser
df = df[df["mileage_km"] >= 100]

# Ta bort exakta dubbletter
df = df.drop_duplicates(subset=["url", "display_name"])
df = df.drop_duplicates(subset=["display_name", "year", "price_sek", "mileage_km"])

# Ta bort extrema prisavvikelser per biltyp när gruppen är tillräckligt stor
cleaned_groups = []

for display_name, year, group in df.groupby("display_name", "year"):
    group = group.copy()

    if len(group) >= 8:
        q1 = group["price_sek"].quantile(0.25)
        q3 = group["price_sek"].quantile(0.75)
        iqr = q3 - q1

        if iqr > 0:
            lower = q1 - 1.75 * iqr
            upper = q3 + 1.75 * iqr
            group = group[(group["price_sek"] >= lower) & (group["price_sek"] <= upper)]

    cleaned_groups.append(group)

df = pd.concat(cleaned_groups, ignore_index=True)

print("")
print("SAMMANFATTNING")
print("--------------")
print("Antal annonser:", len(df))

print("")
print("ANTAL PER BIL")
print("-------------")
print(df["display_name"].value_counts().to_string())

print("")
print("MEDIANPRIS PER BIL OCH ÅRSMODELL")
print("--------------------------------")
print(
    df.groupby(["display_name", "year"])["price_sek"]
    .agg(["count", "median", "min", "max"])
    .sort_index()
    .to_string()
)

df2 = df.copy()

df2["price_rank"] = df2.groupby(["display_name", "year"])["price_sek"].rank(ascending=True)
df2["mileage_rank"] = df2.groupby(["display_name", "year"])["mileage_km"].rank(ascending=True)
df2["year_rank"] = df2.groupby(["display_name"])["year"].rank(ascending=False)

df2["deal_score"] = (
    df2["price_rank"] * 0.50
    + df2["mileage_rank"] * 0.30
    + df2["year_rank"] * 0.20
)

df2 = df2.sort_values(["display_name", "deal_score"])

print("")
print("BÄSTA KANDIDATER")
print("----------------")
print(
    df2[
        [
            "display_name",
            "price_sek",
            "year",
            "mileage_km",
            "deal_score",
            "url",
        ]
    ]
    .head(80)
    .to_string(index=False)
)

df2.to_csv(OUTPUT_FILE, index=False)

print("")
print("Sparade rankad lista i", OUTPUT_FILE)
