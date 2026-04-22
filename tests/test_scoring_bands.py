from __future__ import annotations

import pytest

from house_index.scoring import rules


class TestBandDesc:
    BANDS = [[3, 1.0], [6, 0.8], [10, 0.55], [15, 0.3]]

    @pytest.mark.parametrize(
        "value,expected_mult",
        [
            (0, 1.0),
            (3, 1.0),
            (3.01, 0.8),
            (6, 0.8),
            (8, 0.55),
            (10, 0.55),
            (12, 0.3),
            (15, 0.3),
            (15.01, 0.0),
            (100, 0.0),
        ],
    )
    def test_bands(self, value, expected_mult):
        assert rules.band_desc(value, 25, self.BANDS) == pytest.approx(25 * expected_mult)

    def test_none_returns_zero(self):
        assert rules.band_desc(None, 25, self.BANDS) == 0.0

    def test_empty_bands_returns_zero(self):
        assert rules.band_desc(5, 25, []) == 0.0


class TestBandAsc:
    BANDS = [[40, 0.3], [55, 0.6], [70, 0.85], [90, 1.0]]

    @pytest.mark.parametrize(
        "value,expected_mult",
        [
            (0, 0.0),
            (39, 0.0),
            (40, 0.3),
            (50, 0.3),
            (55, 0.6),
            (70, 0.85),
            (85, 0.85),
            (90, 1.0),
            (150, 1.0),
        ],
    )
    def test_bands(self, value, expected_mult):
        assert rules.band_asc(value, 15, self.BANDS) == pytest.approx(15 * expected_mult)

    def test_none_returns_zero(self):
        assert rules.band_asc(None, 15, self.BANDS) == 0.0


class TestEnumScore:
    MAP = {"garage": 8, "lot": 5, "street": 2, "none": 0}

    def test_known_value(self):
        assert rules.enum_score("garage", self.MAP) == 8
        assert rules.enum_score("none", self.MAP) == 0

    def test_unknown_value(self):
        assert rules.enum_score("unknown", self.MAP) == 0.0

    def test_none(self):
        assert rules.enum_score(None, self.MAP) == 0.0


class TestBoolScore:
    def test_true(self):
        assert rules.bool_score(True, 3) == 3.0

    def test_false(self):
        assert rules.bool_score(False, 3) == 0.0

    def test_none(self):
        assert rules.bool_score(None, 3) == 0.0


class TestBoolPlusArea:
    def test_no_amenity(self):
        assert rules.bool_plus_area_score(False, 50, 2, 0.05, 6) == 0.0

    def test_has_but_no_area(self):
        assert rules.bool_plus_area_score(True, None, 2, 0.05, 6) == 2.0

    def test_has_with_area(self):
        assert rules.bool_plus_area_score(True, 40, 2, 0.05, 6) == pytest.approx(4.0)

    def test_cap_applied(self):
        assert rules.bool_plus_area_score(True, 1000, 2, 0.05, 6) == 6.0


class TestConditionalBool:
    def test_condition_not_met(self):
        assert rules.conditional_bool_score(2, lambda v: v > 3, True, 5) == 0.0

    def test_condition_met_target_true(self):
        assert rules.conditional_bool_score(5, lambda v: v > 3, True, 5) == 5.0

    def test_condition_met_target_false(self):
        assert rules.conditional_bool_score(5, lambda v: v > 3, False, 5) == 0.0

    def test_condition_value_none(self):
        assert (
            rules.conditional_bool_score(None, lambda v: v is not None and v > 3, True, 5) == 0.0
        )
