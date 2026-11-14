"""Market data for the Portfolio simulator: Yahoo Finance via yfinance, cached with st.cache_data.

Rules
- Prices are always returned in the asset's *major* currency (GBp/GBX/USX... are divided by 100).
- Several tickers are downloaded in one yf.download call whenever possible.
- A ticker that returns no data is logged and skipped; nothing here raises to the page.
Caches: quotes and FX 5 min, history 1 h, ranked universe lists and metadata 24 h.
"""
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
import yfinance as yf

from universe import (COMMODITIES, CRYPTO, ETF_CANDIDATES, STOCK_CANDIDATES, TOP_ETFS, TOP_STOCKS, UCITS)

log = logging.getLogger("stack.market")
logging.getLogger("yfinance").setLevel(logging.CRITICAL)   # yfinance prints its own noisy errors

# Minor-unit currencies Yahoo uses for some listings -> (major currency, divisor)
MINOR_UNITS = {"GBp": ("GBP", 100), "GBX": ("GBP", 100), "USX": ("USD", 100), "ZAc": ("ZAR", 100), "ILA": ("ILS", 100)}


def normalize_currency(cur):
    """Yahoo currency code -> (ISO currency, divisor to apply to prices)."""
    if not cur:
        return "USD", 1
    return MINOR_UNITS.get(cur, (cur.upper(), 1))


def _now():
    return datetime.now().strftime("%H:%M")


def _closes(tickers, **kwargs):
    """Batch-download daily closes. Returns a DataFrame (dates x tickers); tickers without data are dropped."""
    tickers = list(dict.fromkeys(tickers))
    if not tickers:
        return pd.DataFrame()
    try:
        raw = yf.download(tickers, interval="1d", auto_adjust=False, progress=False, threads=True,
                          multi_level_index=True, **kwargs)
    except Exception as exc:  # network error, Yahoo hiccup...
        log.warning("yf.download failed for %s: %s", tickers, exc)
        return pd.DataFrame()
    if raw is None or raw.empty or "Close" not in raw.columns.get_level_values(0):
        log.warning("No data returned for %s", tickers)
        return pd.DataFrame()
    close = raw["Close"]
    if isinstance(close, pd.Series):
        close = close.to_frame(tickers[0])
    close = close.dropna(axis=1, how="all")
    missing = [t for t in tickers if t not in close.columns]
    if missing:
        log.warning("Skipping tickers without price data: %s", ", ".join(missing))
    close.index = pd.to_datetime(close.index).tz_localize(None).normalize()
    return close.sort_index()


# ---------------------------------------------------------------------------
# Metadata (24 h)
# ---------------------------------------------------------------------------
def _parallel(fn, items, workers=8):
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(fn, items))


@st.cache_data(ttl=86_400, show_spinner=False)
def currency_map(tickers):
    """ticker -> (currency, divisor). Uses fast_info (cheap). Unknown tickers default to USD."""
    def one(t):
        try:
            return t, normalize_currency(yf.Ticker(t).fast_info["currency"])
        except Exception as exc:
            log.warning("No currency for %s: %s", t, exc)
            return t, None
    return {t: c for t, c in _parallel(one, list(tickers)) if c}


@st.cache_data(ttl=86_400, show_spinner=False)
def asset_info(tickers):
    """ticker -> {name, currency, divisor, market_cap, total_assets, country, sector}. Failed tickers are skipped."""
    def one(t):
        try:
            info = yf.Ticker(t).info or {}
        except Exception as exc:
            log.warning("No info for %s: %s", t, exc)
            return t, None
        if not info or not (info.get("currency") or info.get("longName") or info.get("shortName")):
            log.warning("Empty info for %s", t)
            return t, None
        cur, div = normalize_currency(info.get("currency"))
        return t, {
            "name": info.get("longName") or info.get("shortName") or t,
            "currency": cur, "divisor": div,
            "market_cap": info.get("marketCap"), "total_assets": info.get("totalAssets"),
            "country": info.get("country"), "sector": info.get("sector"),
        }
    return {t: m for t, m in _parallel(one, list(tickers), workers=6) if m}


