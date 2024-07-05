from typing import Iterable


def clean_period_tickers(
        period_tickers: dict[str, Iterable[str]],
        tickers_to_remove: list[str]) -> dict[str, Iterable[str]]:
    """Remove selected tickers from period lists."""
    cleaned_period_tickers = {}
    for date, tickers in period_tickers.items():
        for excl_ticker in tickers_to_remove:
            try:
                tickers.remove(excl_ticker)
            except ValueError:
                continue
        cleaned_period_tickers[date] = tickers
    
    return cleaned_period_tickers
