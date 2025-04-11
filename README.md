# Bayesian Estimation of Stellar Parameters
[[English]](README.md) ✅

[[简体中文]](README_zh.md) 
## 1. Project Overview

This project reads spectral files provided by astronomical telescopes like LAMOST or Gaia, performs Bayesian estimation of key stellar physical parameters (effective temperature $T_{\text{eff}}$, surface gravity $\log g$, metallicity $[\text{Fe/H}]$), and saves the estimation results as .fits files.

Another project by our team, [A python tool library for astronomy](https://github.com/T-Auto/Python-tools-for-Astronomy), provides necessary tools for this solution, such as information reading, catalog cross-matching, and error calculation.

## 2. Usage

Taking the parameter estimation using low-resolution spectral data provided by the LAMOST (Large Sky Area Multi-Object Fiber Spectroscopic Telescope) survey project as an example:

1.  **Prepare Data**: Ensure that the required LAMOST catalog, LAMOST spectral files, PHOENIX model spectral files, and PHOENIX wavelength file exist in the data paths specified in `config/settings.py`.

2.  **Run Script**: In the project root directory, execute the following command:

    ```bash
    python start.py
    ```

3.  **Check Results**: The program will execute the parameter estimation process and generate a FITS file containing the estimated parameters at the `OUTPUT_FITS_PATH` specified in `config/settings.py` (defaults to `output.fits`).

During runtime, the program will output log information, displaying the processing progress and any potential warnings or errors.

## 3. Configuration

All configurable parameters are centralized in the `config/settings.py` file. Key parameters include:

*   **Data Paths**:
    *   `LAMOST_CATALOG_PATH`: Path to the LAMOST catalog file.
    *   `LAMOST_SPECTRA_DIR`: Directory path storing LAMOST spectral files.
    *   `PHOENIX_SPECTRA_DIR`: Directory path storing PHOENIX model spectral files.
    *   `PHOENIX_WAVE_PATH`: Path to the wavelength file corresponding to the PHOENIX models.
    *   `OUTPUT_FITS_PATH`: Path for the output results FITS file.
*   **Filtering Criteria**:
    *   `TARGET_CLASS`: Target object type to process (e.g., 'STAR').
    *   `MIN_SNRG`: Minimum acceptable signal-to-noise ratio (SNR) of the spectrum (e.g., in the g-band).
*   **Processing Parameters**:
    *   `MIN_VALID_PIXELS`: Minimum number of valid pixels required for a spectrum to be processed effectively.
    *   `WAVE_INTERPOLATE_BOUNDS_ERROR`, `WAVE_INTERPOLATE_FILL_VALUE`: Parameters controlling interpolation behavior.
*   **Performance Configuration**:
    *   `NUM_PROCESSES`: Number of worker processes for parallel processing (defaults to the number of CPU cores minus 1).
    *   `MAX_SPECTRA_TO_PROCESS`: (Optional) Limit the number of spectra to process, useful for testing or debugging. Set to `None` to process all qualifying spectra.
*   **Output Format**:
    *   `OUTPUT_COLUMNS`: Column names to include in the output FITS file.
    *   `OUTPUT_FORMATS`: Data formats for each column in the output FITS file.

Please modify the `config/settings.py` file according to your actual data storage locations and requirements.
