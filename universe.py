"""Asset universe for the Portfolio simulator.

Stocks and ETFs are *candidate* lists: market_data.py ranks them live (market cap / total assets
from Yahoo Finance) and keeps the top 50 / top 30. Commodities and crypto are fixed lists.
"""

STOCK_CANDIDATES = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "AVGO", "TSLA", "BRK-B", "TSM", "2222.SR", "LLY", "JPM",
    "WMT", "V", "ORCL", "MA", "XOM", "UNH", "COST", "NFLX", "PG", "JNJ", "HD", "BAC", "ABBV", "005930.KS",
    "0700.HK", "ASML", "SAP", "NESN.SW", "NOVO-B.CO", "ROG.SW", "NOVN.SW", "MC.PA", "RMS.PA", "OR.PA", "KO",
    "PLTR", "AMD", "CVX", "CRM", "WFC", "CSCO", "IBM", "TM", "PM", "LIN", "MCD", "ABT", "GE", "MS", "AXP",
    "GS", "1398.HK", "AZN", "SHEL", "HSBC", "TMUS", "DIS", "INTU", "NOW", "UBSG.SW",
]
TOP_STOCKS = 50

ETF_CANDIDATES = [
    "SPY", "IVV", "VOO", "VTI", "QQQ", "VEA", "IEFA", "VUG", "VTV", "BND", "AGG", "IWF", "IEMG", "VXUS", "VGT",
    "IJH", "VWO", "VIG", "IJR", "GLD", "XLK", "VO", "SCHD", "IWM", "RSP", "BNDX", "EFA", "IWD", "URTH",
    "SWDA.L", "CSPX.L", "VWCE.DE", "EUNL.DE", "IUSQ.DE", "CHSPI.SW",
]
TOP_ETFS = 30
# European-domiciled (UCITS) listings get a "UCITS" tag.
UCITS = {"SWDA.L", "CSPX.L", "VWCE.DE", "EUNL.DE", "IUSQ.DE", "CHSPI.SW"}

COMMODITIES = {
    "GC=F": "Gold", "SI=F": "Silver", "PL=F": "Platinum", "PA=F": "Palladium", "HG=F": "Copper",
    "ALI=F": "Aluminium", "CL=F": "WTI crude oil", "BZ=F": "Brent crude oil", "NG=F": "Natural gas",
    "RB=F": "Gasoline", "HO=F": "Heating oil", "ZC=F": "Corn", "ZW=F": "Wheat", "ZS=F": "Soybeans",
    "KC=F": "Coffee", "SB=F": "Sugar", "CC=F": "Cocoa", "CT=F": "Cotton", "LE=F": "Live cattle", "HE=F": "Lean hogs",
}

CRYPTO = {
    "BTC-USD": "Bitcoin", "ETH-USD": "Ether", "SOL-USD": "Solana", "XRP-USD": "XRP", "BNB-USD": "BNB",
    "ADA-USD": "Cardano", "DOGE-USD": "Dogecoin", "AVAX-USD": "Avalanche", "LINK-USD": "Chainlink", "DOT-USD": "Polkadot",
}

# Asset classes (key -> display label). "cash" is only used in allocation charts.
CLASSES = {"stock": "Stocks", "etf": "ETFs", "commodity": "Commodities", "crypto": "Crypto", "cash": "Cash"}

# Benchmark used for the "compare with MSCI World" overlay and the "Beat the market" badge.
BENCHMARK = "URTH"
BENCHMARK_NAME = "MSCI World (URTH)"

COMMODITY_NOTE = (
    "Simplified: you buy a CHF \"exposure\" that follows the futures price. There are no contracts, leverage, "
    "margin or expiry dates here. Real futures work very differently and can lose more than the money put in."
)
