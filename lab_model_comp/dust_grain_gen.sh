#!/usr/bin/env bash

set -euo pipefail
export LC_ALL=C

# =============================================================================
# Paths
# =============================================================================

SIL_DIR="/home/jschneider/Projects/dust_ice/data"

WATER_FILE="/home/jschneider/Projects/dust_ice/data/nk_data_potapov/trans_water_150.lnk"
OUTPUT_DIR="/home/jschneider/Projects/dust_ice/data/dust_models"

OPTOOL="/home/jschneider/optool/optool"

# -----------------------------------------------------------------------------
# Grain size distribution
# -----------------------------------------------------------------------------

# Grain size distribution values taken from Potapov et al. 2025 

GRAIN_AMIN=0.001       # Minimum grain radius [micron]
GRAIN_AMAX=0.1         # Maximum grain radius [micron]
GRAIN_APOW=3.5         # Power-law exponent

GRAIN_NA=""

# -----------------------------------------------------------------------------
# Wavelength grid
# -----------------------------------------------------------------------------

WAVELENGTH_MIN=1         # Minimum wavelength [micron]
WAVELENGTH_MAX=20        # Maximum wavelength [micron]
N_WAVELENGTHS=1000       # Number of wavelength points

CORE_POROSITY=0.0
MANTLE_POROSITY=0.0

GRAIN_METHOD="dhs"
DHS_FMAX=0.8

XLIM=1000

# Silicate : total water mass ratios.
RATIOS=(
    2.7
    4.5
    7.5
)

MANTLE_WATER_FRACTIONS=(
    0.00
)

# =============================================================================
# Checks
# =============================================================================

if [[ ! -d "$SIL_DIR" ]]; then
    echo "ERROR: Silicate directory does not exist: $SIL_DIR" >&2
    exit 1
fi

if [[ ! -f "$WATER_FILE" ]]; then
    echo "ERROR: Water file does not exist: $WATER_FILE" >&2
    exit 1
fi

if [[ ! -x "$OPTOOL" ]]; then
    echo "ERROR: optool executable not found or not executable: $OPTOOL" >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

shopt -s nullglob

