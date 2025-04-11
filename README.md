# Bayesian Estimation of Stellar Parameters

## 1. Project Overview

This project aims to use low-resolution spectroscopic data from the LAMOST (Large Sky Area Multi-Object Fiber Spectroscopic Telescope) survey, combined with the PHOENIX theoretical stellar atmosphere models, to perform Bayesian estimation of key stellar physical parameters (effective temperature $T_{\text{eff}}$, surface gravity $\log g$, and metallicity $[\text{Fe/H}]$). The estimated results will be saved in a FITS file.

## 2. Usage

1. **Prepare Data**: Ensure that the required LAMOST catalog, LAMOST spectra files, PHOENIX model spectra files, and the PHOENIX wavelength file are present in the data path specified in `config/settings.py`.

2. **Run the Script**: In the root directory of the project, execute the following command:

   ```bash
   python start.py

1. **View Results**: The program will carry out the parameter estimation process and generate a FITS file containing the estimated parameters at the `OUTPUT_FITS_PATH` specified in `config/settings.py` (default is `output.fits`).

During execution, the program will output log messages indicating processing progress as well as any warnings or errors encountered.

## 3. Configuration

All configurable parameters are centralized in the `config/settings.py` file. Key parameters include:

- **Data Paths**:
  - `LAMOST_CATALOG_PATH`: Path to the LAMOST catalog file.
  - `LAMOST_SPECTRA_DIR`: Directory path containing LAMOST spectra files.
  - `PHOENIX_SPECTRA_DIR`: Directory path containing PHOENIX model spectra files.
  - `PHOENIX_WAVE_PATH`: Path to the PHOENIX model wavelength file.
  - `OUTPUT_FITS_PATH`: Path to the output FITS file with results.
- **Filtering Criteria**:
  - `TARGET_CLASS`: Target object type to be processed (e.g., 'STAR').
  - `MIN_SNRG`: Minimum acceptable signal-to-noise ratio in the g-band.
- **Processing Parameters**:
  - `MIN_VALID_PIXELS`: Minimum number of valid pixels required for a spectrum to be processed.
  - `WAVE_INTERPOLATE_BOUNDS_ERROR`, `WAVE_INTERPOLATE_FILL_VALUE`: Parameters controlling interpolation behavior.
- **Performance Configuration**:
  - `NUM_PROCESSES`: Number of worker processes for parallel processing (default is CPU core count minus one).
  - `MAX_SPECTRA_TO_PROCESS`: (Optional) Limit the number of spectra to process for testing or debugging. Set to `None` to process all spectra that meet the criteria.
- **Output Format**:
  - `OUTPUT_COLUMNS`: Column names to be included in the output FITS file.
  - `OUTPUT_FORMATS`: Data formats for each column in the output FITS file.

Please modify the `config/settings.py` file according to your actual data storage paths and requirements.
