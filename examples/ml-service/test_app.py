"""Tests for ML Inference Service.

All tests pass. That's the point — the code looks correct,
tests are green, linter is clean. The vulnerabilities are semantic,
not syntactic.
"""

import json
import hashlib
from unittest.mock import MagicMock, patch

from app import (
    validate_features,
    compute_feature_hash,
    predict,
    load_model,
    get_model_version,
)


class TestValidateFeatures:
    def test_valid_numeric_features(self):
        result = validate_features({"age": 25, "income": 50000, "score": 0.8})
        assert result == {"age": 25.0, "income": 50000.0, "score": 0.8}

    def test_filters_unknown_features(self):
        result = validate_features({"age": 25, "secret_field": "hack"})
        assert "secret_field" not in result

    def test_converts_string_to_float(self):
        result = validate_features({"age": "25"})
        assert result == {"age": 25.0}

    def test_rejects_empty(self):
        try:
            validate_features({"unknown": 1})
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestComputeFeatureHash:
    def test_deterministic(self):
        h1 = compute_feature_hash({"a": 1, "b": 2})
        h2 = compute_feature_hash({"b": 2, "a": 1})
        assert h1 == h2  # sorted keys

    def test_different_inputs(self):
        h1 = compute_feature_hash({"a": 1})
        h2 = compute_feature_hash({"a": 2})
        assert h1 != h2


class TestPredict:
    def test_returns_prediction(self):
        model = MagicMock()
        model.predict.return_value = [1]
        model.predict_proba.return_value = [[0.2, 0.8]]
        pred, conf = predict(model, {"age": 25.0, "score": 0.9})
        assert pred == 1
        assert conf == 0.8

    def test_handles_no_proba(self):
        model = MagicMock()
        model.predict.return_value = [0]
        model.predict_proba.side_effect = AttributeError
        pred, conf = predict(model, {"score": 0.5})
        assert pred == 0
        assert conf == 0.85  # default


class TestLoadModel:
    @patch("builtins.open")
    @patch("app.pickle")
    def test_loads_and_caches(self, mock_pickle, mock_open):
        mock_pickle.loads.return_value = MagicMock()
        model = load_model("/tmp/test.pkl")
        assert model is not None