sil_fileS=("$SIL_DIR"/*.lnk)

if (( ${#sil_fileS[@]} == 0 )); then
    echo "ERROR: No .lnk files found in: $SIL_DIR" >&2
    exit 1
fi


# =============================================================================
# Build common optool arguments
# =============================================================================

GRAIN_ARGS=(
    -a
    "$GRAIN_AMIN"
    "$GRAIN_AMAX"
    "$GRAIN_APOW"
)

# Add explicit number of grain sizes only if requested.
if [[ -n "$GRAIN_NA" ]]; then
    GRAIN_ARGS+=("$GRAIN_NA")
fi


WAVELENGTH_ARGS=(
    -l
    "$WAVELENGTH_MIN"
    "$WAVELENGTH_MAX"
    "$N_WAVELENGTHS"
)


POROSITY_ARGS=(
    -p
    "$CORE_POROSITY"
    "$MANTLE_POROSITY"
)


case "$GRAIN_METHOD" in
    dhs)
        GEOMETRY_ARGS=(
            -dhs "$DHS_FMAX"
        )
        ;;

    mie)
        GEOMETRY_ARGS=(
            -mie
        )
        ;;

    *)
        echo "ERROR: Unknown GRAIN_METHOD: $GRAIN_METHOD" >&2
        echo "Supported values: dhs, mie" >&2
        exit 1
        ;;
esac


if [[ -n "$XLIM" ]]; then
    GEOMETRY_ARGS+=(
        -xlim "$XLIM"
    )
fi


# =============================================================================
# Print configuration
# =============================================================================

echo
echo "============================================================"
echo "Dust model configuration"
echo "============================================================"
echo "Grain radius:"
echo "  amin       = $GRAIN_AMIN micron"
echo "  amax       = $GRAIN_AMAX micron"
echo "  power law  = $GRAIN_APOW"

if [[ -n "$GRAIN_NA" ]]; then
    echo "  size bins  = $GRAIN_NA"
else
    echo "  size bins  = optool default"
fi

echo
echo "Wavelength grid:"
echo "  min        = $WAVELENGTH_MIN micron"
echo "  max        = $WAVELENGTH_MAX micron"
echo "  points     = $N_WAVELENGTHS"

echo
echo "Porosity:"
echo "  core       = $CORE_POROSITY"
echo "  mantle     = $MANTLE_POROSITY"

echo
echo "Geometry:"
echo "  method     = $GRAIN_METHOD"

if [[ "$GRAIN_METHOD" == "dhs" ]]; then
    echo "  DHS fmax   = $DHS_FMAX"
fi

if [[ -n "$XLIM" ]]; then
    echo "  xlim       = $XLIM"
else
    echo "  xlim       = optool default"
fi

echo "============================================================"
echo


# =============================================================================
# Generate dust models
# =============================================================================

for sil_file in "${sil_fileS[@]}"; do

    # -------------------------------------------------------------------------
    # Read density from .lnk file
    # -------------------------------------------------------------------------

    sil_density=$(
        awk '
            /^[[:space:]]*[!#*]/ { next }

            NF {
                print $2
                exit
            }
        ' "$sil_file"
    )

    if [[ -z "$sil_density" ]]; then
        echo "WARNING: Could not determine density from: $sil_file" >&2
        continue
    fi


    echo "============================================================"
    echo "SILicate file:    $sil_file"
    echo "SILicate density: $sil_density g/cm^3"
    echo "============================================================"


    for ratio in "${RATIOS[@]}"; do

        # ---------------------------------------------------------------------
        # Total grain mass fractions
        #
        # SIL : water = ratio : 1
        #
        # f_SIL = ratio / (ratio + 1)
        # f_water    = 1     / (ratio + 1)
        # ---------------------------------------------------------------------

        sil_mf=$(
            awk -v r="$ratio" '
                BEGIN {
                    printf "%.6f", r / (r + 1.0)
                }
            '
        )

        water_total_mf=$(
            awk -v r="$ratio" '
                BEGIN {
                    printf "%.6f", 1.0 / (r + 1.0)
                }
            '
        )


        for mantle_fraction in "${MANTLE_WATER_FRACTIONS[@]}"; do

            # -----------------------------------------------------------------
            # Water in core
            # -----------------------------------------------------------------

            water_core_mf=$(
                awk \
                    -v fw="$water_total_mf" \
                    -v xm="$mantle_fraction" '
                    BEGIN {
                        printf "%.6f", fw * (1.0 - xm)
                    }
                '
            )


            # -----------------------------------------------------------------
            # Water in mantle
            # -----------------------------------------------------------------

            water_mantle_mf=$(
                awk \
                    -v fw="$water_total_mf" \
                    -v xm="$mantle_fraction" '
                    BEGIN {
                        printf "%.6f", fw * xm
                    }
                '
            )


            # -----------------------------------------------------------------
            # Output directory
            # -----------------------------------------------------------------

            model_name="rho_${sil_density}"\
"_sil_${sil_mf}"\
"_waterCore_${water_core_mf}"\
"_waterMantle_${water_mantle_mf}"\
"_ratio_${ratio}to1"

            model_dir="$OUTPUT_DIR/$model_name"

            mkdir -p "$model_dir"


            # -----------------------------------------------------------------
            # Build optool command
            # -----------------------------------------------------------------

            cmd=(
                "$OPTOOL"

                # Composition
                -c "$sil_file" "$sil_mf"

                # Grain size distribution
                "${GRAIN_ARGS[@]}"

                # Wavelength grid
                "${WAVELENGTH_ARGS[@]}"

                # Porosity
                "${POROSITY_ARGS[@]}"

                # Grain geometry
                "${GEOMETRY_ARGS[@]}"
            )


            # -----------------------------------------------------------------
            # Add water to core
            # -----------------------------------------------------------------

            if awk -v f="$water_core_mf" \
                'BEGIN { exit !(f > 0.0) }'
            then
                cmd+=(
                    -c "$WATER_FILE" "$water_core_mf"
                )
            fi


            # -----------------------------------------------------------------
            # Add water to mantle
            # -----------------------------------------------------------------

            if awk -v f="$water_mantle_mf" \
                'BEGIN { exit !(f > 0.0) }'
            then
                cmd+=(
                    -m "$WATER_FILE" "$water_mantle_mf"
                )
            fi


            cmd+=(
                -o "$model_dir"
                -err
            )


            # -----------------------------------------------------------------
            # Run optool
            # -----------------------------------------------------------------

            echo
            echo "Generating: $model_name"
            echo "  sil file:              $(basename "$sil_file")"
            echo "  sil density:           $sil_density g/cm^3"
            echo "  sil mass fraction:     $sil_mf"
            echo "  Water core mass fraction:   $water_core_mf"
            echo "  Water mantle mass fraction: $water_mantle_mf"
            echo "  sil:water ratio:       ${ratio}:1"
            echo "  Grain sizes:                $GRAIN_AMIN - $GRAIN_AMAX micron"
            echo "  Grain power law:            $GRAIN_APOW"
            echo "  Wavelengths:                $WAVELENGTH_MIN - $WAVELENGTH_MAX micron"
            echo "  Geometry:                   $GRAIN_METHOD"

            printf "  Command:"
            printf " %q" "${cmd[@]}"
            printf "\n\n"

            "${cmd[@]}"

        done
    done
done


echo
echo "============================================================"
echo "Finished generating dust models."
echo "Output directory: $OUTPUT_DIR"
echo "============================================================"