# ---------------------------------------------------------------------------
# FX (5 min / 1 h)
# ---------------------------------------------------------------------------
def fx_ticker(cur):
    return f"{cur}CHF=X"


@st.cache_data(ttl=300, show_spinner=False)
def fx_now(currencies):
    """currency -> (CHF per unit now, CHF per unit at previous close). CHF -> (1, 1)."""
    out = {"CHF": (1.0, 1.0)}
    need = [c for c in currencies if c != "CHF"]
    closes = _closes([fx_ticker(c) for c in need], period="7d")
    for c in need:
        s = closes[fx_ticker(c)].dropna() if fx_ticker(c) in closes else pd.Series(dtype=float)
        if s.empty:
            log.warning("No FX rate for %s", c)
            continue
        out[c] = (float(s.iloc[-1]), float(s.iloc[-2]) if len(s) > 1 else float(s.iloc[-1]))
    return out


@st.cache_data(ttl=3_600, show_spinner=False)
def fx_history(currencies, start):
    """Daily CHF-per-unit rates since `start` (ISO date), columns = currencies (CHF column = 1)."""
    need = [c for c in currencies if c != "CHF"]
    closes = _closes([fx_ticker(c) for c in need], start=start)
    out = pd.DataFrame({c: closes[fx_ticker(c)] for c in need if fx_ticker(c) in closes})
    if out.empty:
        out = pd.DataFrame(index=pd.DatetimeIndex([pd.Timestamp(start)]))
    out["CHF"] = 1.0
    return out


# ---------------------------------------------------------------------------
# Prices (5 min / 1 h)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def quotes(tickers):
    """ticker -> {price, prev_close, change_pct, last_date} in major currency, plus '_fetched_at'."""
    cmap = currency_map(tuple(tickers))
    closes = _closes(tickers, period="7d")
    out = {"_fetched_at": _now()}
    for t in tickers:
        if t not in closes:
            continue
        s = closes[t].dropna() / cmap.get(t, ("USD", 1))[1]
        if s.empty:
            continue
        price = float(s.iloc[-1])
        prev = float(s.iloc[-2]) if len(s) > 1 else price
        out[t] = {"price": price, "prev_close": prev, "change_pct": (price / prev - 1) * 100 if prev else 0.0,
                  "last_date": s.index[-1].date().isoformat()}
    return out


@st.cache_data(ttl=3_600, show_spinner=False)
def history(tickers, start):
    """Daily closes (major currency) since `start` (ISO date) for several tickers in one download."""
    cmap = currency_map(tuple(tickers))
    closes = _closes(tickers, start=start)
    for t in closes.columns:
        closes[t] = closes[t] / cmap.get(t, ("USD", 1))[1]
    return closes


@st.cache_data(ttl=3_600, show_spinner=False)
def sparklines(tickers):
    """ticker -> list of ~1 year of closes (weekly points, enough for a sparkline)."""
    closes = _closes(tickers, period="1y")
    return {t: [round(float(v), 6) for v in closes[t].dropna().iloc[::5]] for t in closes.columns}


@st.cache_data(ttl=300, show_spinner=False)
def market_open(ticker, asset_class):
    """True when the exchange is in regular trading hours (crypto is always open)."""
    if asset_class == "crypto":
        return True
    try:
        return (yf.Ticker(ticker).info or {}).get("marketState") == "REGULAR"
    except Exception as exc:
        log.warning("No market state for %s: %s", ticker, exc)
        return False


def refresh_prices():
    """'Refresh prices' button: drop the short-lived caches (quotes, FX, history, market state)."""
    for fn in (quotes, fx_now, history, fx_history, market_open, sparklines):
        fn.clear()


