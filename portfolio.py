"""Portfolio maths for the virtual-money simulator (no Streamlit, no network: easy to test).

Data model (stored in progress.json under "portfolio"):
  cash_flows: [{"ts": ISO datetime, "kind": "deposit" | "withdrawal", "amount": CHF}]
  trades:     [{"ts", "ticker", "name", "cls", "currency", "side": "buy" | "sell", "qty",
                "price": native major-currency price, "fx": CHF per unit, "gross_chf", "fee_chf"}]
  settings:   {"fee_pct": 0.1}
  earned:     badge keys already unlocked (kept even if the position is sold later)

Conventions
- Cost basis uses the average-cost method, in CHF, fees included (PRU = cost / quantity).
- External flows (deposits / withdrawals) are never counted as gains.
- Time-weighted return (TWR): daily sub-period returns r_t = V_t / (V_{t-1} + F_t) - 1, where F_t is the
  net external flow of day t (assumed at the start of the day), chained geometrically.
"""
from datetime import date, datetime, timedelta

import pandas as pd

EPS = 1e-9
INVEST_CLASSES = ("stock", "etf", "commodity", "crypto")


def new_portfolio():
    return {"cash_flows": [], "trades": [], "settings": {"fee_pct": 0.1}, "earned": []}


def fmt_chf(x, dec=2):
    """CHF 1'234.56 (Swiss thousands separator)."""
    return f"CHF {x:,.{dec}f}".replace(",", "'")


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def _day(ts):
    return pd.Timestamp(ts[:10])


# ---------------------------------------------------------------------------
# Cash, flows, positions
# ---------------------------------------------------------------------------
def net_invested(pf):
    return sum(f["amount"] if f["kind"] == "deposit" else -f["amount"] for f in pf["cash_flows"])


def cash(pf):
    c = net_invested(pf)
    for t in pf["trades"]:
        c += -(t["gross_chf"] + t["fee_chf"]) if t["side"] == "buy" else t["gross_chf"] - t["fee_chf"]
    return c


def total_fees(pf):
    return sum(t["fee_chf"] for t in pf["trades"])


def positions(pf):
    """ticker -> open position (qty, cost basis in CHF and native currency, open_since...)."""
    pos, realized = {}, 0.0
    for t in sorted(pf["trades"], key=lambda x: x["ts"]):
        p = pos.setdefault(t["ticker"], {"ticker": t["ticker"], "name": t["name"], "cls": t["cls"],
                                         "currency": t["currency"], "qty": 0.0, "cost_chf": 0.0,
                                         "cost_native": 0.0, "open_since": None})
        if t["side"] == "buy":
            if p["qty"] <= EPS:
                p["open_since"] = t["ts"]
            p["qty"] += t["qty"]
            p["cost_chf"] += t["gross_chf"] + t["fee_chf"]
            p["cost_native"] += t["qty"] * t["price"]
        else:
            frac = min(t["qty"] / p["qty"], 1.0) if p["qty"] > EPS else 1.0
            removed = p["cost_chf"] * frac
            realized += t["gross_chf"] - t["fee_chf"] - removed
            p["cost_chf"] -= removed
            p["cost_native"] -= p["cost_native"] * frac
            p["qty"] -= t["qty"]
            if p["qty"] <= EPS:
                p.update(qty=0.0, cost_chf=0.0, cost_native=0.0, open_since=None)
    return {k: v for k, v in pos.items() if v["qty"] > EPS}, realized


def held_qty(pf, ticker):
    return positions(pf)[0].get(ticker, {}).get("qty", 0.0)


