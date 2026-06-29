from fastapi import FastAPI
import yfinance as yf
import time
from fastapi.middleware.cors import CORSMiddleware
import threading
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CACHE = {}
LAST_FETCH = 0

PORTFOLIO = [
    {"symbol": "YATHARTH.NS", "qty": 8, "avg": 813.80},
    {"symbol": "BDL.NS", "qty": 12, "avg": 1717.50},
    {"symbol": "EMMVEE.NS", "qty": 50, "avg": 215.23},
    {"symbol": "INOXWIND.NS", "qty": 50, "avg": 183.76},
    {"symbol": "PPLPHARMA.NS", "qty": 40, "avg": 204.10},
    {"symbol": "RVNL.NS", "qty": 12, "avg": 349.50},
    {"symbol": "SUZLON.NS", "qty": 136, "avg": 67.86},
    {"symbol": "GREAVESCOT.NS", "qty": 1, "avg": 217.74},
    {"symbol": "EDELWEISS.NS", "qty": 1, "avg": 117.50},
    {"symbol": "VIMTALABS.NS", "qty": 4, "avg": 716.85},
    {"symbol": "NAVKARCORP.NS", "qty": 50, "avg": 100.66},
    {"symbol": "NSLNISP.NS", "qty": 100, "avg": 46.95},    
{"symbol": "ASHOKLEY.NS", "qty": 100, "avg": 143.89},  
    {"symbol": "SIYSIL.NS", "qty": 10, "avg": 633.88},        # Siyaram Silk Mills
{"symbol": "ALLTIME.NS", "qty": 30, "avg": 248.98},       # All Time Plastics
{"symbol": "DCXINDIA.NS", "qty": 25, "avg": 194.70},      # DCX Systems
{"symbol": "MAMATA.NS", "qty": 50, "avg": 372.11},        # Mamata Machinery
{"symbol": "WELSPUNLIV.NS", "qty": 70, "avg": 153.58},    # Welspun Living
{"symbol": "CANBK.NS", "qty": 100, "avg": 133.81},        # Canara Bank
{"symbol": "REDINGTON.NS", "qty": 35, "avg": 245.65},     # Redington      # Redington
]

INDICES = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANK NIFTY": "^NSEBANK",
    "MIDCAP NIFTY": "^NSEMDCP50"
}

@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/portfolio")
def get_portfolio():
    global LAST_FETCH, CACHE

    now = time.time()
    if now - LAST_FETCH < 30 and CACHE:
        return CACHE

    try:
        symbols = [p["symbol"] for p in PORTFOLIO] + list(INDICES.values())
        tickers = yf.Tickers(" ".join(symbols))

        stocks_output = []

        total_invested = 0
        total_current = 0
        total_day_change = 0

        # 🔹 STOCKS
        for stock in PORTFOLIO:
            ticker = tickers.tickers[stock["symbol"]]
            hist = ticker.history(period="5d")

            if len(hist) < 2:
                continue

            prev_close = hist["Close"].iloc[-2]
            price = hist["Close"].iloc[-1]

            qty = stock["qty"]
            avg = stock["avg"]

            invested = qty * avg
            current = qty * price

            change = current - invested
            percent = (change / invested) * 100

            day_change = (price - prev_close)
            day_change_amt = day_change*qty
            day_percent = ((price - prev_close) / prev_close) * 100

            total_invested += invested
            total_current += current
            total_day_change += day_change_amt

            stocks_output.append({
                "symbol": stock["symbol"],
                "qty": qty,
                "avg": avg,
                "price": round(price, 2),
                "invested": round(invested, 2),
                "current": round(current, 2),
                "total_change": round(change, 2),
                "total_percent": round(percent, 2),
                "day_change": round(day_change, 2),
                "day_percent": round(day_percent, 2),
            })

        # 🔹 AGGREGATES
        total_return = total_current - total_invested
        total_percent = (total_return / total_invested) * 100 if total_invested else 0
        total_day_percent = (total_day_change / total_current) * 100 if total_current else 0

        # 🔹 INDICES
        indices_output = []

        for name, symbol in INDICES.items():
            ticker = tickers.tickers[symbol]
            hist = ticker.history(period="5d")

            if len(hist) < 2:
                continue

            prev = hist["Close"].iloc[-2]
            curr = hist["Close"].iloc[-1]

            indices_output.append({
                "name": name,
                "price": round(curr, 2),
                "change": round(curr - prev, 2),
                "percent": round(((curr - prev) / prev) * 100, 2)
            })

        result = {
            "stocks": stocks_output,
            "indices": indices_output,
            "summary": {
                "total_invested": round(total_invested, 2),
                "total_current": round(total_current, 2),
                "total_return": round(total_return, 2),
                "total_percent": round(total_percent, 2),
                "day_change": round(total_day_change, 2),
                "day_percent": round(total_day_percent, 2),
                "wallet": round(total_return + 9527.60, 2),
            }
        }

        CACHE = result
        LAST_FETCH = now

        return result

    except Exception as e:
        if CACHE:
            return CACHE
        return {"error": str(e)}

URL = "https://fin-api-v2.onrender.com/health"

def self_ping():
    while True:
        try:
            res = requests.get(URL, timeout=10)
            print("Ping:", res.status_code)
        except Exception as e:
            print("Ping failed:", e)
        
        time.sleep(300)  # 5 minutes

# run in background
threading.Thread(target=self_ping, daemon=True).start()

@app.get("/health")
def health():
    return {"status": "OK"}

@app.api_route("/", methods=["GET", "HEAD"])
def home():
    return {"status": "ok"}
