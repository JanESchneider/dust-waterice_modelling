
GRAIN_AMIN=0.005
GRAIN_AMAX=1
GRAIN_APOW=3.5
GRAIN_METHOD="dhs"
DHS_FMAX=0.8
WAVELENGTH_MIN=2.5
WAVELENGTH_MAX=4.0
N_WAVELENGTHS=1000

LAB_NK_FILE="/home/jschneider/Proj_WaterIce/data/nk_data_potapov/MgFeSiO4/MgFeSiO4.lnk"
LAB_OUTPUT_DIR="/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/dust_labdata/"

OPTOOL="/home/jschneider/optool/optool"

"$OPTOOL" \
    -c "$LAB_NK_FILE" 1.0 \
    -a "$GRAIN_AMIN" "$GRAIN_AMAX" "$GRAIN_APOW" \
    -l "$WAVELENGTH_MIN" "$WAVELENGTH_MAX" "$N_WAVELENGTHS" \
    -dhs "$DHS_FMAX" \
    -o "$LAB_OUTPUT_DIR"