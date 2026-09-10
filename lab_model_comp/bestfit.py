# ------------------------------------------------------------------------------------- #
# bestfit.py
#
# Original author: Sebastian Redzic (https://github.com/sebastjr)
# Original base version of this code was adapted as a starting point and might 
# be changed and/or augmented in the future.
#
# ------------------------------------------------------------------------------------- #

import argparse
import re
import shutil
import numpy as np
from math import isclose
from pathlib import Path

"""
Takes 'optool' generated dust models and uses RMSE to 
evaulate the fit to a laboratory reference model in the 
absorption and scattering spectra including a overall score
(mean between absorption and scattering score).

The top performing models are copied and sorted into corrosponding
output directories. The models are sorted into absorption, scattering and overall
including (if the script manages to find them) related models that only differ
in water location in the grain structure from the top performer(s).
"""

# =====================================================================================
# Command-line arguments
# =====================================================================================

parser = argparse.ArgumentParser(
    description=(
        "Rank optool opacity models against a laboratory spectrum."
        "Ranking is done using RMSE against the labratory spectrum for absorption, "
        "scattering and an overall score (mean of absorption and scattering score)."
        "Top performers are then copied into a new directory with models with the same parameters (excluding water location) also included if found."
        ),
)

parser.add_argument(
    "--input",
    "-i",
    required=True,
    dest="input",
    help=(
        "Input directory containing models to be fitted against a labratory spectrum." \
        "Directory is expected to contain model folders with a 'dustkappa.dat' file." \
        "EXPECTED STRUCTURE: see README"
    ),
)

parser.add_argument(
    "--lab-file",
    "-l",
    required=True,
    dest="lab_file",
    help=("Laboratory model directory containing 'dustkappa.dat'." \
    "EXPECTED STRUCTURE: " \
    "lab_model/" \
    "└── dustkappa.dat"
    ),
)

parser.add_argument(
    "--ranking-output",
    "-o",
    default="bestfit_models",
    dest="ranking_output",
    help=(
        "Root directory for the absorption, scattering, and overall model "
        "bundles. Default: bestfit_models." \
        "OUTPUT STRUCTURE: see README" \
    ),
)

parser.add_argument(
    "--ranking-file",
    default=None,
    help=(
        "Path for the complete ranking text file. By default, the file is "
        "written to <ranking-output-dir>/model_rankings.txt."
    ),
)

parser.add_argument(
    "--wavelength-minimum",
    "-lmin",
    dest="wavelength_minimum",
    default=2.5, # µm
    help=(
        "Minimum wavelength used for fitting in µm"
    ),
)

parser.add_argument(
    "--wavelength-maximum",
    "-lmax",
    dest="wavelength_maximum",
    default=4.0, # µm
    help=(
        "Maximum wavelength used for fitting in µm"
    ),
)

parser.add_argument(
    "--copy-models",
    action="store_true",
    help=argparse.SUPPRESS,
)

parser.add_argument(
    "--move-models",
    action="store_true",
    help=argparse.SUPPRESS,
)

parser.add_argument(
    "--include-all",
    action="store_true",
    help=argparse.SUPPRESS,
)

args = parser.parse_args()

# =====================================================================================
# Constants and paths
# =====================================================================================

INPUT_DIR = Path(args.input).expanduser().resolve()
LAB_MODEL_PATH = Path(args.lab_file).expanduser().resolve()
RANKING_OUTPUT_DIR = Path(args.ranking_output).expanduser().resolve()

OPACITY_FILE_NAME = "dustkappa.dat"
SILICATE_MATERIALS = ( # Recognized materials in model filenames (used to fetch all related models)
    "astrosil",
    "pyr-mg50",
    "pyr-mg100",
)

WAVELENGTH_INTERVAL = (args.wavelength_minimum, args.wavelength_maximum)  # µm

SCATTERING_MATRIX = False
TOP_N = 3
DENSITY_ABS_TOLERANCE = 1e-8

RATIO_REL_TOLERANCE = 5e-5
RATIO_ABS_TOLERANCE = 5e-5

LAB_OPACITY_FILE = LAB_MODEL_PATH / OPACITY_FILE_NAME # Make path to lab dustkappa.dat file

# =====================================================================================
# Command-line error handling
# =====================================================================================

if args.move_models:
    print(
        "Warning: --move-models is deprecated. Models will be copied and "
        "the originals will be retained."
    )

