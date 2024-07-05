from typing import Iterable, Callable
import logging
import requests

from api import http_get

logging.basicConfig(level=logging.INFO)


def get_raw_financial_data(
        all_tickers: Iterable[str],
        url_fn: Callable[[str, int], str],
        fs_limit: int
    ) -> list[list[dict]]:
    """Get financial statement section."""
    data: list[list[dict]] = []
    for ticker in all_tickers:
        try:
            response_data = http_get.http_get_sync(
                url_fn(symbol=ticker, limit=fs_limit)
            )
            data.append(response_data)
        except (requests.exceptions.HTTPError, AttributeError):
            continue
    
    return data