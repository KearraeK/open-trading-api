"""핵심 분석 모듈: MDD 계산, 구간별 회복률 산출, 매수 신호 판단."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 1. MDD (일별 낙폭) 계산
# ---------------------------------------------------------------------------

def calculate_drawdown(prices: pd.Series) -> pd.Series:
    """
    각 날짜의 「전고점 대비 하락률(%)」을 계산합니다.

    공식: (현재가 - 전고점) / 전고점 × 100  → 항상 0 이하의 값
    """
    rolling_max = prices.cummax()
    drawdown = (prices - rolling_max) / rolling_max * 100
    drawdown.name = "drawdown_pct"
    return drawdown


# ---------------------------------------------------------------------------
# 2. 구간별 회복률 테이블 산출
# ---------------------------------------------------------------------------

def calculate_recovery_table(
    drawdown: pd.Series,
    step: float = 5.0,
    max_drawdown: float = 70.0,
) -> pd.DataFrame:
    """
    하락률 구간별 회복률 테이블을 반환합니다.

    회복률(X%) 정의
    ~~~~~~~~~~~~~~
    분석 기간 전체 영업일 중 「고점 대비 낙폭이 X% 이내」였던 날의 비율.

    예: 회복률(20%) = 85%  →  전체 기간의 85% 에서 주가가 전고점 대비 -20% 이내에 위치.
    즉 -20% 아래로 내려간 날이 15% 에 불과 → 현재 -20% 지점은 역사적 과매도 구간.

    Parameters
    ----------
    drawdown     : calculate_drawdown() 결과 Series (값이 ≤ 0)
    step         : 구간 간격(%) 기본 5
    max_drawdown : 최대 분석 구간(%) 기본 70

    Returns
    -------
    pd.DataFrame  columns=[drawdown_threshold, days_within, total_days, recovery_rate]
    """
    thresholds = np.arange(0, max_drawdown + step, step)
    total_days = len(drawdown)
    records = []

    for thr in thresholds:
        days_within = int((drawdown >= -thr).sum())
        recovery_rate = round(days_within / total_days * 100, 2)
        records.append(
            {
                "drawdown_threshold": round(float(thr), 1),
                "days_within": days_within,
                "total_days": total_days,
                "recovery_rate": recovery_rate,
            }
        )

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 3. 현재 회복률 보간
# ---------------------------------------------------------------------------

def interpolate_recovery_rate(recovery_table: pd.DataFrame, current_dd_abs: float) -> float:
    """
    현재 낙폭(절댓값)에 대응하는 회복률을 선형 보간으로 반환합니다.
    """
    thr = recovery_table["drawdown_threshold"].values
    rr = recovery_table["recovery_rate"].values
    return float(np.interp(current_dd_abs, thr, rr))


# ---------------------------------------------------------------------------
# 4. 매수 신호 종합 판단
# ---------------------------------------------------------------------------

def get_current_status(
    prices: pd.Series,
    vix_series: Optional[pd.Series] = None,
    fear_greed: Optional[dict] = None,
    recovery_threshold: float = 80.0,
    vix_threshold: float = 30.0,
    drawdown_step: float = 5.0,
    max_drawdown: float = 70.0,
) -> dict:
    """
    현재 날짜 기준의 MDD, 회복률, 매수 신호를 종합한 딕셔너리를 반환합니다.

    Returns
    -------
    dict with keys::
        ticker, analysis_start, analysis_end, total_days,
        current_price, peak_price,
        current_drawdown,        # 현재 낙폭 (%)
        recovery_rate_at_current,# 현재 낙폭 지점의 회복률 (%)
        recovery_threshold,      # 설정된 회복률 임계값 (%)
        recovery_threshold_dd,   # 회복률 임계값에 해당하는 낙폭 수준 (%)
        mdd_condition,           # 회복률 조건 충족 여부
        current_vix,             # 최신 VIX 값 (없으면 None)
        vix_threshold,           # 설정된 VIX 임계값
        vix_condition,           # VIX 조건 충족 여부 (None=데이터 없음)
        fear_greed_value,        # 공포탐욕지수 값 (없으면 None)
        fear_greed_class,        # 공포탐욕지수 분류 (없으면 None)
        fear_greed_condition,    # 공포탐욕지수 조건 충족 여부 (None=데이터 없음)
        buy_signal,              # 최종 매수 신호
        recovery_table           # 구간별 회복률 DataFrame
    """
    drawdown = calculate_drawdown(prices)
    recovery_table = calculate_recovery_table(drawdown, step=drawdown_step, max_drawdown=max_drawdown)

    current_price = float(prices.iloc[-1])
    peak_price = float(prices.cummax().iloc[-1])
    current_dd = float(drawdown.iloc[-1])       # ≤ 0
    current_dd_abs = abs(current_dd)

    recovery_at_current = interpolate_recovery_rate(recovery_table, current_dd_abs)

    # 회복률 임계값에 해당하는 낙폭 수준 (역방향 보간)
    thr_vals = recovery_table["drawdown_threshold"].values
    rr_vals = recovery_table["recovery_rate"].values
    # recovery_rate 는 threshold 증가에 따라 단조 증가 → 역보간
    recovery_threshold_dd = float(np.interp(recovery_threshold, rr_vals, thr_vals))

    mdd_condition = recovery_at_current >= recovery_threshold

    # VIX 조건
    current_vix: Optional[float] = None
    vix_condition: Optional[bool] = None
    if vix_series is not None and not vix_series.empty:
        current_vix = float(vix_series.iloc[-1])
        vix_condition = current_vix >= vix_threshold

    # 공포탐욕지수 조건 (25 이하 = Extreme Fear)
    fear_greed_value: Optional[int] = None
    fear_greed_class: Optional[str] = None
    fear_greed_condition: Optional[bool] = None
    if fear_greed is not None:
        fear_greed_value = fear_greed["value"]
        fear_greed_class = fear_greed["classification"]
        fear_greed_condition = fear_greed_class in ("Extreme Fear", "Fear")

    # 최종 매수 신호: MDD 조건 필수 + (VIX 또는 공포탐욕지수) 중 하나 이상 충족
    fear_signal_any = (
        (vix_condition is True)
        or (fear_greed_condition is True)
    )
    # 공포 지표 데이터가 하나도 없으면 MDD 조건만으로 판단
    if vix_condition is None and fear_greed_condition is None:
        buy_signal = mdd_condition
    else:
        buy_signal = mdd_condition and fear_signal_any

    return {
        "ticker": prices.name,
        "analysis_start": str(prices.index[0].date()),
        "analysis_end": str(prices.index[-1].date()),
        "total_days": len(prices),
        "current_price": round(current_price, 2),
        "peak_price": round(peak_price, 2),
        "current_drawdown": round(current_dd, 2),
        "recovery_rate_at_current": round(recovery_at_current, 2),
        "recovery_threshold": recovery_threshold,
        "recovery_threshold_dd": round(recovery_threshold_dd, 2),
        "mdd_condition": mdd_condition,
        "current_vix": round(current_vix, 2) if current_vix is not None else None,
        "vix_threshold": vix_threshold,
        "vix_condition": vix_condition,
        "fear_greed_value": fear_greed_value,
        "fear_greed_class": fear_greed_class,
        "fear_greed_condition": fear_greed_condition,
        "buy_signal": buy_signal,
        "recovery_table": recovery_table,
    }
