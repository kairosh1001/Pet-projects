from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.model_service import PriceModelService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate saved CatBoost models against df_check.csv."
    )
    parser.add_argument("--data", default="df_check.csv", help="Prepared dataset path.")
    parser.add_argument("--rows", type=int, default=1000, help="Rows to validate.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = ROOT / args.data
    service = PriceModelService(
        models_dir=ROOT / "models",
        metadata_path=ROOT / "model_metadata.json",
    )

    df = pd.read_csv(data_path)
    sample = df.head(args.rows).copy()

    target = service.metadata.target
    if target not in sample.columns:
        raise ValueError(f"Target column is missing from validation data: {target}")

    y_true_log = sample[target]
    result = service.predict(sample.drop(columns=[target]))
    predictions = result.predictions

    pred_q50_log = predictions["pred_price_per_m2_log_q50"]
    rmse_log = float(np.sqrt(np.mean((y_true_log - pred_q50_log) ** 2)))
    approx_rmse_pct = float(np.exp(rmse_log) - 1)

    print("Model validation complete")
    print(f"Rows checked: {len(sample)}")
    print(f"Feature columns: {len(service.metadata.feature_columns)}")
    print(f"Categorical features: {len(service.metadata.categorical_features)}")
    print(f"q50 log RMSE on checked rows: {rmse_log:.6f}")
    print(f"Approx q50 RMSE percent: {approx_rmse_pct:.2%}")
    print()
    print("Prediction sample:")
    print(
        predictions[
            [
                "pred_price_per_m2_q10",
                "pred_price_per_m2_q50",
                "pred_price_per_m2_q90",
                "interval_width_pct",
            ]
        ]
        .head(5)
        .round(2)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