def value_positions(pos, quotes, fx):
    """Add live price / value / P&L to each open position. Positions without a quote keep their cost."""
    rows = []
    for p in pos.values():
        q = quotes.get(p["ticker"])
        rate = fx.get(p["currency"], (None, None))[0]
        if q and rate:
            price, value = q["price"], p["qty"] * q["price"] * rate
            change = q["change_pct"]
        else:
            price, value, change = None, p["cost_chf"], 0.0
        pnl = value - p["cost_chf"]
        rows.append({**p, "price": price, "value_chf": value, "pnl_chf": pnl,
                     "pnl_pct": pnl / p["cost_chf"] * 100 if p["cost_chf"] else 0.0,
                     "pru_chf": p["cost_chf"] / p["qty"], "pru_native": p["cost_native"] / p["qty"],
                     "day_pct": change})
    total = sum(r["value_chf"] for r in rows)
    for r in rows:
        r["weight_pct"] = r["value_chf"] / total * 100 if total else 0.0
    return rows


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------
def preview_order(pf, side, ticker, price, fx_rate, qty=None, amount_chf=None, fmt=None):
    """Work out an order before it is confirmed. Give either qty or amount_chf (order value before fees).
    Returns a dict with qty, gross_chf, fee_chf, total_chf (cash change) and error (None if OK)."""
    fmt = fmt or fmt_chf          # the app passes its own formatter (display currency)
    fee_rate = pf["settings"].get("fee_pct", 0.0) / 100
    unit_chf = price * fx_rate
    if qty is None:
        qty = (amount_chf or 0) / unit_chf if unit_chf else 0
    gross = qty * unit_chf
    fee = gross * fee_rate
    out = {"qty": qty, "gross_chf": gross, "fee_chf": fee, "unit_chf": unit_chf, "error": None}
    if qty <= EPS:
        out["error"] = "Enter an amount or a quantity greater than zero."
    elif side == "buy":
        out["total_chf"] = gross + fee
        if gross + fee > cash(pf) + 1e-6:
            out["error"] = (f"Not enough cash: this order needs {fmt(gross + fee)} including fees, "
                            f"you have {fmt(cash(pf))}.")
    else:
        out["total_chf"] = gross - fee
        held = held_qty(pf, ticker)
        if qty > held + 1e-9:
            out["error"] = f"You only hold {held:.6g} units."
    return out


def record_trade(pf, side, asset, preview, price, fx_rate, ts=None):
    pf["trades"].append({
        "ts": ts or now_iso(), "ticker": asset["ticker"], "name": asset["name"], "cls": asset["cls"],
        "currency": asset["currency"], "side": side, "qty": preview["qty"], "price": price, "fx": fx_rate,
        "gross_chf": preview["gross_chf"], "fee_chf": preview["fee_chf"],
    })


def record_flow(pf, kind, amount, ts=None):
    pf["cash_flows"].append({"ts": ts or now_iso(), "kind": kind, "amount": float(amount)})


# ---------------------------------------------------------------------------
# History, TWR, benchmark
# ---------------------------------------------------------------------------
def first_day(pf):
    stamps = [f["ts"] for f in pf["cash_flows"]] + [t["ts"] for t in pf["trades"]]
    return _day(min(stamps)) if stamps else None


def value_history(pf, closes, fx_hist, live_quotes=None, live_fx=None, today=None):
    """Daily portfolio value in CHF from the first flow to today.

    closes: DataFrame of daily closes (major currency), columns = tickers.
    fx_hist: DataFrame of CHF-per-unit rates, columns = currencies.
    live_quotes / live_fx: today's prices replace today's (possibly missing) close.
    Returns a DataFrame indexed by day with: value, cash, holdings, flow (net external flow), invested, ret.
    """
    start = first_day(pf)
    if start is None:
        return pd.DataFrame()
    today = pd.Timestamp(today or date.today())
    days = pd.date_range(start, max(today, start), freq="D")

    tickers = sorted({t["ticker"] for t in pf["trades"]})
    cur_of = {t["ticker"]: t["currency"] for t in pf["trades"]}
    px = closes.reindex(columns=tickers).reindex(days.union(closes.index)).ffill().reindex(days) if tickers else pd.DataFrame(index=days)
    fx = fx_hist.reindex(days.union(fx_hist.index)).ffill().reindex(days)
    if live_quotes:
        for t in tickers:
            if t in live_quotes:
                px.loc[today, t] = live_quotes[t]["price"]
    if live_fx:
        for c, (rate, _) in live_fx.items():
            fx.loc[today, c] = rate
    # A trade price fills any gap before the first available close (e.g. bought before data starts).
    for t in pf["trades"]:
        d = _day(t["ts"])
        if pd.isna(px.at[d, t["ticker"]]):
            px.loc[d:, t["ticker"]] = px.loc[d:, t["ticker"]].fillna(t["price"])
        cur = t["currency"]
        if cur not in fx.columns:
            fx[cur] = float("nan")
        if pd.isna(fx.at[d, cur]):
            fx.loc[d:, cur] = fx.loc[d:, cur].fillna(t["fx"])

    flow = pd.Series(0.0, index=days)
    cash_delta = pd.Series(0.0, index=days)
    for f in pf["cash_flows"]:
        amt = f["amount"] if f["kind"] == "deposit" else -f["amount"]
        flow[_day(f["ts"])] += amt
        cash_delta[_day(f["ts"])] += amt
    qty = pd.DataFrame(0.0, index=days, columns=tickers)
    for t in pf["trades"]:
        d, sign = _day(t["ts"]), 1 if t["side"] == "buy" else -1
        qty.at[d, t["ticker"]] += sign * t["qty"]
        cash_delta[d] += -(t["gross_chf"] + t["fee_chf"]) if sign > 0 else t["gross_chf"] - t["fee_chf"]
    qty = qty.cumsum().clip(lower=0)

    holdings = pd.Series(0.0, index=days)
    for t in tickers:
        holdings += (qty[t] * px[t] * fx[cur_of[t]]).fillna(0.0)
    out = pd.DataFrame({"cash": cash_delta.cumsum(), "holdings": holdings, "flow": flow})
    out["value"] = out["cash"] + out["holdings"]
    out["invested"] = flow.cumsum()
    base = out["value"].shift(1, fill_value=0.0) + out["flow"]
    out["ret"] = (out["value"] / base - 1).where(base > EPS, 0.0)
    return out