if args.ranking_file is not None:
    RANKING_OUTPUT_FILE = Path(args.ranking_file).expanduser().resolve()
else:
    RANKING_OUTPUT_FILE = RANKING_OUTPUT_DIR / "model_rankings.txt"

if not INPUT_DIR.is_dir():
    parser.error(f"Input directory does not exist: {INPUT_DIR}")

if not LAB_MODEL_PATH.is_dir():
    parser.error(
        f"Laboratory model directory does not exist: {LAB_MODEL_PATH}"
    )

if not LAB_OPACITY_FILE.is_file():
    parser.error(
        f"Laboratory opacity file does not exist: {LAB_OPACITY_FILE}"
    )

for possible_model_path in INPUT_DIR.iterdir():
    if (
        possible_model_path.is_dir()
        and RANKING_OUTPUT_DIR.is_relative_to(possible_model_path.resolve())
    ):
        parser.error(
            "The ranking output directory cannot be inside a model "
            f"directory: {possible_model_path}"
        )

# =====================================================================================
# Utility functions
# =====================================================================================

def rmse(
        model_data: np.ndarray, 
        lab_data: np.ndarray
        ) -> float:
    """Calculate the root-mean-square error between two arrays."""
    model_data = np.asarray(model_data, dtype=float)
    lab_data = np.asarray(lab_data, dtype=float)

    if model_data.shape != lab_data.shape:
        raise ValueError(
            "Model and laboratory data have different shapes: "
            f"{model_data.shape} and {lab_data.shape}."
        )

    if model_data.size == 0:
        raise ValueError("Model and laboratory data are empty.")

    return float(np.sqrt(np.mean((model_data - lab_data) ** 2)))


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

    # Formatting of dustkappa.dat file slightly differs if scattering matrix is included
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
            "Opacity data must contain at least four columns: "
            "wavelength, kabs, ksca, and g."
        )

    opacity_data = opacity_data[:, :4] # Ignore column identifiers: wavelength, kabs, ksca, g

    if not np.all(np.isfinite(opacity_data)):
        raise ValueError("Opacity data contains NaN or infinite values.")

    wavelength = opacity_data[:, 0]

    if wavelength.size > 1 and not np.all(np.diff(wavelength) > 0):
        raise ValueError("Wavelength values must be strictly increasing.")

    kabs = opacity_data[:, 1]
    ksca = opacity_data[:, 2]
    g = opacity_data[:, 3]

    return wavelength, kabs, ksca, g


def format_models(
    title: str,
    ranked_models: list[tuple[Path, dict[str, float]]],
    score_key: str,
    top_n: int | None = None,
) -> str:
    """Return a formatted ranking while displaying only model basenames."""
    models_to_include = (
        ranked_models if top_n is None else ranked_models[:top_n]
    )

    output_lines = [title + ":", ""]

    for rank, (model_path, scores) in enumerate(models_to_include, start=1):
        output_lines.extend(
            [
                f"{rank:3d}. {model_path.name}",
                f"     absorption RMSE = {scores['rmse_abs']:.6e}",
                f"     scattering RMSE = {scores['rmse_sca']:.6e}",
                f"     total RMSE      = {scores['rmse_total']:.6e}",
                f"     ranking score   = {scores[score_key]:.6e}",
                "",
            ]
        )

    return "\n".join(output_lines)


def sum_values_after_matching_parts(
    parts: list[str],
    predicate,
    property_name: str,
) -> float:
    """Sum numeric fractions following every matching material field.

    A model can contain several components of the same material, for example
    ``waterCore_0.05_waterMantle_0.05``.  Both fractions belong to the total
    water abundance and therefore both must contribute to the ratio.
    """
    values = []

    for index, item in enumerate(parts):
        if not predicate(item.lower()):
            continue

        try:
            values.append(float(parts[index + 1]))
        except (IndexError, ValueError) as error:
            raise ValueError(
                f"No valid numeric value follows a {property_name} field."
            ) from error

    if not values:
        raise ValueError(f"No {property_name} field was found.")

    return sum(values)


