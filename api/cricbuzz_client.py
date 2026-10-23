"""Thin, retrying client for the Cricbuzz Cricket API on RapidAPI.

Endpoint paths follow the public RapidAPI listing; confirm them against your own
subscription page, since RapidAPI providers can change them.
"""
import logging
import time

import requests

import config
from api import demo_payloads

log = logging.getLogger(__name__)


class CricbuzzAPIError(Exception):
    """Raised for any non-recoverable API problem."""


class RateLimitError(CricbuzzAPIError):
    """HTTP 429 after all retries were used."""


class CricbuzzClient:
    ENDPOINTS = {
        "live": "/matches/v1/live",
        "recent": "/matches/v1/recent",
        "upcoming": "/matches/v1/upcoming",
        "scorecard": "/mcenter/v1/{match_id}/scard",
        "match_info": "/mcenter/v1/{match_id}",
        "top_stats": "/stats/v1/topstats/0",
        "player": "/stats/v1/player/{player_id}",
        "teams": "/teams/v1/international",
        "series": "/series/v1/international",
    }
    RETRY_STATUS = {429, 500, 502, 503, 504}

    def __init__(self, api_key=None, host=None, session=None, demo=None, sleep=time.sleep):
        self.api_key = api_key if api_key is not None else config.RAPIDAPI_KEY
        self.host = host or config.RAPIDAPI_HOST
        self.session = session or requests.Session()
        self.demo = config.USE_DEMO_API if demo is None else demo
        self._sleep = sleep

    @property
    def headers(self):
        return {"x-rapidapi-key": self.api_key, "x-rapidapi-host": self.host}

    def _get(self, key, params=None, **path):
        """GET with timeout, retry + exponential backoff, and JSON validation."""
        if self.demo:
            return demo_payloads.get(key)
        url = f"https://{self.host}" + self.ENDPOINTS[key].format(**path)
        last = None
        for attempt in range(1, config.API_MAX_RETRIES + 1):
            try:
                resp = self.session.get(url, headers=self.headers, params=params, timeout=config.API_TIMEOUT)
            except (requests.ConnectionError, requests.Timeout) as exc:
                last = exc
                log.warning("Attempt %s failed (%s)", attempt, exc)
            else:
                if resp.status_code == 200:
                    try:
                        return resp.json()
                    except ValueError as exc:
                        raise CricbuzzAPIError(f"Invalid JSON from {url}") from exc
                if resp.status_code in (401, 403):
                    raise CricbuzzAPIError("API key rejected: check RAPIDAPI_KEY and your subscription")
                if resp.status_code not in self.RETRY_STATUS:
                    raise CricbuzzAPIError(f"HTTP {resp.status_code} from {url}")
                last = RateLimitError("Rate limit hit") if resp.status_code == 429 else CricbuzzAPIError(f"HTTP {resp.status_code}")
            if attempt < config.API_MAX_RETRIES:
                self._sleep(config.API_BACKOFF_SECONDS * 2 ** (attempt - 1))
        if isinstance(last, CricbuzzAPIError):
            raise last
        raise CricbuzzAPIError(f"Network failure after retries: {last}")

    def live_matches(self):
        return self._get("live")

    def recent_matches(self):
        return self._get("recent")

    def upcoming_matches(self):
        return self._get("upcoming")

    def scorecard(self, match_id):
        return self._get("scorecard", match_id=match_id)

    def top_stats(self, stats_type="mostRuns", match_format=None):
        params = {"statsType": stats_type}
        if match_format:
            params["matchType"] = match_format
        return self._get("top_stats", params=params)

    def player(self, player_id):
        return self._get("player", player_id=player_id)
