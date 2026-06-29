from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.prediction_service import PredictionService, validate_krisha_url


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict price for one Krisha URL.")
    parser.add_argument("url", help="Krisha listing URL.")
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    validate_krisha_url(args.url)
    prediction = PredictionService(ROOT).predict_by_url(args.url)

    print("Prediction complete")
    print(f"URL: {args.url}")
    print(f"Title: {prediction.title}")
    print(f"Listed price: {prediction.listed_price:,.0f} KZT")
    print(f"Area: {prediction.area_m2:,.2f} m2")
    print(f"Listed price per m2: {prediction.listed_price_per_m2:,.0f} KZT")
    print(f"Pred q10 per m2: {prediction.pred_price_per_m2_q10:,.0f} KZT")
    print(f"Pred q50 per m2: {prediction.pred_price_per_m2_q50:,.0f} KZT")
    print(f"Pred q90 per m2: {prediction.pred_price_per_m2_q90:,.0f} KZT")
    print(f"Pred q50 total: {prediction.pred_total_q50:,.0f} KZT")
    print(
        "Conservative discount vs asking: "
        f"{prediction.discount_vs_asking_pct_conservative:.2%}"
    )
    print(
        "Median discount vs asking: "
        f"{prediction.discount_vs_asking_pct_median:.2%}"
    )
    print(f"Interval width: {prediction.interval_width_pct:.2%}")


if __name__ == "__main__":
    main()
