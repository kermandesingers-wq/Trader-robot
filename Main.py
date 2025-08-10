import os
import time
import requests
import numpy as np
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TOOBIT_API_KEY")
API_SECRET = os.getenv("TOOBIT_API_SECRET")

BASE_URL = "https://api.toobit.com"

HEADERS = {
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

SYMBOL = "BTCUSDT"

# پارامترهای استراتژی
LADDER_STEPS = 5         # تعداد پله‌ها
STEP_SIZE = 200          # فاصله قیمت هر پله
ORDER_QUANTITY = 0.001   # حجم هر سفارش
EMA_PERIOD = 20          # دوره EMA برای تایید روند

# تابع دریافت داده های کندل (مثلا آخرین قیمت ها)
def get_candles():
    endpoint = f"{BASE_URL}/api/v1/market/candles?symbol={SYMBOL}&interval=1m&limit=50"
    try:
        resp = requests.get(endpoint)
        data = resp.json()
        closes = [float(candle['close']) for candle in data['data']]
        return closes
    except Exception as e:
        print(f"Error fetching candles: {e}")
        return []

# محاسبه EMA
def calculate_ema(prices, period=20):
    prices = np.array(prices)
    ema = []
    k = 2 / (period + 1)
    for i in range(len(prices)):
        if i == 0:
            ema.append(prices[0])
        else:
            ema.append(prices[i]*k + ema[i-1]*(1-k))
    return ema[-1] if ema else None

# ارسال سفارش محدود
def place_limit_order(side, price, quantity):
    endpoint = f"{BASE_URL}/api/v1/trade/placeOrder"
    data = {
        "symbol": SYMBOL,
        "side": side,
        "type": "LIMIT",
        "price": price,
        "quantity": quantity,
        "timeInForce": "GTC"
    }
    try:
        resp = requests.post(endpoint, json=data, headers=HEADERS)
        if resp.status_code == 200:
            print(f"Order placed: {side} {quantity} @ {price}")
            return resp.json()
        else:
            print(f"Order error: {resp.text}")
            return None
    except Exception as e:
        print(f"Exception placing order: {e}")
        return None

def ladder_strategy():
    print("Starting combined Ladder Strategy...")

    closes = get_candles()
    if len(closes) < EMA_PERIOD:
        print("Not enough candle data.")
        return

    ema = calculate_ema(closes, EMA_PERIOD)
    last_price = closes[-1]
    print(f"Last price: {last_price}, EMA{EMA_PERIOD}: {ema}")

    # تایید روند: اگر قیمت بالاتر از EMA است، روند صعودی است و فقط خرید پلکانی
    if last_price > ema:
        print("Uptrend confirmed - placing buy ladder orders.")
        for i in range(LADDER_STEPS):
            price = last_price - i * STEP_SIZE
            place_limit_order("BUY", price, ORDER_QUANTITY)
            time.sleep(1)
    # اگر قیمت پایین‌تر از EMA است، روند نزولی است و فقط فروش پلکانی
    elif last_price < ema:
        print("Downtrend confirmed - placing sell ladder orders.")
        for i in range(LADDER_STEPS):
            price = last_price + i * STEP_SIZE
            place_limit_order("SELL", price, ORDER_QUANTITY)
            time.sleep(1)
    else:
        print("Price near EMA - no orders placed.")

if __name__ == "__main__":
    ladder_strategy()
