from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor


MODEL_FILENAMES = {
    "q10": "catboost_q10_price_per_m2_log.cbm",
    "q50": "catboost_q50_price_per_m2_log.cbm",
    "q90": "catboost_q90_price_per_m2_log.cbm",
}


@dataclass(frozen=True)
class ModelMetadata:
    feature_columns: list[str]
    categorical_features: list[str]
    target: str


@dataclass(frozen=True)
class PredictionFrame:
    features: pd.DataFrame
    predictions: pd.DataFrame


class PriceModelService:
    def __init__(
        self,
        models_dir: Path | str = "models",
        metadata_path: Path | str = "model_metadata.json",
    ) -> None:
        self.models_dir = Path(models_dir)
        self.metadata_path = Path(metadata_path)
        self.metadata = self._load_metadata(self.metadata_path)
        self.models = self._load_models(self.models_dir)

    @staticmethod
    def _load_metadata(path: Path) -> ModelMetadata:
        with path.open("r", encoding="utf-8") as file:
            raw = json.load(file)

        return ModelMetadata(
            feature_columns=list(raw["feature_columns"]),
            categorical_features=list(raw["categorical_features"]),
            target=str(raw["target"]),
        )

    @staticmethod
    def _load_models(models_dir: Path) -> dict[str, CatBoostRegressor]:
        models: dict[str, CatBoostRegressor] = {}
        for quantile, filename in MODEL_FILENAMES.items():
            model_path = models_dir / filename
            if not model_path.exists():
                raise FileNotFoundError(f"Missing model file: {model_path}")

            model = CatBoostRegressor()
            model.load_model(str(model_path))
            models[quantile] = model

        return models

    def prepare_features(self, data: pd.DataFrame | dict[str, Any]) -> pd.DataFrame:
        if isinstance(data, dict):
            frame = pd.DataFrame([data])
        else:
            frame = data.copy()

        missing = [
            column
            for column in self.metadata.feature_columns
            if column not in frame.columns
        ]
        if missing:
            raise ValueError(f"Missing required feature columns: {missing}")

        frame = frame.loc[:, self.metadata.feature_columns].copy()

        for column in self.metadata.categorical_features:
            frame[column] = frame[column].astype("string").fillna("missing")

        numeric_columns = [
            column
            for column in self.metadata.feature_columns
            if column not in self.metadata.categorical_features
        ]
        for column in numeric_columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

        return frame

    def predict(self, data: pd.DataFrame | dict[str, Any]) -> PredictionFrame:
        features = self.prepare_features(data)
        predictions = pd.DataFrame(index=features.index)

        for quantile, model in self.models.items():
            pred_log = model.predict(features)
            predictions[f"pred_price_per_m2_log_{quantile}"] = pred_log
            predictions[f"pred_price_per_m2_{quantile}"] = np.exp(pred_log)

        predictions["interval_width_pct"] = (
            predictions["pred_price_per_m2_q90"]
            - predictions["pred_price_per_m2_q10"]
        ) / predictions["pred_price_per_m2_q50"]

        return PredictionFrame(features=features, predictions=predictions)
