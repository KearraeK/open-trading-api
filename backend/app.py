"""FastAPI 백엔드: MDD Recovery Rate Analyzer REST API.

실행 방법 (프로젝트 루트에서)
    uvicorn backend.app:app --reload
"""

from __future__ import annotations

import os
import sys

# 프로젝트 루트를 sys.path에 추가여 mdd_recovery_analyzer 패키지 import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from mdd_recovery_analyzer.analyzer import calculate_drawdown, get_current_status
from mdd_recovery_analyzer.data_fetcher import (
    fetch_fear_greed_index,
    fetch_price_data,
    fetch_vix_data,
)

app = FastAPI(
    title="MDD Recovery Rate Analyzer API",
    description="VIX & MDD 회복률 분석 - 기계적 추가 매수 타이밍 산출",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/analyze")
async def analyze(
    ticker: str = Query(default="SPY", description="분석할 티커 (SPY, QQQ, AAPL 등)"),
    years: int = Query(default=20, ge=1, le=40, description="분석 기간 (년)"),
    recovery_threshold: float = Query(default=80.0, ge=50.0, le=99.0, description="매수 기준 회복률 (%)"),
    vix_threshold: float = Query(default=30.0, ge=10.0, le=80.0, description="매수 기준 VIX 수준"),
    no_vix: bool = Query(default=False, description="VIX 조회 비활성화"),
    no_fear_greed: bool = Query(default=False, description="공포탐욕지수 조회 비활성화"),
    step: float = Query(default=5.0, ge=1.0, le=10.0, description="회복률 테이블 구간 간격 (%)"),
) -> dict:
    """분석 실행 엔드포인트.

    1. 주가 + VIX 데이터 수집
    2. 낙폭 / 회복률 계산
    3. 매수 신호 판단 후 JSON 반환
    """
    # ── 주가 데이터 수집 ──────────────────────────────────────────
    try:
        prices = fetch_price_data(ticker.upper(), years=years)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"주가 데이터 수집 실패: {exc}") from exc

    # ── VIX ──────────────────────────────────────────────────────────────
    vix_series = None
    if not no_vix:
        try:
            vix_series = fetch_vix_data(years=years)
        except Exception:
            pass  # VIX 없이 MDD 조건만으로 진행

    # ── 공포탐욕지수 ───────────────────────────────────────────────────
    fear_greed = None
    if not no_fear_greed:
        fear_greed = fetch_fear_greed_index()

    # ── 분석 ───────────────────────────────────────────────────────────
    status = get_current_status(
        prices=prices,
        vix_series=vix_series,
        fear_greed=fear_greed,
        recovery_threshold=recovery_threshold,
        vix_threshold=vix_threshold,
        drawdown_step=step,
    )

    # ── 차트용 데이터 (weekly resample 으로 페이로드 최소화) ───────────────
    drawdown = calculate_drawdown(prices)
    prices_w = prices.resample("W").last()
    drawdown_w = drawdown.resample("W").last()

    price_chart = [
        {
            "date": str(idx.date()),
            "price": round(float(p), 2),
            "drawdown": round(float(d), 2),
        }
        for idx, p, d in zip(prices_w.index, prices_w.values, drawdown_w.values)
    ]

    return {
        # 메타
        "ticker": status["ticker"],
        "analysis_start": status["analysis_start"],
        "analysis_end": status["analysis_end"],
        "total_days": status["total_days"],
        # 가격
        "current_price": status["current_price"],
        "peak_price": status["peak_price"],
        # MDD / 회복률
        "current_drawdown": status["current_drawdown"],
        "recovery_rate_at_current": status["recovery_rate_at_current"],
        "recovery_threshold": status["recovery_threshold"],
        "recovery_threshold_dd": status["recovery_threshold_dd"],
        "mdd_condition": status["mdd_condition"],
        # VIX
        "current_vix": status["current_vix"],
        "vix_threshold": status["vix_threshold"],
        "vix_condition": status["vix_condition"],
        # 공포탐욕
        "fear_greed_value": status["fear_greed_value"],
        "fear_greed_class": status["fear_greed_class"],
        "fear_greed_condition": status["fear_greed_condition"],
        # 최종 신호
        "buy_signal": status["buy_signal"],
        # 차트 데이터
        "price_chart": price_chart,
        "recovery_table": status["recovery_table"].to_dict(orient="records"),
    }
