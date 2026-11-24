"""
Index Production Exception Monitor
It simulates a daily validation workflow for index constituent data.

Structure:
    1. Load S&P 500 price and company data
    2. Clean and merge the datasets
    3. Calculate daily returns per stock
    4. Flag abnormal moves using Z-Scores
    5. Export an exception report (CSV) and an incident log (TXT)

Data source: Kaggle - S&P 500 Stocks (andrewmvd/sp-500-stocks)
Required files in the same folder: sp500_stocks.csv, sp500_companies.csv
"""

import pandas as pd

#Setup and initialization of variables and constants
STOCKS_FILE = "sp500_stocks.csv"
COMPANIES_FILE = "sp500_companies.csv"
REPORT_FILE = "sample_output/exception_report.csv"
LOG_FILE = "sample_output/incident_log.txt"

Z_THRESHOLD = 3                 #Flags moves beyond 3 standard deviations
MONITORING_WINDOW_DAYS = 90     #Limit only the report to the most recent 90 days of data

#Step 1: Data Loading - Read both CSV files into DataFrames
def load_data():
    stocks = pd.read_csv(STOCKS_FILE)
    companies = pd.read_csv(COMPANIES_FILE)
    print(f"Loaded {len(stocks):,} price rows and {len(companies):,} companies.")
    return stocks, companies



#Step 2: Clean the data - Fix data types and remove null/unusable rows
def clean_data(stocks,companies):
    #Convert Date field from text data type to date data type so sorting and filtering work
    stocks["Date"] = pd.to_datetime(stocks["Date"])

    #Drop rows with no price data since it cannot produce returns
    stocks = stocks.dropna(subset=["Close", "Adj Close", "Volume"])

    print(f"{len(stocks):,} price rows left after cleaning")
    return stocks, companies



#Step 3: Merge the data - attach company details to each price row using Symbol as primary key
def merge_data(stocks,companies):
    #One row per Symbol, so joining won't multiple price rows.
    companies = companies.drop_duplicates(subset=["Symbol"], keep="first")

    #Used left join to keep every price row even if the company info is missing.
    merged = stocks.merge(
        companies[["Symbol", "Shortname", "Sector", "Industry", "Weight"]],
        on="Symbol",
        how="left"
    )
    return merged



#Step 4: Daily returns - Add a Daily_Retrun column: % change in Adj Close against the prior day
def calculate_returns(prices):
    #Sort first so that pct_change won't compare the wrong rows
    prices = prices.sort_values(["Symbol", "Date"])

    #groupby keeps each stock's returns separate from other stocks.
    #Adj Close is used because it accounts for splits and dividends.
    #The first day of each stock is NaN (no prior day) - this is expected.
    prices["Daily_Return"] = prices.groupby("Symbol")["Adj Close"].pct_change()
    return prices



#Step 5: Anomaly detection - Flag days where a stock's return is unusual compared to its own historical average.
def detect_exceptions(df):
    #Each stock's normal behavior
    stats = (
        df.groupby("Symbol")["Daily_Return"]
        .agg(Mean_Return="mean", Std_Return="std")
        .reset_index()
    )
    df = df.merge(stats, on="Symbol", how="left")

    # Z-Score: how many standard deviations today's return is from normal.
    df["Z_Score"] = (df["Daily_Return"] - df["Mean_Return"]) / df["Std_Return"]
    df["Is_Exception"] = df["Z_Score"].abs() > Z_THRESHOLD

    print(f"Total exceptions across history: {df["Is_Exception"].sum():,}")
    return df



#Step 6: Exception report - Keep recent exceptions only, sorted by most severe cases first.
def build_exception_report(df):
    exceptions = df[df["Is_Exception"]]

    #NOTE!: The window is measured from the latest date in the data, not today's date.
    latest_date = df["Date"].max()
    cutoff_date = latest_date - pd.DateOffset(days=MONITORING_WINDOW_DAYS)
    exceptions = exceptions[exceptions["Date"] >= cutoff_date]

    report = exceptions[
        ["Date", "Symbol", "Shortname", "Sector", "Adj Close", "Daily_Return", "Z_Score", "Weight"]
    ].sort_values("Z_Score", key=abs, ascending=False)

    #.copy() makes report an independent table, so adding the Narrative column later won't touch the original data
    return report.copy()



#Step 7: Incident narratives - write a plain-english incident summary for one exception row
def generate_narrative(row):
    direction = "surge" if row["Daily_Return"] > 0 else "drop"
    return_pct = round(row["Daily_Return"] * 100, 2)
    z_score = round(row["Z_Score"], 2)
    date_str = row["Date"].strftime("%B %d, %Y")

    return(
        f"On {date_str}, {row['Shortname']} ({row['Symbol']}) recorded an "
        f"abnormal price {direction} of {return_pct}%, which is {z_score} "
        f"standard deviations from its historical average. "
        f"Sector: {row['Sector']}. Index Weight: {round(row['Weight'], 4)}. "
        f"Flagged for production review."
    )



#Step 8: Output - Save the structured report (CSV) and the readable incident log (TXT)
def write_outputs(report):
    report["Narrative"] = report.apply(generate_narrative, axis=1)
    report.to_csv(REPORT_FILE, index=False)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        for narrative in report["Narrative"]:
            f.write(narrative + "\n" + "-" * 80 + "\n")

    print(f"Saved {REPORT_FILE} and {LOG_FILE}.")
    return report



#Main
def main():
    stocks, companies = load_data()
    stocks, companies = clean_data(stocks,companies)
    merged = merge_data(stocks,companies)
    merged = calculate_returns(merged)
    merged = detect_exceptions(merged)
    report = build_exception_report(merged)
    report = write_outputs(report)

    print(f"\nExceptions flagged (last {MONITORING_WINDOW_DAYS} days: {len(report)})")
    if not report.empty:
        print("\nTop exception:")
        print(report["Narrative"].iloc[0])


if __name__ == "__main__":
    main()
