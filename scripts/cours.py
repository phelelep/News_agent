#!/usr/bin/env python3
"""Cours des tickers de watchlist.md.

Sans option : tableau Markdown, à coller sous « ## Cours » dans le rapport.
--json : mêmes données pour le site.
Code de sortie 1 si aucun cours n'a pu être récupéré.
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WATCHLIST = Path(__file__).resolve().parent.parent / "watchlist.md"
CRYPTO_IDS = {"BTC": "bitcoin", "ETH": "ethereum"}
LINE = re.compile(r"^- (.+?) \(([A-Z0-9.\-]+)\)")
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def fetch_json(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def read_watchlist():
    return [m.groups() for m in map(LINE.match, WATCHLIST.read_text(encoding="utf-8").splitlines()) if m]


def stock_quote(name, ticker):
    """Dernière clôture et variation calculée sur les deux dernières clôtures."""
    symbol = urllib.parse.quote(ticker)
    data = fetch_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=7d&interval=1d")
    result = data["chart"]["result"][0]
    closes = result["indicators"]["quote"][0]["close"]
    days = [(t, c) for t, c in zip(result["timestamp"], closes) if c is not None]
    (_, previous), (last_time, last) = days[-2], days[-1]
    return {
        "nom": name,
        "ticker": ticker,
        "prix": round(last, 2),
        "variation": round((last / previous - 1) * 100, 2),
        "devise": result["meta"].get("currency", "USD"),
        "date": datetime.fromtimestamp(last_time, timezone.utc).strftime("%Y-%m-%d"),
    }


def crypto_quotes(entries):
    ids = ",".join(CRYPTO_IDS[ticker] for _, ticker in entries)
    data = fetch_json(
        "https://api.coingecko.com/api/v3/simple/price"
        f"?ids={ids}&vs_currencies=usd&include_24hr_change=true"
    )
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return [
        {
            "nom": name,
            "ticker": ticker,
            "prix": round(data[CRYPTO_IDS[ticker]]["usd"], 2),
            "variation": round(data[CRYPTO_IDS[ticker]]["usd_24h_change"], 2),
            "devise": "USD",
            "date": today,
        }
        for name, ticker in entries
    ]


def collect():
    entries = read_watchlist()
    quotes, missing = [], []
    for name, ticker in entries:
        if ticker in CRYPTO_IDS:
            continue
        try:
            quotes.append(stock_quote(name, ticker))
        except Exception as error:
            missing.append(ticker)
            print(f"{ticker} : {error}", file=sys.stderr)
    crypto = [(name, ticker) for name, ticker in entries if ticker in CRYPTO_IDS]
    try:
        quotes += crypto_quotes(crypto)
    except Exception as error:
        missing += [ticker for _, ticker in crypto]
        print(f"crypto : {error}", file=sys.stderr)
    return quotes, missing


def fr_number(value):
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")


def markdown(quotes, missing):
    lines = ["| Actif | Ticker | Cours | Var. | Date |", "|---|---|---:|---:|---|"]
    for q in quotes:
        lines.append(
            f"| {q['nom']} | {q['ticker']} | {fr_number(q['prix'])} {q['devise']} "
            f"| {q['variation']:+.2f} % | {q['date']} |".replace(".", ",", 0)
        )
    if missing:
        lines += ["", f"Cours indisponibles : {', '.join(missing)}."]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    quotes, missing = collect()
    if not quotes:
        print("Aucun cours récupéré.", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"cours": quotes, "manquants": missing}, ensure_ascii=False))
    else:
        print(markdown(quotes, missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
