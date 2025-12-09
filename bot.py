#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import requests
import numpy as np
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("SIS")

# ----------------------------
# CONFIG
# ----------------------------
import os
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "NO_TOKEN_SET")

# ----------------------------
# Safe fetch candles from Binance
# ----------------------------
def fetch_candles():
    """Безпечне отримання close-цін з Binance."""
    url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=100"

    try:
        r = requests.get(url, timeout=10)
    except Exception as e:
        log.error(f"❌ Network error: {e}")
        return []

    try:
        data = r.json()
    except Exception as e:
        log.error(f"❌ Binance non-JSON: {e}")
        return []

    # Binance може повернути {"code": -1121, "msg": "..."}
    if not isinstance(data, list):
        log.error(f"❌ Binance error: {data}")
        return []

    if len(data) == 0:
        log.error("❌ Binance returned empty array")
        return []

    # Extract close prices safely
    closes = []
    for c in data:
        if isinstance(c, list) and len(c) > 4:
            try:
                closes.append(float(c[4]))
            except:
                continue

    if not closes:
        log.error("❌ No valid candle closes extracted")
        return []

    return np.array(closes)


# ----------------------------
# ANALYSIS COMMAND
# ----------------------------
async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info("/analysis called")

    closes = fetch_candles()
    if len(closes) < 10:
        await update.message.reply_text("⚠️ Not enough market data to analyze.")
        return

    ma20 = np.mean(closes[-20:])
    price = closes[-1]

    text = f"""
📊 *Market Analysis*
Price: `{price}`
MA20: `{ma20:.2f}`

Trend: {"UP" if price > ma20 else "DOWN"}
"""
    await update.message.reply_text(text, parse_mode="Markdown")


# ----------------------------
# TREND COMMAND
# ----------------------------
async def trend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info("/trend called")

    closes = fetch_candles()
    if len(closes) < 2:
        await update.message.reply_text("⚠️ No data available.")
        return

    trend_text = "UP 📈" if closes[-1] > closes[-2] else "DOWN 📉"

    await update.message.reply_text(f"Current Trend: *{trend_text}*", parse_mode="Markdown")


# ----------------------------
# APP INIT
# ----------------------------
def main():
    log.info("S.I.S. BOT starting...")

    if TELEGRAM_BOT_TOKEN == "NO_TOKEN_SET":
        log.error("❌ TELEGRAM_BOT_TOKEN is missing!")
        return

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("analysis", analysis))
    app.add_handler(CommandHandler("trend", trend))

    log.info("S.I.S. BOT running...")
    app.run_polling()


if __name__ == "__main__":
    main()

