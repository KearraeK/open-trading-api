"""FastAPI 백엔드: MDD Recovery Rate Analyzer REST API.

실행 방법 (프로젝트 루트에서)
    uvicorn backend.app:app --reload
"""

from __future__ import annotations

import math
import os
import random
import sys

# 프로젝트 루트를 sys.path에 추가여 mdd_recovery_analyzer 패키지 import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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


# ── React 빌드 경로 (SPA 라우트는 API 등록 후 파일 끝에 추가) ───────────────────
_FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")


# ──────────────────────────────────────────────────────────────────────────────
# 데모용 합성 데이터 생성 (네트워크 없는 환경에서 UI 확인용)
# ──────────────────────────────────────────────────────────────────────────────

def _make_demo_data(ticker: str, years: int, recovery_threshold: float, vix_threshold: float, step: float) -> dict:
    """기하 브라운 운동(GBM)으로 실제 시장과 유사한 합성 주가를 생성하여 분석합니다."""
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(42)
    n = years * 252

    # 티커별 파라미터
    params = {
        "SPY":  {"s0": 120.0, "mu": 0.10, "sigma": 0.16, "vix_now": 28.5},
        "QQQ":  {"s0":  80.0, "mu": 0.12, "sigma": 0.22, "vix_now": 28.5},
        "AAPL": {"s0":  15.0, "mu": 0.18, "sigma": 0.28, "vix_now": 28.5},
        "TSLA": {"s0":   5.0, "mu": 0.20, "sigma": 0.55, "vix_now": 28.5},
        "NVDA": {"s0":   3.0, "mu": 0.25, "sigma": 0.50, "vix_now": 28.5},
    }
    cfg = params.get(ticker.upper(), {"s0": 50.0, "mu": 0.10, "sigma": 0.22, "vix_now": 25.0})

    dt = 1 / 252
    drift = (cfg["mu"] - 0.5 * cfg["sigma"] ** 2) * dt
    diff  = cfg["sigma"] * math.sqrt(dt)

    log_returns = rng.normal(drift, diff, n)
    prices_arr = cfg["s0"] * np.exp(np.cumsum(log_returns))

    end_date = pd.Timestamp.today().normalize()
    dates = pd.bdate_range(end=end_date, periods=n)
    prices = pd.Series(prices_arr, index=dates, name=ticker.upper())

    # 마지막 가격을 기준으로 현재 낙폭이 ~22% 되도록 조정 (데모 연출)
    peak = float(prices.cummax().iloc[-1])
    target_drawdown = -0.22
    prices.iloc[-1] = peak * (1 + target_drawdown)

    # VIX 합성 (역상관 + 노이즈)
    vix_base = 16 + rng.normal(0, 4, n).cumsum() * 0.05
    vix_base = np.clip(vix_base, 10, 80)
    vix_arr = vix_base + rng.uniform(-2, 2, n)
    vix_arr[-1] = cfg["vix_now"]
    vix = pd.Series(np.clip(vix_arr, 10, 80), index=dates, name="VIX")

    # 분석 수행
    from mdd_recovery_analyzer.analyzer import calculate_drawdown, get_current_status
    status = get_current_status(
        prices=prices,
        vix_series=vix,
        fear_greed={"value": 22, "classification": "Extreme Fear"},
        recovery_threshold=recovery_threshold,
        vix_threshold=vix_threshold,
        drawdown_step=step,
    )

    drawdown = calculate_drawdown(prices)
    prices_w  = prices.resample("W").last()
    drawdown_w = drawdown.resample("W").last()
    price_chart = [
        {"date": str(idx.date()), "price": round(float(p), 2), "drawdown": round(float(d), 2)}
        for idx, p, d in zip(prices_w.index, prices_w.values, drawdown_w.values)
    ]

    return {
        "ticker": status["ticker"],
        "analysis_start": status["analysis_start"],
        "analysis_end": status["analysis_end"],
        "total_days": status["total_days"],
        "current_price": status["current_price"],
        "peak_price": status["peak_price"],
        "current_drawdown": status["current_drawdown"],
        "recovery_rate_at_current": status["recovery_rate_at_current"],
        "recovery_threshold": status["recovery_threshold"],
        "recovery_threshold_dd": status["recovery_threshold_dd"],
        "mdd_condition": status["mdd_condition"],
        "current_vix": status["current_vix"],
        "vix_threshold": status["vix_threshold"],
        "vix_condition": status["vix_condition"],
        "fear_greed_value": status["fear_greed_value"],
        "fear_greed_class": status["fear_greed_class"],
        "fear_greed_condition": status["fear_greed_condition"],
        "buy_signal": status["buy_signal"],
        "price_chart": price_chart,
        "recovery_table": status["recovery_table"].to_dict(orient="records"),
        "_demo": True,
    }


@app.get("/api/analyze")
async def analyze(
    ticker: str = Query(default="SPY", description="분석할 티커 (SPY, QQQ, AAPL 등)"),
    years: int = Query(default=20, ge=1, le=40, description="분석 기간 (년)"),
    recovery_threshold: float = Query(default=80.0, ge=50.0, le=99.0, description="매수 기준 회복률 (%)"),
    vix_threshold: float = Query(default=30.0, ge=10.0, le=80.0, description="매수 기준 VIX 수준"),
    no_vix: bool = Query(default=False, description="VIX 조회 비활성화"),
    no_fear_greed: bool = Query(default=False, description="공포탐욕지수 조회 비활성화"),
    step: float = Query(default=5.0, ge=1.0, le=10.0, description="회복률 테이블 구간 간격 (%)"),
    demo: bool = Query(default=False, description="데모 모드: 합성 데이터로 UI 확인"),
) -> dict:
    """분석 실행 엔드포인트.

    1. 주가 + VIX 데이터 수집
    2. 낙폭 / 회복률 계산
    3. 매수 신호 판단 후 JSON 반환
    """
    # ── 데모 모드 ─────────────────────────────────────────────────
    if demo:
        return _make_demo_data(ticker, years, recovery_threshold, vix_threshold, step)

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


# ── React SPA 정적 파일 서빙 (반드시 API 라우트 정의 후 마지막에 위치) ───────────
if os.path.isdir(_FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_FRONTEND_DIST, "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(os.path.join(_FRONTEND_DIST, "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        """SPA fallback: /api/* 는 통과, 그 외는 index.html 반환."""
        if full_path.startswith("api"):
            raise HTTPException(status_code=404)
        return FileResponse(os.path.join(_FRONTEND_DIST, "index.html"))
