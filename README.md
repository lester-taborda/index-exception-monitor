# Index Production Exception Monitor

A Python automation tool simulating the daily validation workflow for index constituent data in a financial data production environment.

## Motivation
I built this simple Python tool to demonstrate production operations thinking applied in a real-world financial index data, particularly the automated exception detection, incident triage, and operational reporting workflows that's fundamental in real-time index production.


## What it does
- Loads S&P 500 constituent price and company data
- Cleans and validates source data (handles missing prices and date formatting)
- Merges the 2 datasets using Symbol as the primary/linking key
- Calculates daily returns per constituent using Adjusted Close price
- Detects anomalies using Z-Score statistical thresholds (it flags moves beyond 3 standard deviations from each stock's historical average)
- Filters exception to a 90-day monitoring window (Note: It's measured from the latest date in the dataset - late 2024)
- Generates a structured exception CSV report sorted by severity.
- Generates plain-English incident narrative for each flagged exception which reduces the manual write-up effort and ensures consistent documentation

## Outputs
| File | Description                                                                                                |
|------|------------------------------------------------------------------------------------------------------------|
|`exception_report.csv` | Structured exception report with date, symbol, name, sector, return, Z-Score, index weight, and narrative. |
| `incident_log.txt` | Plain-text readable audit trail of all flagged incidents (sorted by severity).                             |

## Data Source
### Kaggle - S&P500 Stocks Dataset 
from andrewmvd/sp-500-stocks
<https://www.kaggle.com/datasets/andrewmvd/sp-500-stocks>

Download and place the following files in the same directory as the script:
- sp500_stocks.csv  - Daily price data per constituent
- sp500_companies.csv - Constituent metadata (sector, industry, index weight, etc.)

>**NOTE:** These files are excluded from this repository due to its size. You can access the dataset for free in Kaggle from the link above.

## How to Run
1. Clone this repository
2. Download the dataset from Kaggle (link above)
3. Place both CSV files in the project root directory
4. Install dependencies: 

```bash
pip install -r requirements.txt
```

5. Run the script:

```bash
python exception_monitor.py
```

## Sample Output
```
On October 31, 2024, Huntington Ingalls Industries,  (HII) recorded an abnormal price drop of -26.16%, which is -15.06 standard deviations from its historical average. Sector: Industrials. Index Weight: 0.0001. Flagged for production review.
```

## Key Considerations
**Why use Adjusted Close over Close (price)?**
Because Adjusted Close (price) accounts for stock splits and dividends which gives accurate representation of true price movement. Raw Close (price) can show artificial price jumps that would generate false exceptions.

**Why Z-Score for anomaly detection?**
A 5% daily move for a volatile tech stock is normal but "extreme" for some like utility stocks. Z-Score normalizes across all constituents by measuring each move against that stock's own historical behavior and not a fixed percentage threshold. This approach lets one rule apply across sectors with very different volatility.

**Why a 3 standard deviation threshold?**
Because it's common convention for flagging statistical outlier. Genuine anomalies usually fall beyond 3 standard deviations.

**Why 90-day monitoring window?**
Full historical data (back to 2010) is used to build each stock's behavioral baseline. The actionable exception report is filtered from the last 90 days only which is a relevant operational window for a production team.

## Limitations
- Uses historical data, not a live feed.
- Flag statistical outliers only. The flagged moves are not checked against news or corporate events which means each one still needs human review.
- Z-scores uses each stock's full-history average and standard deviation, which makes this only a simple screening method and not a production-grade model.

## Technologies
- Python 3
- Pandas

## Author
Lester John G. Taborda