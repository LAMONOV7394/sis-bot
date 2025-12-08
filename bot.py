import logging
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from telegram.ext import ApplicationBuilder, CommandHandler
from config import TELEGRAM_BOT_TOKEN

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("SIS")

def fetch_candles():
    url = "https://api.binance.com/api/v3/klines"
    r = requests.get(url, params={"symbol": "BTCUSDT", "interval": "1h", "limit": 200})
    data = r.json()
    return np.array([float(x[4]) for x in data])

def ema(values, span):
    return pd.Series(values).ewm(span=span).mean().iloc[-1]

def header(title):
    now = datetime.utcnow().strftime("%Y-%m-%d · %H:%M UTC")
    return f"{title}\n{now}\n"

async def analysis(update, context):
    closes = fetch_candles()
    price = closes[-1]

    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200)

    trend = "bullish" if ema50 > ema200 else "bearish"

    text = header("BTC · Market Intelligence")
    text += (
        f"\nprice: {price:.2f}"
        f"\ntrend: {trend}"
        f"\nema50: {ema50:.2f}"
        f"\nema200: {ema200:.2f}"
        "\n"
    )

    await update.message.reply_text(text)

async def trend(update, context):
    closes = fetch_candles()
    ema50_val = ema(closes, 50)
    ema200_val = ema(closes, 200)

    trend = "bullish" if ema50_val > ema200_val else "bearish"

    text = header("BTC · Trend Phase")
    text += (
        f"\ntrend: {trend}"
        f"\nema50: {ema50_val:.2f}"
        f"\nema200: {ema200_val:.2f}"
    )

    await update.message.reply_text(text)

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("analysis", analysis))
    app.add_handler(CommandHandler("trend", trend))
    log.info("S.I.S. BOT running...")
    app.run_polling()

if __name__ == "__main__":
    main()
