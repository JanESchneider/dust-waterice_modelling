
GRAIN_AMIN=0.001
GRAIN_AMAX=0.1
GRAIN_APOW=3.5
GRAIN_METHOD="dhs"
DHS_FMAX=0.8
WAVELENGTH_MIN=1
WAVELENGTH_MAX=20
N_WAVELENGTHS=1000

#LAB_NK_FILE="/home/jschneider/Projects/dust_ice/data/data_jena-db_MgFeSiO4.lnk"
LAB_NK_FILE="/home/jschneider/Projects/dust_ice/data/nk_data_potapov/MgSiO3_H2O_200K_7_5/MgSiO3_H2O_200K_7_5.lnk"
LAB_OUTPUT_DIR="/home/jschneider/Projects/dust_ice/data/dust_potapov/MgSiO3_H2O_200K_7_5"

OPTOOL="/home/jschneider/optool/optool"

"$OPTOOL" \
    -c "$LAB_NK_FILE" \
    -a "$GRAIN_AMIN" "$GRAIN_AMAX" "$GRAIN_APOW" \
    -l "$WAVELENGTH_MIN" "$WAVELENGTH_MAX" "$N_WAVELENGTHS" \
    -dhs "$DHS_FMAX" \
    -o "$LAB_OUTPUT_DIR"