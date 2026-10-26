"""HTTP with bounded retries, timeouts and a polite delay. stdlib only."""
from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request

log = logging.getLogger("nbapicks.http")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
RETRY_STATUS = {429, 500, 502, 503, 504}


class FetchError(Exception):
    def __init__(self, url: str, status: int | None, detail: str):
        super().__init__(f"{url}: {status} {detail}")
        self.url, self.status, self.detail = url, status, detail


def get_json(url: str, *, retries: int = 3, timeout: float = 25, backoff: float = 2.0,
             min_interval: float = 0.0, opener=None) -> dict:
    """GET and decode JSON. Retries network errors and 429/5xx with exponential backoff
    (2s, 4s, 8s by default; honours Retry-After up to 60s). Raises FetchError."""
    opener = opener or urllib.request.urlopen
    last: FetchError | None = None
    for attempt in range(retries + 1):
        if min_interval:
            time.sleep(min_interval)
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json",
                                                   "Accept-Encoding": "identity"})
        try:
            with opener(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            last = FetchError(url, e.code, e.reason)
            if e.code not in RETRY_STATUS:
                raise last
            wait = backoff * 2 ** attempt
            ra = e.headers.get("Retry-After") if e.headers else None
            if ra and ra.isdigit():
                wait = min(60, max(wait, int(ra)))
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = FetchError(url, None, repr(e))
            wait = backoff * 2 ** attempt
        except json.JSONDecodeError as e:
            raise FetchError(url, 200, f"invalid JSON: {e}")
        if attempt < retries:
            log.warning("retry %s in %.0fs: %s", url, wait, last)
            time.sleep(wait)
    raise last  # type: ignore[misc]
