# ------------------------------------------------------------------------------------- #
# ranked_bundles_plotter.py
#
# Original author: Sebastian Redzic (https://github.com/sebastjr)
# Original base version of this code was adapted as a starting point and might 
# be changed and/or augmented in the future.
#
# ------------------------------------------------------------------------------------- #


import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


# =====================================================================================
# Command-line arguments
# =====================================================================================

parser = argparse.ArgumentParser(
    description=(
        "Plot the ranked model bundles created by the best-fit ranking script."
    )
)

parser.add_argument(
    "--bestfit-dir",
    "-i",
    required=True,
    dest="bestfit_dir",
    help=(
        "Best-fit output directory containing the absorption, scattering, "
        "and overall ranking folders."
    ),
)

parser.add_argument(
    "--lab-file",
    "-l",
    required=True,
    dest="lab_file",
    help="Laboratory .optool directory containing dustkappa.dat.",
)

parser.add_argument(
    "--output-dir",
    "-o",
    dest="output",
    default=None,
    help="Directory for the generated PDF plots. Default: plots_<bestfit_dir_name>",
)

args = parser.parse_args()

# =====================================================================================
# Constants and paths
# =====================================================================================

BESTFIT_DIR = Path(args.bestfit_dir).expanduser().resolve()
LAB_MODEL_DIR = Path(args.lab_file).expanduser().resolve()

if args.output is None:
    OUTPUT_DIR = Path("plots_" + Path(args.bestfit_dir).name)

else:
    OUTPUT_DIR = Path(args.output).expanduser().resolve()

OPACITY_FILENAME = "dustkappa.dat"
BUNDLE_INFO_FILENAME = "bundle_info.txt"
COMBINED_PLOT_FILENAME = "top_ranked_models.pdf"


# Set this to True when dustkappa.dat contains a scattering-matrix header:
#
#   iformat
#   nlam
#   nang
#
# Otherwise, leave it False for the normal two-line header:
#
#   iformat
#   nlam
SCATTERING_MATRIX = False
PLOT_ALL_MODEL_FOLDERS = True # Plot every folder containing a dustkappa.dat file in the immediate input path.
WAVELENGTH_INTERVAL = (2.6, 3.6)  # µm
TOP_N = 3 # Number of model contenders wanted for plot.

RANKING_CATEGORIES = (
    "absorption",
    "scattering",
    "overall",
)

CATEGORY_LABELS = {
    "absorption": "absorption",
    "scattering": "scattering",
    "overall": "overall",
}

FONT_SIZE = 7.5 # Font size for plot legends.

if not BESTFIT_DIR.is_dir():
    parser.error(f"Best-fit directory does not exist: {BESTFIT_DIR}")

if not LAB_MODEL_DIR.is_dir():
    parser.error(f"Laboratory model directory does not exist: {LAB_MODEL_DIR}")

lab_opacity_path = LAB_MODEL_DIR / OPACITY_FILENAME

if not lab_opacity_path.is_file():
    parser.error(
        f"Laboratory opacity file does not exist: {lab_opacity_path}"
    )

# =====================================================================================
# Data structures and utility functions
# =====================================================================================