def parse_model_properties(
    model_path: Path,
) -> tuple[str, float, float]:
    """Extract silicate material, density, and silicate:water mass ratio. Used to fetch related models to 'model_path'."""
    model_name = model_path.name.removesuffix(".optool")
    parts = model_name.split("_")
    lower_parts = [part.lower() for part in parts]

    try:
        # -------------------------------------------------------------
        # Density
        # -------------------------------------------------------------

        if "rho" in lower_parts:
            rho_index = lower_parts.index("rho")
            rho = float(parts[rho_index + 1])
        else:
            density_match = next(
                (
                    re.search(
                        r"density([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
                        part,
                        flags=re.IGNORECASE,
                    )
                    for part in parts
                    if "density" in part.lower()
                ),
                None,
            )

            if density_match is None:
                raise ValueError("No density field was found.")

            rho = float(density_match.group(1))

        # -------------------------------------------------------------
        # Silicate material
        # -------------------------------------------------------------

        matching_materials = [
            material
            for material in SILICATE_MATERIALS
            if any(material in part for part in lower_parts)
        ]

        if not matching_materials:
            raise ValueError("No recognized silicate material was found.")

        if len(matching_materials) > 1:
            raise ValueError(
                "More than one recognized silicate material was found."
            )

        silicate_material = matching_materials[0]

        # -------------------------------------------------------------
        # Silicate mass fraction
        # -------------------------------------------------------------

        silicate_fraction = sum_values_after_matching_parts(
            parts,
            lambda item: silicate_material in item,
            silicate_material,
        )

        # -------------------------------------------------------------
        # Water mass fraction
        # -------------------------------------------------------------

        try:
            water_fraction = sum_values_after_matching_parts(
                parts,
                lambda item: "water" in item or "h2o" in item,
                "water",
            )
        except ValueError:
            # For a two-material silicate/water mixture, use the
            # complement if water is not explicitly given.
            water_fraction = 1.0 - silicate_fraction

        if silicate_fraction <= 0.0:
            raise ValueError(
                "Silicate mass fraction must be greater than zero."
            )

        if water_fraction <= 0.0:
            raise ValueError(
                "Water mass fraction must be greater than zero."
            )

        silicate_water_ratio = silicate_fraction / water_fraction

    except (ValueError, IndexError, StopIteration) as error:
        raise ValueError(
            "Could not extract material, density, and silicate:water "
            f"ratio from model name {model_path.name!r}: {error}"
        ) from error

    return silicate_material, rho, silicate_water_ratio


def find_matching_models(
    reference_model_path: Path,
    model_paths: list[Path],
) -> tuple[list[Path], float | None, float | None]:
    """Find models with the same material, density, and silicate:water ratio."""
    try:
        (
            reference_material,
            reference_rho,
            reference_ratio,
        ) = parse_model_properties(reference_model_path)

    except ValueError as error:
        print(
            f"Warning: {error} The bundle will contain only the ranked "
            "reference model."
        )
        return [reference_model_path], None, None

    matching_models = []

    for model_path in model_paths:
        try:
            material, rho, ratio = parse_model_properties(model_path)
        except ValueError:
            continue

        same_material = material == reference_material

        same_rho = isclose(
            rho,
            reference_rho,
            rel_tol=0.0,
            abs_tol=DENSITY_ABS_TOLERANCE,
        )

        same_ratio = isclose(
            ratio,
            reference_ratio,
            rel_tol=RATIO_REL_TOLERANCE,
            abs_tol=RATIO_ABS_TOLERANCE,
        )

        if same_material and same_rho and same_ratio:
            matching_models.append(model_path)

    if reference_model_path not in matching_models:
        matching_models.append(reference_model_path)

    matching_models.sort(key=lambda path: path.name)

    return matching_models, reference_rho, reference_ratio


def is_same_path(
        first: Path, 
        second: Path
        ) -> bool:
    """Compare existing paths, including paths reached through symlinks."""
    try:
        return first.samefile(second)
    except OSError:
        return first.resolve() == second.resolve()


def make_bundle_name(
        rank: int, 
        reference_model_path: Path
        ) -> str:
    """Create the folder name for one ranked reference-model bundle."""
    reference_name = reference_model_path.name.removesuffix(".optool")
    return f"{rank:02d}_{reference_name}"


