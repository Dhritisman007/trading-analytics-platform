# services/options/nse_fetcher.py

import requests
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# NSE requires a session with cookies from the main page
NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept":          "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer":         "https://www.nseindia.com/option-chain",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua":       '"Chromium";v="122"',
    "sec-fetch-dest":  "empty",
    "sec-fetch-mode":  "cors",
    "sec-fetch-site":  "same-origin",
}

NSE_URLS = {
    "main":        "https://www.nseindia.com",
    "option_chain": "https://www.nseindia.com/option-chain",
    "nifty_oc":    "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",
    "banknifty_oc": "https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY",
    "finnifty_oc": "https://www.nseindia.com/api/option-chain-indices?symbol=FINNIFTY",
}


def _create_nse_session() -> requests.Session:
    """
    Create an authenticated NSE session.
    NSE blocks direct API calls — you must visit the main page
    first to get cookies, then use those cookies for API requests.
    """
    session = requests.Session()
    session.headers.update(NSE_HEADERS)

    try:
        # Step 1: Visit main page to get initial cookies
        session.get(NSE_URLS["main"], timeout=10)
        time.sleep(0.5)

        # Step 2: Visit option chain page to get additional cookies
        session.get(NSE_URLS["option_chain"], timeout=10)
        time.sleep(0.5)

        logger.debug("NSE session created successfully")
    except Exception as e:
        logger.warning(f"NSE session creation issue: {e}")

    return session


def fetch_option_chain_raw(symbol: str = "NIFTY") -> dict:
    """
    Fetch raw option chain data from NSE.

    Args:
        symbol: NIFTY, BANKNIFTY, or FINNIFTY

    Returns:
        Raw JSON response from NSE API
    """
    symbol = symbol.upper().replace("^NSEI", "NIFTY").replace("^NSEBANK", "BANKNIFTY")

    url_map = {
        "NIFTY":     NSE_URLS["nifty_oc"],
        "BANKNIFTY": NSE_URLS["banknifty_oc"],
        "FINNIFTY":  NSE_URLS["finnifty_oc"],
    }

    url = url_map.get(symbol, NSE_URLS["nifty_oc"])

    session = _create_nse_session()

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"NSE API HTTP error: {e}")
        raise ValueError(f"NSE API returned error for {symbol}: {e}")
    except Exception as e:
        logger.error(f"NSE API fetch failed: {e}")
        raise ValueError(f"Failed to fetch option chain for {symbol}: {e}")
    finally:
        session.close()