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

## 4. Mathematical Principles

The core of this project is to estimate stellar parameters $\theta = {T_{\text{eff}}, \log g, [\text{Fe/H}]}$ from observed spectral data $D$. We adopt a maximum likelihood estimation method to search for the best match on a predefined PHOENIX model parameter grid ${\theta_i}$.

**Likelihood Function**: Assuming the error at each pixel of the observed spectrum follows an independent Gaussian distribution, the likelihood function $\mathcal{L}(D | \theta)$ can be expressed in terms of the chi-squared statistic $\chi^2(\theta)$:

$\mathcal{L}(D | \theta) \propto \exp\left(-\frac{1}{2} \chi^2(\theta)\right)$

**Chi-squared Calculation**: The chi-squared value quantifies the difference between the model spectrum and the observed spectrum, taking into account the observational error (represented by inverse variance `ivar`):

$\chi^2(\theta) = \sum_{j \in \text{valid}} \left( \frac{ \text{flux}*{\text{obs}, j}^{\text{norm}} - \text{flux}*{\text{model}, j}^{\text{norm}}(\theta) }{ \sigma_j^{\text{norm}} } \right)^2 = \sum_{j \in \text{valid}} \left( \text{flux}*{\text{obs}, j}^{\text{norm}} - \text{flux}*{\text{model}, j}^{\text{norm}}(\theta) \right)^2 \cdot \text{ivar}_{\text{obs}, j}^{\text{norm}}$

Where:

- $j$ iterates over all valid pixels (typically those with `mask` = 0 and `ivar` > 0).
- $\text{flux}^{\text{norm}}$ denotes the normalized flux. In the code, a simple median normalization is used.
- $\text{flux}*{\text{model}, j}^{\text{norm}}(\theta)$ is the model flux for parameters $\theta$, resampled to the observed wavelength grid $\text{wave}*{\text{obs}}$, and normalized in the same way.
- $\text{ivar}_{\text{obs}, j}^{\text{norm}}$ is the inverse variance of the normalized observed flux. Note: In theory, the normalization process alters the inverse variance, but in the current implementation, the original `ivar` is directly used for simplicity.

**Log-Likelihood**: In practice, the log-likelihood $\ln \mathcal{L}$ is used to avoid numerical underflow and to simplify computation:

$ \ln \mathcal{L}(D | \theta) = -\frac{1}{2} \chi^2(\theta) + \text{const} $

The `calculate_log_likelihood` function in the code computes and returns the $-0.5 \chi^2(\theta)$ part.

**Parameter Estimation**: The project computes the log-likelihood for each parameter point $\theta_i$ in the PHOENIX model grid and selects the parameter $\hat{\theta}$ that maximizes the log-likelihood as the best estimate:

$ \hat{\theta} = \underset{\theta_i \in \text{Grid}}{\operatorname{argmax}} \ln \mathcal{L}(D | \theta_i) $

This method is equivalent to Maximum A Posteriori (MAP) estimation under the assumption of a uniform prior over the model grid points. The final estimated stellar parameters are $\hat{\theta} = {\hat{T}_{\text{eff}}, \hat{\log g}, [\widehat{\text{Fe/H}}]}$.