"""Reusable bilingual publication-grade Matplotlib style and figure exporter.

Copy this module into a competition project's ``shared/paper_style.py`` to keep
colors, fonts, axis styling, non-color encodings, and 400 dpi dual-format
exports consistent across all sub-questions (q1..qN / Q1..QN).
"""

from __future__ import annotations

import argparse
import inspect
import re
import struct
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Literal

import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties


# Semantic palette consistent across the whole paper:
# primary/ink for main data, secondary/teal for baselines/comparisons,
# accent/vermilion for optimal solutions, risks, and critical thresholds.
COLORS: dict[str, str] = {
    "ink": "#26384A",
    "primary": "#26384A",
    "secondary": "#237D78",
    "teal": "#237D78",
    "accent": "#C85A45",
    "vermilion": "#C85A45",
    "gold": "#D49A3A",
    "slate": "#5B6FA8",
    "rose": "#B66B78",
    "muted": "#87919C",
    "grid": "#DCE2E5",
    "faint": "#DCE2E5",
    "band": "#D8E5E5",
    "paper": "#FCFBF8",
    "white": "#FFFFFF",
}

# Ordered categorical sequence for multi-series plots.
CAT_PALETTE: tuple[str, ...] = (
    COLORS["primary"],
    COLORS["secondary"],
    COLORS["accent"],
    COLORS["gold"],
    COLORS["slate"],
    COLORS["rose"],
)

# Non-color redundant encodings so figures stay readable in grayscale or colorblind view.
LINE_STYLES: tuple[str, ...] = ("-", "--", "-.", ":", (0, (3, 1, 1, 1)), (0, (5, 2)))
MARKERS: tuple[str, ...] = ("o", "s", "^", "D", "v", "P")

ZH_FONT_CANDIDATES: list[str] = [
    "Microsoft YaHei",
    "PingFang SC",
    "Noto Sans CJK SC",
    "SimHei",
    "SimSun",
    "DejaVu Sans",
]
EN_FONT_CANDIDATES: list[str] = [
    "Times New Roman",
    "Nimbus Roman",
    "Liberation Serif",
    "DejaVu Serif",
]

QUESTION_DIR_RE = re.compile(r"^q[1-9]\d*$", re.IGNORECASE)
FIGURE_STEM_RE = re.compile(r"^fig\d{2}_[a-z0-9][a-z0-9_]*$")

def _available_fonts(candidates: list[str], fallback: str) -> list[str]:
    installed = {font.name for font in mpl.font_manager.fontManager.ttflist}
    matched = [name for name in candidates if name in installed]
    return matched or [fallback]


_ZH_FONTS = _available_fonts(ZH_FONT_CANDIDATES, "DejaVu Sans")
_EN_FONTS = _available_fonts(EN_FONT_CANDIDATES, "DejaVu Serif")

_ZH_FONT = FontProperties(family=_ZH_FONTS[0], weight="normal")
_EN_FONT = FontProperties(family=_EN_FONTS[0], weight="normal")


def apply_text_font(text, *, lang: Literal["zh", "en"] = "zh") -> None:
    """Use Times New Roman/serif for pure ASCII labels and CJK fonts otherwise."""
    content = text.get_text().strip()
    if lang == "en" or (content and content.isascii()):
        text.set_fontproperties(_EN_FONT)
    else:
        text.set_fontproperties(_ZH_FONT)


def apply_paper_style(
    *,
    lang: Literal["zh", "en"] = "zh",
    background: Literal["warm", "white"] = "warm",
    dpi: int = 400,
) -> None:
    """Configure global Matplotlib rcParams for clean competition paper figures."""
    bg_color = COLORS["paper"] if background == "warm" else COLORS["white"]
    if lang == "en":
        base_family = "serif"
        sans_list = _available_fonts(["Helvetica", "Arial", "DejaVu Sans"], "DejaVu Sans")
    else:
        base_family = "sans-serif"
        sans_list = _ZH_FONTS

    mpl.rcParams.update(
        {
            "font.family": base_family,
            "font.sans-serif": sans_list,
            "font.serif": _EN_FONTS,
            "mathtext.fontset": "stix",
            "axes.unicode_minus": False,
            "figure.dpi": 160,
            "savefig.dpi": dpi,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.04,
            "figure.facecolor": bg_color,
            "axes.facecolor": bg_color,
            "axes.edgecolor": COLORS["muted"],
            "axes.linewidth": 0.7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "bold",
            "axes.titlesize": 11.5,
            "axes.labelsize": 9.5,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "xtick.color": COLORS["ink"],
            "ytick.color": COLORS["ink"],
            "legend.frameon": False,
            "legend.fontsize": 8.5,
            "lines.linewidth": 2.0,
            "lines.markersize": 4.8,
        }
    )


def style_axis(
    ax,
    *,
    grid: bool = True,
    grid_axis: Literal["x", "y", "both"] = "y",
    lang: Literal["zh", "en"] = "zh",
    hide_left_spine: bool = False,
) -> None:
    """Apply clean axis borders, light reading grid, and bilingual tick/label fonts."""
    ax.tick_params(length=3.0 if not hide_left_spine else 0.0, width=0.6, pad=4)
    ax.spines["bottom"].set_color(COLORS["muted"])
    if hide_left_spine:
        ax.spines["left"].set_visible(False)
    else:
        ax.spines["left"].set_color(COLORS["muted"])
    if grid:
        ax.grid(axis=grid_axis, color=COLORS["grid"], linewidth=0.65, linestyle="-")
    else:
        ax.grid(False)
    ax.set_axisbelow(True)

    apply_text_font(ax.xaxis.label, lang=lang)
    apply_text_font(ax.yaxis.label, lang=lang)
    if ax.get_title():
        apply_text_font(ax.title, lang=lang)
    for label in [*ax.get_xticklabels(), *ax.get_yticklabels()]:
        apply_text_font(label, lang=lang)


