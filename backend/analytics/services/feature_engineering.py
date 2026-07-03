import pandas as pd
import ta

# Explicit, ordered feature set shared by training and inference. Every feature
# is dimensionless (returns, ratios, normalized oscillators) so a model trained
# on one series transfers to any other ticker.
FEATURE_COLUMNS = [
    "pct_1d",
    "pct_5d",
    "pct_10d",
    "trend_10d",
    "rsi_14",
    "macd_norm",
    "macd_signal_norm",
    "sma10_sma50_ratio",
    "close_sma20_ratio",
    "volatility_10d",
]

TARGET_COLUMN = "target_next_pct"


def build_feature_frame(close: pd.Series) -> pd.DataFrame:
    """Build scale-free features and the next-day pct-change target from a
    close-price series. Early rows contain NaN (longest lookback is SMA-50)
    and the last row's target is NaN; callers filter what they need."""
    df = pd.DataFrame({"close": close.astype(float)})
    pct = df["close"].pct_change()

    df["pct_1d"] = pct
    df["pct_5d"] = df["close"].pct_change(5)
    df["pct_10d"] = df["close"].pct_change(10)
    df["trend_10d"] = pct.rolling(10).mean()
    df["rsi_14"] = ta.momentum.rsi(df["close"], window=14) / 100.0
    df["macd_norm"] = ta.trend.macd(df["close"]) / df["close"]
    df["macd_signal_norm"] = ta.trend.macd_signal(df["close"]) / df["close"]

    sma10 = ta.trend.sma_indicator(df["close"], window=10)
    sma20 = ta.trend.sma_indicator(df["close"], window=20)
    sma50 = ta.trend.sma_indicator(df["close"], window=50)
    df["sma10_sma50_ratio"] = sma10 / sma50 - 1.0
    df["close_sma20_ratio"] = df["close"] / sma20 - 1.0

    df["volatility_10d"] = pct.rolling(10).std()

    df[TARGET_COLUMN] = pct.shift(-1)
    return df