def twr(hist, since=None):
    """Time-weighted return (fraction) over the days after `since` (all history if None)."""
    if hist.empty:
        return 0.0
    r = hist["ret"] if since is None else hist.loc[hist.index > pd.Timestamp(since), "ret"]
    return float((1 + r).prod() - 1)


def benchmark_history(hist, bench_chf):
    """Same deposits/withdrawals invested in the benchmark (bench_chf: daily CHF price series)."""
    if hist.empty or bench_chf is None or bench_chf.dropna().empty:
        return None
    p = bench_chf.reindex(hist.index.union(bench_chf.index)).ffill().bfill().reindex(hist.index)
    units = (hist["flow"] / p).cumsum()
    return pd.DataFrame({"value": units * p, "price": p})


def bench_return(bench, since=None):
    if bench is None or bench.empty:
        return 0.0
    p = bench["price"] if since is None else bench.loc[bench.index >= pd.Timestamp(since), "price"]
    return float(p.iloc[-1] / p.iloc[0] - 1) if len(p) > 1 else 0.0


def day_change(hist):
    """(CHF, %) change today, excluding today's deposits/withdrawals."""
    if len(hist) == 0:
        return 0.0, 0.0
    v = hist["value"].iloc[-1]
    prev = hist["value"].iloc[-2] if len(hist) > 1 else 0.0
    base = prev + hist["flow"].iloc[-1]
    chg = v - base
    return chg, (chg / base * 100 if base > EPS else 0.0)


# ---------------------------------------------------------------------------
# Allocation, rankings, badges
# ---------------------------------------------------------------------------
def allocation(rows, cash_chf, key, cash_label=None):
    out = {}
    for r in rows:
        k = r.get(key) or "Other"
        out[k] = out.get(k, 0.0) + r["value_chf"]
    if cash_label and cash_chf > EPS:
        out[cash_label] = out.get(cash_label, 0.0) + cash_chf
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def top_flop(rows, n=3):
    """Best and worst positions by P&L %; a position never appears in both lists."""
    ranked = sorted(rows, key=lambda r: r["pnl_pct"], reverse=True)
    top = ranked[:n]
    flop = [r for r in reversed(ranked) if r not in top][:n]
    return top, flop


def badge_status(pf, hist=None, bench=None, today=None):
    """Which portfolio badges are earned right now (keys)."""
    today = today or date.today()
    pos, _ = positions(pf)
    earned = set()
    if any(t["side"] == "buy" for t in pf["trades"]):
        earned.add("first_trade")
    if len({p["cls"] for p in pos.values()} & set(INVEST_CLASSES)) >= 4:
        earned.add("diversified")
    if len({p["currency"] for p in pos.values()}) >= 3:
        earned.add("global")
    if any(p["open_since"] and date.fromisoformat(p["open_since"][:10]) <= today - timedelta(days=30) for p in pos.values()):
        earned.add("long_term")
    start = first_day(pf)
    if hist is not None and not hist.empty and bench is not None and start is not None \
            and start.date() <= today - timedelta(days=30):
        since = today - timedelta(days=30)
        if twr(hist, since) > bench_return(bench, since):
            earned.add("beat_market")
    return earned