def write_bundle_info(
    bundle_dir: Path,
    category_name: str,
    rank: int,
    reference_model_path: Path,
    score_key: str,
    scores: dict[str, float],
    rho: float | None,
    ratio: float | None,
    matching_models: list[Path],
) -> None:
    """Write a small text file describing one model bundle."""
    rho_text = "unavailable" if rho is None else f"{rho:.12g}"
    ratio_text = "unavailable" if ratio is None else f"{ratio:.12g}:1"

    bundle_info = (
        f"Ranking category: {category_name}\n"
        f"Rank: {rank}\n"
        f"Reference model: {reference_model_path.name}\n"
        f"Ranking score: {scores[score_key]:.12e}\n"
        f"Density rho: {rho_text}\n"
        f"Astrosil:water ratio: {ratio_text}\n"
        f"Number of model directories: {len(matching_models)}\n"
        "\nIncluded model directories:\n"
        + "".join(f"- {path.name}\n" for path in matching_models)
    )

    (bundle_dir / "bundle_info.txt").write_text(
        bundle_info,
        encoding="utf-8",
    )


# =====================================================================================
# Laboratory data extraction
# =====================================================================================

try:
    lab_wavelength, lab_kabs, lab_ksca, _lab_g = load_optool_opacity(
        LAB_OPACITY_FILE
    )
except (OSError, ValueError, IndexError) as error:
    raise RuntimeError(
        f"Could not read laboratory opacity file: {LAB_OPACITY_FILE}"
    ) from error

wavelength_min, wavelength_max = WAVELENGTH_INTERVAL
lab_mask = (
    (lab_wavelength >= wavelength_min)
    & (lab_wavelength <= wavelength_max)
)

lab_wavelength_fit = lab_wavelength[lab_mask]
lab_kabs_fit = lab_kabs[lab_mask]
lab_ksca_fit = lab_ksca[lab_mask]

if lab_wavelength_fit.size == 0:
    raise ValueError(
        "Laboratory spectrum contains no entries in interval "
        f"{WAVELENGTH_INTERVAL} µm."
    )

# =====================================================================================
# Model data extraction and RMSE calculation
# =====================================================================================

# Paths are retained throughout the calculation. The basename is used only when
# displaying a model in the terminal, ranking file, or output folder name.
model_paths = sorted(
    (
        path.resolve()
        for path in INPUT_DIR.iterdir()
        if path.is_dir() and (path / OPACITY_FILE_NAME).is_file()
    ),
    key=lambda path: path.name,
)

model_scores: dict[Path, dict[str, float]] = {}

for model_path in model_paths: # Calculate RMSE values for each model in directory.
    opacity_file = model_path / OPACITY_FILE_NAME

    if is_same_path(model_path, LAB_MODEL_PATH):
        print(f"Skipped {model_path.name}: this is the laboratory model.")
        continue

    print(f"Opened {model_path.name} ...")

    try:
        model_wavelength, model_kabs, model_ksca, _model_g = (
            load_optool_opacity(opacity_file)
        )
    except (OSError, ValueError, IndexError) as error:
        print(f"Could not read model {model_path.name!r}: {error}")
        continue

    if (
        lab_wavelength_fit[0] < model_wavelength[0]
        or lab_wavelength_fit[-1] > model_wavelength[-1]
    ):
        print(
            f"Skipped {model_path.name}: model does not cover "
            f"{WAVELENGTH_INTERVAL} µm."
        )
        continue
    # Interpolate each model onto lab wavelength grid so RMSE
    # scores compare opacity values at identical wavelengths.
    model_kabs_fit = np.interp(
        lab_wavelength_fit,
        model_wavelength,
        model_kabs,
    )
    model_ksca_fit = np.interp(
        lab_wavelength_fit,
        model_wavelength,
        model_ksca,
    )

    rmse_abs = rmse(model_kabs_fit, lab_kabs_fit)
    rmse_sca = rmse(model_ksca_fit, lab_ksca_fit)
    rmse_total = (rmse_abs + rmse_sca) / 2.0

    model_scores[model_path] = {
        "rmse_abs": rmse_abs,
        "rmse_sca": rmse_sca,
        "rmse_total": rmse_total,
    }

if not model_scores:
    raise RuntimeError("No valid models were fitted.")

# =====================================================================================
# Rank models based on performance
# =====================================================================================

ranked_models_abs = sorted(
    model_scores.items(),
    key=lambda item: item[1]["rmse_abs"],
)
ranked_models_sca = sorted(
    model_scores.items(),
    key=lambda item: item[1]["rmse_sca"],
)
ranked_models_total = sorted(
    model_scores.items(),
    key=lambda item: item[1]["rmse_total"],
)