# ---------------------------------------------------------------------------
# Universe lists (24 h)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=86_400, show_spinner=False)
def top_stocks():
    """Top 50 candidates by current market cap converted to USD."""
    info = asset_info(tuple(STOCK_CANDIDATES))
    fx = fx_now(tuple(sorted({m["currency"] for m in info.values()} | {"USD"})))
    usd = fx["USD"][0]
    rows = []
    for t in STOCK_CANDIDATES:
        m = info.get(t)
        if not m or not m["market_cap"] or m["currency"] not in fx:
            log.warning("Skipping %s: no market cap", t)
            continue
        cap_usd = m["market_cap"] * fx[m["currency"]][0] / usd      # local currency -> CHF -> USD
        rows.append({"ticker": t, "name": m["name"], "currency": m["currency"], "size_usd": cap_usd,
                     "country": m["country"], "sector": m["sector"], "tag": ""})
    rows.sort(key=lambda r: r["size_usd"], reverse=True)
    return {"rows": rows[:TOP_STOCKS], "fetched_at": _now(), "date": date.today().isoformat()}


@st.cache_data(ttl=86_400, show_spinner=False)
def top_etfs():
    """Top 30 candidates by totalAssets. Yahoo publishes no AUM for some European listings: those are
    listed after the ranked funds (tag 'AUM n/a') instead of being silently dropped."""
    info = asset_info(tuple(ETF_CANDIDATES))
    ranked, unranked = [], []
    for t in ETF_CANDIDATES:
        m = info.get(t)
        if not m:
            continue
        row = {"ticker": t, "name": m["name"], "currency": m["currency"], "size_usd": m["total_assets"],
               "country": None, "sector": None, "tag": "UCITS" if t in UCITS else ""}
        (ranked if m["total_assets"] else unranked).append(row)
    ranked.sort(key=lambda r: r["size_usd"], reverse=True)
    for r in unranked:
        r["tag"] = (r["tag"] + " · AUM n/a").strip(" ·")
    return {"rows": ranked[:TOP_ETFS] + unranked, "fetched_at": _now(), "date": date.today().isoformat()}


def fixed_list(names):
    cmap = currency_map(tuple(names))
    rows = [{"ticker": t, "name": n, "currency": cmap[t][0], "size_usd": None, "country": None, "sector": None, "tag": ""}
            for t, n in names.items() if t in cmap]
    return {"rows": rows, "fetched_at": _now(), "date": date.today().isoformat()}


def universe(asset_class):
    if asset_class == "stock":
        return top_stocks()
    if asset_class == "etf":
        return top_etfs()
    return fixed_list(COMMODITIES if asset_class == "commodity" else CRYPTO)


def start_of_range(code, today=None):
    """'1W'/'1M'/'6M'/'1Y'/'5Y' -> start date."""
    today = today or date.today()
    days = {"1W": 7, "1M": 31, "6M": 183, "1Y": 366, "5Y": 5 * 366}[code]
    return today - timedelta(days=days)


# ---------------------------------------------------------------------------
# Global search (10 min)
# ---------------------------------------------------------------------------
# Yahoo quoteType -> app asset class. Other types (options, indices, currencies...) are not tradable here.
QUOTE_TYPES = {"EQUITY": ("stock", "Equity"), "ETF": ("etf", "ETF"), "MUTUALFUND": ("etf", "Fund"),
               "FUTURE": ("commodity", "Future"), "CRYPTOCURRENCY": ("crypto", "Crypto")}
# Friendlier names for Yahoo's exchange labels (anything else is shown as Yahoo gives it).
EXCHANGES = {"Swiss": "SIX Swiss", "Milan": "Borsa Italiana", "NasdaqGS": "NASDAQ", "NasdaqGM": "NASDAQ", "NasdaqCM": "NASDAQ",
             "NYSEArca": "NYSE Arca", "Paris": "Euronext Paris", "Amsterdam": "Euronext Amsterdam", "Brussels": "Euronext Brussels",
             "Lisbon": "Euronext Lisbon", "XETRA": "Xetra", "Frankfurt": "Frankfurt", "LSE": "London SE", "London": "London SE",
             "CCC": "Crypto", "CCY": "FX", "HKSE": "Hong Kong", "Tokyo": "Tokyo", "KSE": "Korea", "Saudi": "Tadawul",
             "Copenhagen": "Nasdaq Copenhagen", "Stockholm": "Nasdaq Stockholm", "OID": "OTC", "PNK": "OTC",
             "New York Commodity Exchange": "COMEX", "Chicago Mercantile Exchange": "CME", "NY Mercantile": "NYMEX"}
