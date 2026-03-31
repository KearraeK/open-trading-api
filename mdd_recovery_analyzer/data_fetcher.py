"""데이터 수집 모듈: yfinance로 주가/VIX, alternative.me API로 공포탐욕지수 수집."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import requests
import yfinance as yf


def fetch_price_data(ticker: str, years: int = 20) -> pd.Series:
    """지정 티커의 일별 수정 종가를 반환합니다 (pd.Series, index=날짜)."""
    end = datetime.today()
    start = end - timedelta(days=years * 365)
    raw = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if raw.empty:
        raise ValueError(f"'{ticker}' 데이터를 가져올 수 없습니다. 티커를 확인하세요.")
    close = raw["Close"]
    # yfinance v0.2+ 는 멀티인덱스 컬럼 반환 가능 → 단일 Series 로 변환
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close.name = ticker
    return close.dropna()


def fetch_vix_data(years: int = 20) -> pd.Series:
    """VIX 지수 일별 종가를 반환합니다 (pd.Series, index=날짜)."""
    vix = fetch_price_data("^VIX", years=years)
    vix.name = "VIX"
    return vix


def fetch_fear_greed_index() -> Optional[dict]:
    """
    CNN Fear & Greed Index 현재 값을 alternative.me API 로 조회합니다.
    반환값 예시::
        {
            "value": 25,
            "classification": "Extreme Fear",   # 또는 Fear / Neutral / Greed / Extreme Greed
            "timestamp": "2024-01-15"
        }
    API 호출 실패 시 None 반환.
    """
    url = "https://api.alternative.me/fng/?limit=1&format=json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()["data"][0]
        return {
            "value": int(data["value"]),
            "classification": data["value_classification"],
            "timestamp": datetime.utcfromtimestamp(int(data["timestamp"])).strftime("%Y-%m-%d"),
        }
    except Exception:
        return None