def load_optool_opacity(
    path: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Read wavelength, absorption, scattering, and asymmetry data."""
    with path.open(encoding="utf-8") as file:
        lines = [
            line
            for line in file
            if line.strip() and not line.lstrip().startswith("#")
        ]

    header_size = 3 if SCATTERING_MATRIX else 2

    if len(lines) < header_size:
        raise ValueError("Opacity file does not contain a complete header.")

    try:
        _iformat = int(lines[0])
        nlam = int(lines[1])

        if SCATTERING_MATRIX:
            _nang = int(lines[2])
    except ValueError as error:
        raise ValueError("Opacity file contains an invalid header.") from error

    data_lines = lines[header_size:header_size + nlam]

    if len(data_lines) != nlam:
        raise ValueError(
            f"Header declares {nlam} wavelength rows, but only "
            f"{len(data_lines)} were found."
        )

    opacity_data = np.loadtxt(data_lines)
    opacity_data = np.atleast_2d(opacity_data)

    if opacity_data.shape[1] < 4:
        raise ValueError(
            "Opacity data must contain wavelength, kabs, ksca, and g."
        )

    opacity_data = opacity_data[:, :4]

    if not np.all(np.isfinite(opacity_data)):
        raise ValueError("Opacity data contains NaN or infinite values.")

    wavelength = opacity_data[:, 0]

    if wavelength.size > 1 and not np.all(np.diff(wavelength) > 0):
        raise ValueError("Wavelength values must be strictly increasing.")

    kabs = opacity_data[:, 1]
    ksca = opacity_data[:, 2]
    g = opacity_data[:, 3]

    return wavelength, kabs, ksca, g


def display_name(model_dir: Path) -> str:
    """Return a model name without an optional .optool suffix."""
    return model_dir.name.removesuffix(".optool")


def bundle_rank(bundle_dir: Path) -> int | None:
    """Extract the leading rank from a bundle folder such as 01_model."""
    rank_text, separator, _remainder = bundle_dir.name.partition("_")

    if not separator or not rank_text.isdigit():
        return None

    return int(rank_text)


def get_ranked_bundle(category_dir: Path, rank: int) -> Path | None:
    """Find the bundle directory corresponding to one rank."""
    matching_bundles = [
        path
        for path in category_dir.iterdir()
        if path.is_dir() and bundle_rank(path) == rank
    ]

    if not matching_bundles:
        return None

    if len(matching_bundles) > 1:
        names = ", ".join(path.name for path in matching_bundles)
        raise RuntimeError(
            f"More than one rank-{rank} bundle exists in {category_dir}: "
            f"{names}"
        )

    return matching_bundles[0]


def read_reference_model_name(bundle_dir: Path) -> str | None:
    """Read the ranked reference-model directory name from bundle_info.txt."""
    info_path = bundle_dir / BUNDLE_INFO_FILENAME

    if not info_path.is_file():
        return None

    with info_path.open(encoding="utf-8") as file:
        for line in file:
            key, separator, value = line.partition(":")

            if separator and key.strip().lower() == "reference model":
                reference_name = value.strip()
                return reference_name or None

    return None


def model_directories_in_bundle(bundle_dir: Path) -> list[Path]:
    """Return all direct child model directories containing dustkappa.dat."""
    return sorted(
        (
            path
            for path in bundle_dir.iterdir()
            if path.is_dir() and (path / OPACITY_FILENAME).is_file()
        ),
        key=lambda path: path.name,
    )


def find_reference_model_dir(bundle_dir: Path) -> Path:
    """Locate the ranked reference model inside one bundle."""
    model_dirs = model_directories_in_bundle(bundle_dir)

    if not model_dirs:
        raise FileNotFoundError(
            f"No model directories were found in bundle: {bundle_dir}"
        )

    reference_name = read_reference_model_name(bundle_dir)

    if reference_name is not None:
        exact_match = bundle_dir / reference_name

        if exact_match.is_dir() and (exact_match / OPACITY_FILENAME).is_file():
            return exact_match

        normalized_reference_name = reference_name.removesuffix(".optool")
        normalized_matches = [
            path
            for path in model_dirs
            if path.name.removesuffix(".optool") == normalized_reference_name
        ]

        if len(normalized_matches) == 1:
            return normalized_matches[0]

    # Compatibility fallback for older bundle folders without bundle_info.txt.
    _rank_text, separator, folder_reference_name = bundle_dir.name.partition("_")

    if separator:
        normalized_folder_name = folder_reference_name.removesuffix(".optool")
        normalized_matches = [
            path
            for path in model_dirs
            if path.name.removesuffix(".optool") == normalized_folder_name
        ]

        if len(normalized_matches) == 1:
            return normalized_matches[0]

    raise FileNotFoundError(
        "Could not identify the ranked reference model in bundle: "
        f"{bundle_dir}"
    )


def load_model_data(model_dir: Path) -> dict[str, np.ndarray]:
    """Load one model directory into a small plotting dictionary."""
    wavelength, kabs, ksca, _g = load_optool_opacity(
        model_dir / OPACITY_FILENAME
    )

    return {
        "wavelength": wavelength,
        "kabs": kabs,
        "ksca": ksca,
    }

def configure_axes(
    fig: plt.Figure,
    absorption_axis: plt.Axes,
    scattering_axis: plt.Axes,
    title: str,
) -> None:
    """Apply common labels, limits, and layout to a two-panel figure."""
    fig.supxlabel("Wavelength [µm]")

    absorption_axis.set_ylabel(r"$\kappa_\mathrm{abs}$ [cm$^2$/g]")
    scattering_axis.set_ylabel(r"$\kappa_\mathrm{sca}$ [cm$^2$/g]")

    scattering_axis.set_xlim(*WAVELENGTH_INTERVAL)
    absorption_axis.set_title(title)

    #absorption_axis.set_yscale("log")
    #scattering_axis.set_yscale("log")


    absorption_axis.legend(loc="upper left",
                           fontsize=FONT_SIZE,
                           )
    scattering_axis.legend(loc="upper left",
                           fontsize=FONT_SIZE,
                           )

    scattering_axis.text(
        0.98,
        0.95,
        (
            r"$a_{\mathrm{min}} = 1\,\mathrm{nm}$"
            "\n"
            r"$a_{\mathrm{max}} = 100\,\mathrm{nm}$"
            "\n"
            r"$\mathrm{d}n_{\mathrm{dust}}(a) "
            r"\propto a^{-3.5}\,\mathrm{d}a$"
        ),
        transform=scattering_axis.transAxes,
        horizontalalignment="right",
        verticalalignment="top",
    )

    fig.tight_layout()


# =====================================================================================
# Load laboratory spectrum
# =====================================================================================

try:
    laboratory_data = load_model_data(LAB_MODEL_DIR)
except (OSError, ValueError, IndexError) as error:
    raise RuntimeError(
        f"Could not read laboratory model: {LAB_MODEL_DIR}"
    ) from error

laboratory_name = f"Laboratory: {display_name(LAB_MODEL_DIR)}"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================================================
# Combined plot: rank-1 reference model from every ranking category
# =====================================================================================

top_model_entries: dict[str, dict[str, object]] = {}

for category_name in RANKING_CATEGORIES:
    category_dir = BESTFIT_DIR / category_name

    if not category_dir.is_dir():
        print(f"Skipping missing ranking category: {category_dir}")
        continue

    rank_one_bundle = get_ranked_bundle(category_dir, rank=1)

    if rank_one_bundle is None:
        print(f"No rank-1 bundle found in: {category_dir}")
        continue

    try:
        reference_model_dir = find_reference_model_dir(rank_one_bundle)
    except FileNotFoundError as error:
        print(f"Skipping {rank_one_bundle}: {error}")
        continue

    model_key = reference_model_dir.name

    if model_key not in top_model_entries:
        top_model_entries[model_key] = {
            "model_dir": reference_model_dir,
            "categories": [],
        }

    top_model_entries[model_key]["categories"].append(
        CATEGORY_LABELS[category_name]
    )

if not top_model_entries:
    raise RuntimeError(
        "No rank-1 reference models could be read from the best-fit directory."
    )

fig, (absorption_axis, scattering_axis) = plt.subplots(
    2,
    1,
    sharex=True,
    figsize=(16, 12),
)

absorption_axis.plot(
    laboratory_data["wavelength"],
    laboratory_data["kabs"],
    label=laboratory_name,
)
scattering_axis.plot(
    laboratory_data["wavelength"],
    laboratory_data["ksca"],
    label=laboratory_name,
)

for entry in top_model_entries.values():
    model_dir = entry["model_dir"]
    categories = entry["categories"]

    try:
        model_data = load_model_data(model_dir)
    except (OSError, ValueError, IndexError) as error:
        print(f"Could not read {model_dir}: {error}")
        continue

    category_text = ", ".join(categories)
    label = f"Rank 1 {category_text}: {display_name(model_dir)}"

    absorption_axis.plot(
        model_data["wavelength"],
        model_data["kabs"],
        label=label,
    )
    scattering_axis.plot(
        model_data["wavelength"],
        model_data["ksca"],
        label=label,
    )

configure_axes(
    fig,
    absorption_axis,
    scattering_axis,
    title="Rank-1 opacity models",
)

combined_plot_path = OUTPUT_DIR / COMBINED_PLOT_FILENAME
fig.savefig(combined_plot_path)
plt.close(fig)
print(f"Created combined plot: {combined_plot_path}")

# =====================================================================================
# Category comparison plots: top three reference models plus laboratory data
# =====================================================================================

created_top_three_plots = 0

for category_name in RANKING_CATEGORIES:
    category_dir = BESTFIT_DIR / category_name

    if not category_dir.is_dir():
        continue

    category_output_dir = OUTPUT_DIR / category_name
    category_output_dir.mkdir(parents=True, exist_ok=True)

    ranked_reference_models: list[tuple[int, Path]] = []

    for rank in range(1, TOP_N + 1):
        bundle_dir = get_ranked_bundle(category_dir, rank)

        if bundle_dir is None:
            print(
                f"No rank-{rank} bundle found for {category_name}; "
                "omitting it from the top-three comparison."
            )
            continue

        try:
            reference_model_dir = find_reference_model_dir(bundle_dir)
        except FileNotFoundError as error:
            print(f"Could not identify rank {rank} for {category_name}: {error}")
            continue

        ranked_reference_models.append((rank, reference_model_dir))

    if not ranked_reference_models:
        print(
            f"No ranked reference models could be read for {category_name}; "
            "skipping its top-three comparison plot."
        )
        continue

    fig, (absorption_axis, scattering_axis) = plt.subplots(
        2,
        1,
        sharex=True,
        figsize=(16, 12),
    )

    absorption_axis.plot(
        laboratory_data["wavelength"],
        laboratory_data["kabs"],
        label=laboratory_name,
        linewidth=2.5,
    )
    scattering_axis.plot(
        laboratory_data["wavelength"],
        laboratory_data["ksca"],
        label=laboratory_name,
        linewidth=2.5,
    )

    plotted_models = 0

    for rank, model_dir in ranked_reference_models:
        try:
            model_data = load_model_data(model_dir)
        except (OSError, ValueError, IndexError) as error:
            print(f"Could not read {model_dir}: {error}")
            continue

        label = f"Rank {rank}: {display_name(model_dir)}"

        absorption_axis.plot(
            model_data["wavelength"],
            model_data["kabs"],
            label=label,
            linewidth=2.0,
        )
        scattering_axis.plot(
            model_data["wavelength"],
            model_data["ksca"],
            label=label,
            linewidth=2.0,
        )

        plotted_models += 1

    if plotted_models == 0:
        plt.close(fig)
        print(
            f"No readable ranked models were found for {category_name}; "
            "skipping its top-three comparison plot."
        )
        continue

    configure_axes(
        fig,
        absorption_axis,
        scattering_axis,
        title=(
            f"Top {plotted_models} models from the "
            f"{category_name} ranking"
        ),
    )

    top_three_output_path = category_output_dir / "top_3_models.pdf"
    fig.savefig(top_three_output_path)
    plt.close(fig)

    created_top_three_plots += 1
    print(
        f"Created top-three comparison plot: {top_three_output_path} "
        f"({plotted_models} ranked models plus laboratory spectrum)"
    )

# =====================================================================================
# Bundle plots: ranks 1, 2, and 3 in absorption, scattering, and overall
# =====================================================================================

created_bundle_plots = 0

for category_name in RANKING_CATEGORIES:
    category_dir = BESTFIT_DIR / category_name

    if not category_dir.is_dir():
        continue

    category_output_dir = OUTPUT_DIR / category_name
    category_output_dir.mkdir(parents=True, exist_ok=True)

    for rank in range(1, TOP_N + 1):
        bundle_dir = get_ranked_bundle(category_dir, rank)

        if bundle_dir is None:
            print(
                f"No rank-{rank} bundle found for {category_name}; skipping."
            )
            continue

        model_dirs = model_directories_in_bundle(bundle_dir)

        if not model_dirs:
            print(f"No valid model directories found in: {bundle_dir}")
            continue

        try:
            reference_model_dir = find_reference_model_dir(bundle_dir)
        except FileNotFoundError:
            reference_model_dir = None

        fig, (absorption_axis, scattering_axis) = plt.subplots(
            2,
            1,
            sharex=True,
            figsize=(16, 12),
        )

        absorption_axis.plot(
            laboratory_data["wavelength"],
            laboratory_data["kabs"],
            label=laboratory_name,
        )
        scattering_axis.plot(
            laboratory_data["wavelength"],
            laboratory_data["ksca"],
            label=laboratory_name,
        )

        for model_dir in model_dirs:
            try:
                model_data = load_model_data(model_dir)
            except (OSError, ValueError, IndexError) as error:
                print(f"Could not read {model_dir}: {error}")
                continue

            is_reference = (
                reference_model_dir is not None
                and model_dir.resolve() == reference_model_dir.resolve()
            )

            label = f"Ranked reference: {display_name(model_dir)}" if is_reference else display_name(model_dir)

            line_width = 2.5 if is_reference else 1.5

            absorption_axis.plot(
                model_data["wavelength"],
                model_data["kabs"],
                label=label,
                linewidth=line_width,
            )
            scattering_axis.plot(
                model_data["wavelength"],
                model_data["ksca"],
                label=label,
                linewidth=line_width,
            )

        configure_axes(
            fig,
            absorption_axis,
            scattering_axis,
            title=(
                f"{category_name.title()} ranking, rank {rank}: "
                "matching density and astrosil:water ratio"
            ),
        )

        output_filename = f"{bundle_dir.name}.pdf"
        output_path = category_output_dir / output_filename

        fig.savefig(output_path)
        plt.close(fig)

        created_bundle_plots += 1
        print(
            f"Created bundle plot: {output_path} "
            f"({len(model_dirs)} models plus laboratory spectrum)"
        )

print()
print(
    "Created 1 rank-1 summary plot, "
    f"{created_top_three_plots} top-three comparison plots, and "
    f"{created_bundle_plots} bundle plots."
)
print(f"Plot output directory: {OUTPUT_DIR}")