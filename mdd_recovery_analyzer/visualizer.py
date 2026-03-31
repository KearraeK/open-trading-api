"""시각화 모듈: MDD 차트, 회복률 분포, 현재 상태 요약 패널."""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

_COLORS = {
    "drawdown": "#e05c5c",
    "price": "#4c9be8",
    "recovery": "#5bba6f",
    "threshold": "#f0a500",
    "signal_yes": "#2ecc71",
    "signal_no": "#e74c3c",
}


def plot_all(
    prices: pd.Series,
    drawdown: pd.Series,
    recovery_table: pd.DataFrame,
    status: dict,
    save_path: Optional[str] = None,
) -> None:
    """
    4개 서브플롯을 포함한 종합 분석 차트를 출력합니다.

    Subplots
    --------
    1. 주가 추이 (수정 종가)
    2. MDD(낙폭) 추이 - 역사적 위치 강조
    3. 구간별 회복률 막대 그래프
    4. 현재 상태 요약 텍스트 패널
    """
    ticker = status["ticker"]
    fig, axes = plt.subplots(4, 1, figsize=(14, 18), gridspec_kw={"height_ratios": [2, 2, 2, 1.2]})
    fig.suptitle(
        f"{ticker}  MDD & 회복률(Recovery Rate) 분석",
        fontsize=16,
        fontweight="bold",
        y=0.98,
    )

    # ------------------------------------------------------------------
    # 1. 주가 추이
    # ------------------------------------------------------------------
    ax1 = axes[0]
    ax1.plot(prices.index, prices.values, color=_COLORS["price"], linewidth=1.2, label="수정 종가")
    ax1.set_ylabel("Price", fontsize=10)
    ax1.set_title("① 주가 추이", fontsize=11, loc="left")
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    # ------------------------------------------------------------------
    # 2. MDD 추이
    # ------------------------------------------------------------------
    ax2 = axes[1]
    ax2.fill_between(drawdown.index, drawdown.values, 0, color=_COLORS["drawdown"], alpha=0.4)
    ax2.plot(drawdown.index, drawdown.values, color=_COLORS["drawdown"], linewidth=0.8)

    # 주요 수평선
    for level, ls in [(-10, ":"), (-20, "--"), (-30, "-."), (-40, "-"), (-50, "-")]:
        ax2.axhline(level, color="gray", linestyle=ls, linewidth=0.8, alpha=0.7)
        ax2.text(drawdown.index[-1], level, f" {level}%", va="center", fontsize=7, color="gray")

    # 회복률 임계값에 해당하는 낙폭 수준 강조
    rr_dd = -status["recovery_threshold_dd"]
    ax2.axhline(
        rr_dd,
        color=_COLORS["threshold"],
        linestyle="--",
        linewidth=1.5,
        label=f"회복률 {status['recovery_threshold']:.0f}% 기준선 ({rr_dd:.1f}%)",
    )

    # 현재 낙폭 표시
    ax2.axhline(
        status["current_drawdown"],
        color="navy",
        linestyle="-",
        linewidth=1.0,
        alpha=0.8,
        label=f"현재 낙폭 ({status['current_drawdown']:.1f}%)",
    )

    ax2.set_ylabel("Drawdown (%)", fontsize=10)
    ax2.set_title("② MDD(낙폭) 추이", fontsize=11, loc="left")
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)

    # ------------------------------------------------------------------
    # 3. 구간별 회복률 막대 그래프
    # ------------------------------------------------------------------
    ax3 = axes[2]
    rt = recovery_table
    bars = ax3.bar(
        rt["drawdown_threshold"],
        rt["recovery_rate"],
        width=rt["drawdown_threshold"].diff().fillna(5).values * 0.8,
        color=_COLORS["recovery"],
        alpha=0.7,
        label="회복률",
    )

    # 회복률 임계값 수평선
    ax3.axhline(
        status["recovery_threshold"],
        color=_COLORS["threshold"],
        linestyle="--",
        linewidth=1.5,
        label=f"매수 기준선 ({status['recovery_threshold']:.0f}%)",
    )

    # 현재 낙폭 수직선
    ax3.axvline(
        abs(status["current_drawdown"]),
        color="navy",
        linestyle="-",
        linewidth=1.5,
        alpha=0.8,
        label=f"현재 낙폭 위치 ({status['current_drawdown']:.1f}%)",
    )

    # 바 위에 회복률 수치 표시
    for bar, rr in zip(bars, rt["recovery_rate"]):
        ax3.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"{rr:.0f}%",
            ha="center",
            va="bottom",
            fontsize=7,
        )

    ax3.set_xlabel("전고점 대비 하락률 (%)", fontsize=10)
    ax3.set_ylabel("회복률 (%)", fontsize=10)
    ax3.set_title("③ 구간별 회복률 (Recovery Rate)", fontsize=11, loc="left")
    ax3.set_ylim(0, 110)
    ax3.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3, axis="y")

    # ------------------------------------------------------------------
    # 4. 현재 상태 요약 패널
    # ------------------------------------------------------------------
    ax4 = axes[3]
    ax4.axis("off")

    signal_color = _COLORS["signal_yes"] if status["buy_signal"] else _COLORS["signal_no"]
    signal_text = "✔ 기계적 추가 매수 구간" if status["buy_signal"] else "✘ 매수 조건 미충족"

    lines = [
        f"분석 기간: {status['analysis_start']} ~ {status['analysis_end']}  ({status['total_days']:,}일)",
        f"현재가: {status['current_price']:,.2f}   전고점: {status['peak_price']:,.2f}",
        f"현재 낙폭: {status['current_drawdown']:.2f}%   현재 회복률: {status['recovery_rate_at_current']:.1f}%",
        f"회복률 {status['recovery_threshold']:.0f}% 기준 낙폭 레벨: -{status['recovery_threshold_dd']:.1f}%",
        f"[MDD 조건] {'충족 ✔' if status['mdd_condition'] else '미충족 ✘'}  "
        + (
            f"[VIX {status['current_vix']:.1f}] {'충족 ✔' if status['vix_condition'] else '미충족 ✘'}"
            if status["current_vix"] is not None
            else "[VIX 데이터 없음]"
        )
        + (
            f"  [공포탐욕 {status['fear_greed_value']} / {status['fear_greed_class']}] "
            + ('충족 ✔' if status['fear_greed_condition'] else '미충족 ✘')
            if status["fear_greed_value"] is not None
            else ""
        ),
    ]

    summary = "\n".join(lines)
    ax4.text(
        0.5, 0.6, summary,
        transform=ax4.transAxes,
        ha="center", va="center",
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f0f0f0", edgecolor="gray"),
    )
    ax4.text(
        0.5, 0.05, signal_text,
        transform=ax4.transAxes,
        ha="center", va="bottom",
        fontsize=13, fontweight="bold",
        color=signal_color,
    )
    ax4.set_title("④ 현재 매수 신호 판단", fontsize=11, loc="left")

    plt.tight_layout(rect=[0, 0, 1, 0.97])

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"차트 저장 완료: {save_path}")
    else:
        plt.show()

    plt.close(fig)