SEARCH_LIMIT = 10


def _universe_matches(query):
    """Our own lists first: fixed commodity/crypto names, and stock/ETF candidates by ticker."""
    q = query.strip().lower()
    out = []
    for names, cls, typ in ((COMMODITIES, "commodity", "Future"), (CRYPTO, "crypto", "Crypto")):
        out += [{"ticker": t, "name": n, "cls": cls, "type": typ, "exchange": "Crypto" if cls == "crypto" else "Futures"}
                for t, n in names.items() if q in n.lower() or q == t.lower()]
    for cands, cls, typ in ((STOCK_CANDIDATES, "stock", "Equity"), (ETF_CANDIDATES, "etf", "ETF")):
        out += [{"ticker": t, "name": t, "cls": cls, "type": typ, "exchange": ""} for t in cands
                if q == t.lower() or (len(q) >= 2 and t.lower().startswith(q))]
    return out


def _yahoo_matches(query):
    """yf.Search; if that is unavailable or fails, try the text as a ticker. Returns (results, error)."""
    try:
        quotes = yf.Search(query, max_results=SEARCH_LIMIT, news_count=0).quotes
    except Exception as exc:          # older yfinance without Search, or Yahoo error
        log.warning("yf.Search failed for %r: %s", query, exc)
        quotes = None
    if quotes is None:
        t = query.strip().upper()
        try:
            yf.Ticker(t).fast_info["lastPrice"]
            quotes = [{"symbol": t, "quoteType": "EQUITY", "exchDisp": ""}]
        except Exception as exc:
            log.warning("Direct ticker lookup failed for %r: %s", t, exc)
            return [], "Yahoo Finance is not responding right now. Please try again in a minute."
    out = []
    for x in quotes:
        kind = QUOTE_TYPES.get(str(x.get("quoteType", "")).upper())
        if not kind or not x.get("symbol"):
            continue
        exch = x.get("exchDisp") or x.get("exchange") or ""
        out.append({"ticker": x["symbol"], "name": x.get("longname") or x.get("shortname") or x["symbol"],
                    "cls": kind[0], "type": kind[1], "exchange": EXCHANGES.get(exch, exch)})
    return out, None


@st.cache_data(ttl=600, show_spinner=False)
def search(query):
    """Up to 10 tradable matches with a live price: {"results": [...], "error": str | None}.
    Each result: ticker, name, cls, type, exchange, currency, price, change_pct. Results without a price are dropped."""
    query = (query or "").strip()
    if len(query) < 2:
        return {"results": [], "error": None}
    found, error = _yahoo_matches(query)
    merged, seen = [], set()
    for r in _universe_matches(query) + found:
        if r["ticker"] not in seen:
            seen.add(r["ticker"])
            merged.append(r)
    merged = merged[:SEARCH_LIMIT * 2]
    if not merged:
        return {"results": [], "error": error}
    tickers = tuple(r["ticker"] for r in merged)
    q = quotes(tickers)
    cmap = currency_map(tickers)
    names = {}
    if any(r["name"] == r["ticker"] for r in merged):     # universe hits found by ticker: get a readable name
        names = {t: m["name"] for t, m in asset_info(tuple(r["ticker"] for r in merged if r["name"] == r["ticker"])).items()}
    results = []
    for r in merged:
        if r["ticker"] not in q or r["ticker"] not in cmap:
            log.info("Search: dropping %s (no price)", r["ticker"])
            continue
        results.append({**r, "name": names.get(r["ticker"], r["name"]), "currency": cmap[r["ticker"]][0],
                        "price": q[r["ticker"]]["price"], "change_pct": q[r["ticker"]]["change_pct"]})
    return {"results": results[:SEARCH_LIMIT], "error": None if results else error}
