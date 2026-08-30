from __future__ import annotations

from typing import Iterable, List, Optional

import numpy as np

from latent_art_bench.io import stable_hash
from latent_art_bench.schemas import FeatureRow, StrictModel


class FitTransformViolation(ValueError):
    pass


class FrozenStandardizerState(StrictModel):
    state_version: str = "real-only-standardizer-v1"
    feature_name: str
    feature_version: str
    feature_config_hash: str
    fit_canonical_work_ids: List[str]
    mean: List[float]
    scale: List[float]
    state_hash: str


class RealOnlyStandardizer:
    """A one-shot transform that makes fit/transform leakage an explicit error."""

    def __init__(self, state: Optional[FrozenStandardizerState] = None) -> None:
        self.state = state

    def fit(self, rows: Iterable[FeatureRow]) -> FrozenStandardizerState:
        if self.state is not None:
            raise FitTransformViolation("the transform is already fitted and frozen")
        rows = list(rows)
        if not rows:
            raise FitTransformViolation("cannot fit on an empty feature collection")
        if any(row.origin != "real" for row in rows):
            raise FitTransformViolation("fit data must contain real works only")
        if any(row.split != "train" for row in rows):
            raise FitTransformViolation("fit data must contain real-training works only")
        if any(row.status == "failed" for row in rows):
            raise FitTransformViolation("failed feature rows cannot be fitted")
        work_ids = [row.canonical_work_id for row in rows]
        if len(set(work_ids)) != len(work_ids):
            raise FitTransformViolation(
                "fit data must contain at most one row per canonical work"
            )
        feature_identity = {
            (row.feature_name, row.feature_version, row.feature_config_hash) for row in rows
        }
        if len(feature_identity) != 1:
            raise FitTransformViolation("fit rows do not share one frozen feature identity")
        matrix = self._matrix(rows)
        mean = matrix.mean(axis=0)
        scale = matrix.std(axis=0, ddof=0)
        scale = np.where(scale <= np.finfo(np.float64).eps, 1.0, scale)
        feature_name, feature_version, config_hash = next(iter(feature_identity))
        state_payload = {
            "state_version": "real-only-standardizer-v1",
            "feature_name": feature_name,
            "feature_version": feature_version,
            "feature_config_hash": config_hash,
            "fit_canonical_work_ids": sorted(work_ids),
            "mean": mean.tolist(),
            "scale": scale.tolist(),
        }
        self.state = FrozenStandardizerState(
            **state_payload, state_hash=stable_hash(state_payload)
        )
        return self.state

    def transform(self, rows: Iterable[FeatureRow]) -> np.ndarray:
        if self.state is None:
            raise FitTransformViolation("transform cannot run before fit or state loading")
        rows = list(rows)
        for row in rows:
            identity = (row.feature_name, row.feature_version, row.feature_config_hash)
            expected = (
                self.state.feature_name,
                self.state.feature_version,
                self.state.feature_config_hash,
            )
            if identity != expected:
                raise FitTransformViolation("transform row has a different feature identity")
        matrix = self._matrix(rows)
        return (matrix - np.asarray(self.state.mean)) / np.asarray(self.state.scale)

    @staticmethod
    def _matrix(rows: List[FeatureRow]) -> np.ndarray:
        if not rows:
            raise FitTransformViolation("cannot transform an empty feature collection")
        matrix = np.asarray([row.vector for row in rows], dtype=np.float64)
        if matrix.ndim != 2 or matrix.shape[1] == 0:
            raise FitTransformViolation("feature vectors must form a non-empty matrix")
        if not np.isfinite(matrix).all():
            raise FitTransformViolation("feature vectors contain non-finite values")
        return matrix
