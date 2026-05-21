import pandas as pd
import numpy as np
import os
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import feedparser

from sklearn.ensemble import RandomForestRegressor


# =========================================================
# CONVERT EXCEL TO CSV
# =========================================================
def convert_excel_to_csv(file_path):

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found")

    if file_path.endswith(".csv"):
        return file_path

    df = pd.read_excel(
        file_path,
        engine="openpyxl"
    )

    csv_path = (
        file_path
        .replace(".xlsx", ".csv")
        .replace(".xls", ".csv")
    )

    df.to_csv(csv_path, index=False)

    return csv_path


# =========================================================
# LOAD + UPDATE PORTFOLIO
# =========================================================
# =========================================================
# LOAD + UPDATE PORTFOLIO
# =========================================================
def load_and_update_portfolio(file_path):

    # =====================================================
    # LOAD FILE
    # =====================================================
    if file_path.endswith(".csv"):

        df = pd.read_csv(file_path)

    else:

        df = pd.read_excel(
            file_path,
            engine="openpyxl"
        )

    # =====================================================
    # REQUIRED COLUMNS
    # =====================================================
    required_cols = {
        "Ticker",
        "Quantity",
        "Avg_Price",
        "Investment_Value"
    }

    if not required_cols.issubset(df.columns):

        raise ValueError(
            f"Portfolio must contain:\n"
            f"{required_cols}"
        )

    # =====================================================
    # CLEAN TICKERS
    # =====================================================
    df["Ticker"] = (
        df["Ticker"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # =====================================================
    # FETCH LIVE PRICES
    # =====================================================
    live_prices = []

    for ticker in df["Ticker"]:

        try:

            # ---------------------------------------------
            # REMOVE DUPLICATE .NS
            # ---------------------------------------------
            ticker = ticker.replace(".NS", "")

            yahoo_symbol = f"{ticker}.NS"

            stock = yf.Ticker(yahoo_symbol)

            history = stock.history(period="1d")

            # ---------------------------------------------
            # VALIDATE DATA
            # ---------------------------------------------
            if history.empty:

                print(
                    f"No data found for {yahoo_symbol}"
                )

                live_prices.append(np.nan)

                continue

            price = history["Close"].iloc[-1]

            # ---------------------------------------------
            # HANDLE INVALID PRICE
            # ---------------------------------------------
            if pd.isna(price):

                live_prices.append(np.nan)

            else:

                live_prices.append(float(price))

        except Exception as e:

            print(
                f"ERROR FETCHING {ticker}: {e}"
            )

            live_prices.append(np.nan)

    # =====================================================
    # ADD LIVE PRICES
    # =====================================================
    df["Live_Price"] = live_prices

    # =====================================================
    # REMOVE INVALID STOCKS
    # =====================================================
    df = df.dropna(
        subset=["Live_Price"]
    )

    # =====================================================
    # HANDLE EMPTY DATAFRAME
    # =====================================================
    if df.empty:

        raise ValueError(
            "No valid stock prices could be fetched.\n"
            "Please check ticker symbols."
        )

    # =====================================================
    # CALCULATE VALUES
    # =====================================================
    df["Current_Value"] = (
        df["Quantity"] * df["Live_Price"]
    )

    df["Profit/Loss"] = (
        df["Current_Value"]
        - df["Investment_Value"]
    )

    return df

# =========================================================
# PORTFOLIO SUMMARY
# =========================================================
def get_portfolio_summary(df):

    total_investment = df["Investment_Value"].sum()

    current_value = df["Current_Value"].sum()

    total_pl = (
        current_value - total_investment
    )

    profit_percent = (
        (total_pl / total_investment) * 100
        if total_investment != 0 else 0
    )

    top_gainer = df.loc[
        df["Profit/Loss"].idxmax()
    ]

    top_loser = df.loc[
        df["Profit/Loss"].idxmin()
    ]

    summary = (
        f"Total Investment: ₹{total_investment:,.2f}\n"
        f"Current Value: ₹{current_value:,.2f}\n"
        f"Net {'Profit' if total_pl > 0 else 'Loss'}: "
        f"₹{abs(total_pl):,.2f}\n"
        f"Overall Return: {profit_percent:.2f}%\n\n"
        f"Top Gainer: {top_gainer['Ticker']}\n"
        f"Top Loser: {top_loser['Ticker']}"
    )

    return summary


# =========================================================
# STOCK PRICE PREDICTION
# =========================================================
def predict_stock_price(
    ticker,
    days_ahead=30
):

    try:

        if ".NS" not in ticker:

            ticker = ticker + ".NS"

        data = yf.download(
            ticker,
            period="6mo",
            interval="1d"
        )

        if len(data) < 20:

            return None

        data = data.reset_index()

        data["Date_Ordinal"] = data[
            "Date"
        ].map(pd.Timestamp.toordinal)

        X = data[["Date_Ordinal"]]

        y = data["Close"]

        model = RandomForestRegressor(
            n_estimators=200,
            random_state=42
        )

        model.fit(X, y)

        future_dates = np.array([
            data["Date_Ordinal"].iloc[-1] + i
            for i in range(1, days_ahead + 1)
        ]).reshape(-1, 1)

        future_preds = model.predict(
            future_dates
        )

        return future_preds[-1]

    except Exception as e:

        print(
            f"Prediction Error ({ticker}): {e}"
        )

        return None


# =========================================================
# INVESTMENT SUGGESTIONS
# =========================================================
def suggest_best_investments(
    df,
    days_ahead=30
):

    results = []

    for ticker in df["Ticker"]:

        future_price = predict_stock_price(
            ticker,
            days_ahead
        )

        if future_price is None:
            continue

        current_price = df.loc[
            df["Ticker"] == ticker,
            "Live_Price"
        ].values[0]

        growth = (
            (
                future_price - current_price
            ) / current_price
        ) * 100

        results.append(
            (
                ticker,
                current_price,
                future_price,
                growth
            )
        )

    if not results:

        return None, None

    results_df = pd.DataFrame(
        results,
        columns=[
            "Ticker",
            "Current",
            "Predicted",
            "Growth_%"
        ]
    )

    best_stocks = results_df.sort_values(
        "Growth_%",
        ascending=False
    ).head(3)

    return results_df, best_stocks


# =========================================================
# GENERATE PORTFOLIO CHARTS
# =========================================================
def generate_portfolio_charts(df):

    os.makedirs("charts", exist_ok=True)

    # =====================================================
    # ALLOCATION PIE CHART
    # =====================================================
    plt.figure(figsize=(8, 8))

    plt.pie(
        df["Current_Value"],
        labels=df["Ticker"],
        autopct="%1.1f%%"
    )

    plt.title("Portfolio Allocation")

    allocation_chart = (
        "charts/portfolio_allocation.png"
    )

    plt.savefig(allocation_chart)

    plt.close()

    # =====================================================
    # PROFIT LOSS BAR CHART
    # =====================================================
    plt.figure(figsize=(10, 6))

    colors = [
        "green" if x >= 0 else "red"
        for x in df["Profit/Loss"]
    ]

    plt.bar(
        df["Ticker"],
        df["Profit/Loss"],
        color=colors
    )

    plt.axhline(0, color="black")

    plt.title("Profit / Loss by Stock")

    plt.xlabel("Stocks")

    plt.ylabel("Profit / Loss")

    performance_chart = (
        "charts/performance_chart.png"
    )

    plt.savefig(performance_chart)

    plt.close()

    return allocation_chart, performance_chart


# =========================================================
# MARKET ALERTS
# =========================================================
def get_market_alerts():

    nifty = yf.Ticker("^NSEI")

    banknifty = yf.Ticker("^NSEBANK")

    nifty_price = (
        nifty.history(period="1d")
        ["Close"]
        .iloc[-1]
    )

    banknifty_price = (
        banknifty.history(period="1d")
        ["Close"]
        .iloc[-1]
    )

    alerts = (
        f"NIFTY 50: {nifty_price:.2f}\n"
        f"BANK NIFTY: {banknifty_price:.2f}"
    )

    return alerts


# =========================================================
# INDIAN STOCK NEWS
# =========================================================
def get_indian_stock_news():

    feed_url = (
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
    )

    feed = feedparser.parse(feed_url)

    news_items = []

    for entry in feed.entries[:5]:

        news_items.append(
            f"• {entry.title}"
        )

    return "\n".join(news_items)