def resolve_output_dir(output_dir: str | Path | None = None) -> Path:
    """Resolve ``qN/outputs`` (or ``QN/outputs``) automatically or use explicit path."""
    if output_dir is not None:
        destination = Path(output_dir)
    else:
        destination = None
        search_roots = [Path.cwd().resolve()]
        search_roots.extend(
            Path(frame.filename).resolve().parent for frame in inspect.stack()[1:]
        )
        for root in search_roots:
            for directory in (root, *root.parents):
                if QUESTION_DIR_RE.fullmatch(directory.name):
                    destination = directory / "outputs"
                    break
            if destination is not None:
                break
        if destination is None:
            raise ValueError(
                "Cannot infer question directory (q1..qN / Q1..QN). "
                "Pass output_dir='qN/outputs' explicitly."
            )

    destination.mkdir(parents=True, exist_ok=True)
    return destination


def export_figure(
    figure: Figure,
    stem: str,
    output_dir: str | Path | None = None,
    formats: Iterable[str] = ("png", "pdf"),
    *,
    dpi: int = 400,
    strict_name: bool = False,
) -> list[Path]:
    """Export figure in high-DPI PNG and optional vector formats (PDF/SVG)."""
    if strict_name and not FIGURE_STEM_RE.fullmatch(stem):
        raise ValueError(
            f"Figure stem {stem!r} must match 'figNN_lowercase_meaning' (e.g. 'fig01_sensitivity')."
        )

    destination = resolve_output_dir(output_dir)
    paths: list[Path] = []
    for raw_ext in formats:
        ext = raw_ext.lower().lstrip(".")
        path = destination / f"{stem}.{ext}"
        save_kwargs = {"bbox_inches": "tight", "pad_inches": 0.04}
        if ext == "png":
            save_kwargs["dpi"] = dpi
        figure.savefig(path, **save_kwargs)
        paths.append(path)
    return paths


def _read_png_dpi(path: Path) -> tuple[float, float] | None:
    with path.open("rb") as handle:
        if handle.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError("not a PNG file")
        while True:
            raw_len = handle.read(4)
            if not raw_len:
                return None
            length = struct.unpack(">I", raw_len)[0]
            chunk_type = handle.read(4)
            data = handle.read(length)
            handle.read(4)
            if chunk_type == b"pHYs" and length == 9:
                x_ppm, y_ppm, unit = struct.unpack(">IIB", data)
                if unit != 1:
                    return None
                return x_ppm * 0.0254, y_ppm * 0.0254
            if chunk_type == b"IEND":
                return None


def _self_test() -> int:
    mpl.use("Agg", force=True)
    import matplotlib.pyplot as plt

    with tempfile.TemporaryDirectory(prefix="paper-style-test-") as temp:
        q_dir = Path(temp) / "Q1" / "outputs"
        apply_paper_style(lang="en", background="warm", dpi=400)
        fig, ax = plt.subplots(figsize=(5.5, 3.6))
        x_vals = [0.0, 1.0, 2.0, 3.0, 4.0]
        ax.plot(
            x_vals,
            [1.0, 0.85, 0.72, 0.65, 0.61],
            color=COLORS["primary"],
            linestyle=LINE_STYLES[0],
            marker=MARKERS[0],
            label="Main model",
        )
        ax.plot(
            x_vals,
            [1.0, 0.96, 0.93, 0.91, 0.90],
            color=COLORS["secondary"],
            linestyle=LINE_STYLES[1],
            marker=MARKERS[1],
            label="Baseline",
        )
        ax.set_xlabel("Iteration step")
        ax.set_ylabel("Normalized error")
        ax.legend()
        style_axis(ax, grid=True, grid_axis="y", lang="en")
        exported = export_figure(
            fig,
            "fig01_style_check",
            output_dir=q_dir,
            formats=("png", "pdf"),
            dpi=400,
            strict_name=True,
        )
        plt.close(fig)

        png_path, pdf_path = exported[0], exported[1]
        dpi_val = _read_png_dpi(png_path)
        if dpi_val is None or min(dpi_val) < 399.0:
            print(f"SELF-TEST FAIL: unexpected PNG DPI {dpi_val}", file=sys.stderr)
            return 2
        if not pdf_path.read_bytes().startswith(b"%PDF-"):
            print("SELF-TEST FAIL: invalid PDF header", file=sys.stderr)
            return 2
        print(
            f"SELF-TEST PASS: exported {png_path.name} ({dpi_val[0]:.1f}x{dpi_val[1]:.1f} dpi) and {pdf_path.name}"
        )
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify templates/paper_style.py")
    parser.add_argument("--self-test", action="store_true", help="Run isolated export verification")
    args = parser.parse_args()
    if args.self_test:
        raise SystemExit(_self_test())
    parser.print_help()