all_abs_ranking_text = format_models(
    title="Complete absorption ranking",
    ranked_models=ranked_models_abs,
    score_key="rmse_abs",
)
all_sca_ranking_text = format_models(
    title="Complete scattering ranking",
    ranked_models=ranked_models_sca,
    score_key="rmse_sca",
)
all_total_ranking_text = format_models(
    title="Complete total ranking",
    ranked_models=ranked_models_total,
    score_key="rmse_total",
)

top_abs_ranking_text = format_models(
    title=f"Top {TOP_N} models by absorption RMSE",
    ranked_models=ranked_models_abs,
    score_key="rmse_abs",
    top_n=TOP_N,
)
top_sca_ranking_text = format_models(
    title=f"Top {TOP_N} models by scattering RMSE",
    ranked_models=ranked_models_sca,
    score_key="rmse_sca",
    top_n=TOP_N,
)
top_total_ranking_text = format_models(
    title=f"Top {TOP_N} models by total RMSE",
    ranked_models=ranked_models_total,
    score_key="rmse_total",
    top_n=TOP_N,
)

header_text = (
    "Opacity model fitting results\n"
    "=============================\n\n"
    f"Wavelength interval: {wavelength_min:.3f}-{wavelength_max:.3f} µm\n"
    f"Number of fitted models: {len(model_scores)}\n\n"
)

complete_file_output = (
    header_text
    + all_abs_ranking_text
    + "\n"
    + all_sca_ranking_text
    + "\n"
    + all_total_ranking_text
)

terminal_output = (
    header_text
    + top_abs_ranking_text
    + "\n"
    + top_sca_ranking_text
    + "\n"
    + top_total_ranking_text
)

RANKING_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
RANKING_OUTPUT_FILE.write_text(complete_file_output, encoding="utf-8")

print()
print(terminal_output)
print(f"Complete ranking file created: {RANKING_OUTPUT_FILE}")

# =====================================================================================
# Create ranked model bundles
# =====================================================================================

RANKING_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ranking_categories = (
    ("absorption", ranked_models_abs, "rmse_abs"),
    ("scattering", ranked_models_sca, "rmse_sca"),
    ("overall", ranked_models_total, "rmse_total"),
)

bundle_jobs = []
bundled_source_paths: set[Path] = set()

for category_name, ranked_models, score_key in ranking_categories:
    category_dir = RANKING_OUTPUT_DIR / category_name

    for rank, (reference_model_path, scores) in enumerate(
        ranked_models[:TOP_N],
        start=1,
    ):
        matching_models, rho, ratio = find_matching_models(
            reference_model_path,
            model_paths,
        )

        bundle_dir = category_dir / make_bundle_name(
            rank,
            reference_model_path,
        )

        if bundle_dir.exists():
            raise FileExistsError(
                "Refusing to overwrite an existing model bundle: "
                f"{bundle_dir}"
            )

        bundle_jobs.append(
            {
                "category_name": category_name,
                "rank": rank,
                "reference_model_path": reference_model_path,
                "score_key": score_key,
                "scores": scores,
                "rho": rho,
                "ratio": ratio,
                "matching_models": matching_models,
                "bundle_dir": bundle_dir,
            }
        )
        bundled_source_paths.update(matching_models)

print()
print(f"Copying ranked model bundles to: {RANKING_OUTPUT_DIR}")

try:
    for job in bundle_jobs:
        bundle_dir = job["bundle_dir"]
        bundle_dir.mkdir(parents=True, exist_ok=False)

        for source_model_path in job["matching_models"]:
            destination_model_path = bundle_dir / source_model_path.name
            shutil.copytree(source_model_path, destination_model_path)

        write_bundle_info(
            bundle_dir=bundle_dir,
            category_name=job["category_name"],
            rank=job["rank"],
            reference_model_path=job["reference_model_path"],
            score_key=job["score_key"],
            scores=job["scores"],
            rho=job["rho"],
            ratio=job["ratio"],
            matching_models=job["matching_models"],
        )

        print(
            f"Created {bundle_dir} "
            f"({len(job['matching_models'])} model directories)"
        )

except (OSError, shutil.Error) as error:
    raise RuntimeError(
        "Could not create all model bundles. Original source models were "
        "not modified. Partial output may remain in "
        f"{RANKING_OUTPUT_DIR}."
    ) from error

print(
    f"Copied {len(bundled_source_paths)} unique source models into the "
    "ranked bundles; all originals were retained."
)