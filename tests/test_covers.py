"""Tests for the procedural cover generator engine."""

from typing import Any

import numpy as np
import pytest
from PIL import Image, ImageDraw

from spotify_curation.covers import (
    SERIES1_GENERATORS,
    SERIES2_GENERATORS,
    gradient_bg,
    lerp_color,
    upload_cover,
)


class TestLerpColor:
    """Color interpolation utility."""

    def test_lerp_at_start(self) -> None:
        result = lerp_color((0, 0, 0), (100, 200, 50), 0.0)
        assert result == (0, 0, 0)

    def test_lerp_at_end(self) -> None:
        result = lerp_color((0, 0, 0), (100, 200, 50), 1.0)
        assert result == (100, 200, 50)

    def test_lerp_midpoint(self) -> None:
        result = lerp_color((10, 20, 30), (20, 40, 60), 0.5)
        assert result == (15, 30, 45)

    def test_lerp_negative(self) -> None:
        result = lerp_color((0, 0, 0), (-10, -20, -30), 1.0)
        assert result == (-10, -20, -30)


class TestGradientBg:
    """Gradient background drawing."""

    def test_gradient_vertical(self) -> None:
        img = Image.new("RGB", (10, 20))
        draw = ImageDraw.Draw(img)
        gradient_bg(draw, 10, 20, (0, 0, 0), (100, 0, 0))
        # Top pixel should be near top color
        top_color = img.getpixel((5, 0))
        bottom_color = img.getpixel((5, 19))
        assert top_color == (0, 0, 0)
        # t = y/h at bottom row => 19/20 = 0.95, so R ≈ 95
        assert bottom_color[0] == 95, f"Expected R=95, got {bottom_color}"
        assert bottom_color[1] == 0
        assert bottom_color[2] == 0

    def test_gradient_diagonal(self) -> None:
        img = Image.new("RGB", (10, 10))
        draw = ImageDraw.Draw(img)
        gradient_bg(draw, 10, 10, (0, 0, 0), (100, 0, 0), diagonal=True)
        # Should not crash; diagonal uses a different algorithm
        assert img.size == (10, 10)


class TestCoverGenerators:
    """All 9 procedural cover generators."""

    @pytest.fixture
    def rng1(self) -> np.random.Generator:
        return np.random.default_rng(42)

    @pytest.fixture
    def rng2(self) -> np.random.Generator:
        return np.random.default_rng(99)

    @pytest.mark.parametrize("name,gen_fn", list(SERIES1_GENERATORS.items()))
    def test_series1_generators(
        self, name: str, gen_fn: Any, rng1: np.random.Generator
    ) -> None:
        img = gen_fn(rng1)
        assert isinstance(img, Image.Image), f"{name}: expected PIL Image"
        assert img.mode == "RGB", f"{name}: expected RGB mode"
        assert img.size == (640, 640), f"{name}: expected 640x640"

    @pytest.mark.parametrize("name,gen_fn", list(SERIES2_GENERATORS.items()))
    def test_series2_generators(
        self, name: str, gen_fn: Any, rng2: np.random.Generator
    ) -> None:
        img = gen_fn(rng2)
        assert isinstance(img, Image.Image), f"{name}: expected PIL Image"
        assert img.mode == "RGB", f"{name}: expected RGB mode"
        assert img.size == (640, 640), f"{name}: expected 640x640"

    def test_reproducibility(self, rng1: np.random.Generator) -> None:
        """Same seed + same generator = identical output."""
        img_a = SERIES1_GENERATORS["rap"](rng1)
        # Re-create generator with same seed
        rng_copy = np.random.default_rng(42)
        img_b = SERIES1_GENERATORS["rap"](rng_copy)
        a_arr = np.array(img_a)
        b_arr = np.array(img_b)
        assert np.array_equal(a_arr, b_arr), "Same seed must produce identical image"

    def test_all_series1_have_different_output(self) -> None:
        """Each generator produces meaningfully different images (not all black/empty)."""
        rng = np.random.default_rng(42)
        for name, gen_fn in SERIES1_GENERATORS.items():
            img = gen_fn(rng)
            arr = np.array(img)
            assert arr.max() > 10, f"{name}: image appears near-black (max={arr.max()})"
            assert arr.min() < 245, f"{name}: image appears near-white (min={arr.min()})"

    def test_all_series2_have_different_output(self) -> None:
        """Each generator produces meaningfully different images (not all black/empty)."""
        rng = np.random.default_rng(99)
        for name, gen_fn in SERIES2_GENERATORS.items():
            img = gen_fn(rng)
            arr = np.array(img)
            assert arr.max() > 10, f"{name}: image appears near-black (max={arr.max()})"
            assert arr.min() < 245, f"{name}: image appears near-white (min={arr.min()})"


class TestUploadCover:
    """upload_cover error handling (no actual Spotify call)."""

    def test_upload_cover_fails_without_auth(self) -> None:
        """upload_cover should fail with auth-manager error when no Spotify session."""
        img = Image.new("RGB", (640, 640))
        with pytest.raises(Exception):
            upload_cover(None, "fake_playlist_id", img)  # type: ignore[arg-type]
