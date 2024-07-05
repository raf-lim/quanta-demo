import requests
import asyncio


JSON = str | int | float | bool | None | dict[str, 'JSON'] | list['JSON']


def http_get_sync(url: str) -> JSON:
    with requests.Session() as session:
        response = session.get(url, timeout=None)
        response.raise_for_status()
        return response.json()
    

async def http_get(url: str) -> JSON:
    return await asyncio.to_thread(http_get_sync, url)

