"""CLI 진입점: MDD Recovery Rate Analyzer 실행 스크립트."""

from __future__ import annotations

import argparse
import sys

from .analyzer import calculate_drawdown, get_current_status
from .data_fetcher import fetch_fear_greed_index, fetch_price_data, fetch_vix_data
from .visualizer import plot_all


def _print_recovery_table(status: dict) -> None:
    rt = status["recovery_table"]
    print("\n[ 구간별 회복률 테이블 ]")
    print(f"{'낙폭 구간':>12} {'해당일수':>10} {'전체일수':>10} {'회복률':>10}")
    print("-" * 46)
    for _, row in rt.iterrows():
        flag = " ◀ 현재" if abs(abs(status["current_drawdown"]) - row["drawdown_threshold"]) < 2.5 else ""
        print(
            f"{row['drawdown_threshold']:>10.1f}%"
            f" {row['days_within']:>10,}"
            f" {row['total_days']:>10,}"
            f" {row['recovery_rate']:>9.1f}%"
            f"{flag}"
        )


def _print_status(status: dict) -> None:
    print("\n" + "=" * 56)
    print(f" {status['ticker']}  MDD & 회복률 분석 결과")
    print("=" * 56)
    print(f" 분석 기간    : {status['analysis_start']} ~ {status['analysis_end']}")
    print(f" 총 영업일수  : {status['total_days']:,}일")
    print(f" 현재가       : {status['current_price']:,.2f}")
    print(f" 전고점       : {status['peak_price']:,.2f}")
    print(f" 현재 낙폭    : {status['current_drawdown']:.2f}%")
    print(f" 현재 회복률  : {status['recovery_rate_at_current']:.1f}%")
    print(f" 회복률 {status['recovery_threshold']:.0f}% 기준 낙폭 레벨 : -{status['recovery_threshold_dd']:.1f}%")
    print()
    print(f" [MDD 조건]       {'충족 ✔' if status['mdd_condition'] else '미충족 ✘'}"
          f"  (회복률 {status['recovery_rate_at_current']:.1f}% {'≥' if status['mdd_condition'] else '<'}"
          f" {status['recovery_threshold']:.0f}%)")

    if status["current_vix"] is not None:
        print(f" [VIX 조건]       {'충족 ✔' if status['vix_condition'] else '미충족 ✘'}"
              f"  (VIX {status['current_vix']:.1f} {'≥' if status['vix_condition'] else '<'}"
              f" {status['vix_threshold']:.0f})")
    else:
        print(" [VIX 조건]       데이터 없음")

    if status["fear_greed_value"] is not None:
        print(f" [공포탐욕 조건]  {'충족 ✔' if status['fear_greed_condition'] else '미충족 ✘'}"
              f"  ({status['fear_greed_value']} / {status['fear_greed_class']})")
    else:
        print(" [공포탐욕 조건]  데이터 없음")

    signal_label = "▶ 기계적 추가 매수 구간 ◀" if status["buy_signal"] else "매수 조건 미충족"
    print()
    print(f" 최종 판단 : {signal_label}")
    print("=" * 56)


def run(
    ticker: str,
    years: int,
    recovery_threshold: float,
    vix_threshold: float,
    no_vix: bool,
    no_fear_greed: bool,
    no_chart: bool,
    save_chart: str | None,
    step: float,
) -> None:
    print(f"\n데이터 수집 중 ... ({ticker}, 최근 {years}년)")

    prices = fetch_price_data(ticker, years=years)
    print(f"  → 주가 데이터: {len(prices)}일 수집 완료 ({prices.index[0].date()} ~ {prices.index[-1].date()})")

    vix_series = None
    if not no_vix:
        try:
            vix_series = fetch_vix_data(years=years)
            print(f"  → VIX 데이터: {len(vix_series)}일 수집 완료")
        except Exception as e:
            print(f"  ⚠ VIX 수집 실패: {e}")

    fear_greed = None
    if not no_fear_greed:
        fear_greed = fetch_fear_greed_index()
        if fear_greed:
            print(f"  → 공포탐욕지수: {fear_greed['value']} ({fear_greed['classification']}) [{fear_greed['timestamp']}]")
        else:
            print("  ⚠ 공포탐욕지수 수집 실패 (API 연결 불가)")

    print("\n분석 중 ...")
    status = get_current_status(
        prices=prices,
        vix_series=vix_series,
        fear_greed=fear_greed,
        recovery_threshold=recovery_threshold,
        vix_threshold=vix_threshold,
        drawdown_step=step,
    )

    _print_status(status)
    _print_recovery_table(status)

    if not no_chart:
        drawdown = calculate_drawdown(prices)
        print("\n차트 렌더링 중 ...")
        plot_all(
            prices=prices,
            drawdown=drawdown,
            recovery_table=status["recovery_table"],
            status=status,
            save_path=save_chart,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mdd-analyzer",
        description="VIX & MDD 회복률 분석 프로그램 - 기계적 추가 매수 타이밍 산출",
    )
    parser.add_argument("ticker", type=str, help="분석할 티커 (예: SPY, QQQ, AAPL)")
    parser.add_argument("-y", "--years", type=int, default=20, help="분석 기간(년) [기본: 20]")
    parser.add_argument("-r", "--recovery-threshold", type=float, default=80.0,
                        help="매수 기준 회복률 %% [기본: 80]")
    parser.add_argument("--vix-threshold", type=float, default=30.0,
                        help="매수 기준 VIX 수준 [기본: 30]")
    parser.add_argument("--no-vix", action="store_true", help="VIX 데이터 수집 비활성화")
    parser.add_argument("--no-fear-greed", action="store_true",
                        help="공포탐욕지수 수집 비활성화")
    parser.add_argument("--no-chart", action="store_true", help="차트 출력 비활성화")
    parser.add_argument("--save-chart", type=str, default=None, metavar="PATH",
                        help="차트를 파일로 저장할 경로 (예: result.png)")
    parser.add_argument("--step", type=float, default=5.0,
                        help="회복률 테이블 구간 간격 %% [기본: 5]")

    args = parser.parse_args()

    try:
        run(
            ticker=args.ticker.upper(),
            years=args.years,
            recovery_threshold=args.recovery_threshold,
            vix_threshold=args.vix_threshold,
            no_vix=args.no_vix,
            no_fear_greed=args.no_fear_greed,
            no_chart=args.no_chart,
            save_chart=args.save_chart,
            step=args.step,
        )
    except KeyboardInterrupt:
        print("\n중단됨.")
        sys.exit(0)
    except ValueError as e:
        print(f"\n오류: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
