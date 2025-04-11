# 基于贝叶斯估计的恒星参数推断

## 1. 项目概要

本项目旨在使用 LAMOST (Large Sky Area Multi-Object Fiber Spectroscopic Telescope) 巡天项目提供的低分辨率光谱数据，结合 PHOENIX 理论恒星大气模型，对恒星的关键物理参数（有效温度 $T_{\text{eff}}$、表面重力 $\log g$、金属丰度 $[\text{Fe/H}]$）进行贝叶斯估计，并将估计结果保存为 FITS 文件。

## 2. 使用方法

1. **准备数据**: 确保 `config/settings.py` 中指定的数据路径下存在所需的 LAMOST 星表、LAMOST 光谱文件、PHOENIX 模型光谱文件和 PHOENIX 波长文件。

2. **运行脚本**: 在项目根目录下，执行以下命令：

   ```bash
   python start.py
   ```

3. **查看结果**: 程序将执行参数估计流程，并在 `config/settings.py` 中指定的 `OUTPUT_FITS_PATH` （默认为 `output.fits`）生成包含估计参数的 FITS 文件。

程序运行时会输出日志信息，显示处理进度和可能遇到的警告或错误。

## 3. 配置

所有可配置的参数都集中在 `config/settings.py` 文件中。主要参数包括：

*   **数据路径**: 
    *   `LAMOST_CATALOG_PATH`: LAMOST 星表文件路径。
    *   `LAMOST_SPECTRA_DIR`: 存储 LAMOST 光谱文件的目录路径。
    *   `PHOENIX_SPECTRA_DIR`: 存储 PHOENIX 模型光谱文件的目录路径。
    *   `PHOENIX_WAVE_PATH`: PHOENIX 模型对应的波长文件路径。
    *   `OUTPUT_FITS_PATH`: 输出结果 FITS 文件的路径。
*   **筛选条件**: 
    *   `TARGET_CLASS`: 需要处理的目标天体类型（例如 'STAR'）。
    *   `MIN_SNRG`: 接受的光谱信噪比（例如 g 波段）的最小值。
*   **处理参数**: 
    *   `MIN_VALID_PIXELS`: 光谱进行有效处理所需的最少有效像素点数量。
    *   `WAVE_INTERPOLATE_BOUNDS_ERROR`, `WAVE_INTERPOLATE_FILL_VALUE`: 控制插值行为的参数。
*   **性能配置**: 
    *   `NUM_PROCESSES`: 用于并行处理的工作进程数量（默认为 CPU 核心数减 1）。
    *   `MAX_SPECTRA_TO_PROCESS`: (可选) 限制处理的光谱数量，用于测试或调试。设为 `None` 则处理所有符合条件的光谱。
*   **输出格式**: 
    *   `OUTPUT_COLUMNS`: 输出 FITS 文件包含的列名。
    *   `OUTPUT_FORMATS`: 输出 FITS 文件中各列的数据格式。

请根据你的实际数据存储位置和需求修改 `config/settings.py` 文件。



## 4. 数学原理

本项目的核心是基于观测光谱数据 $D$ 对恒星参数 $\theta = \{T_{\text{eff}}, \log g, [\text{Fe/H]}\}$ 进行估计。我们采用最大似然估计方法，在一个预定义的 PHOENIX 理论模型参数网格 $\{\theta_i\}$ 上寻找最佳匹配。

**似然函数**: 假设观测光谱每个像素点的误差服从独立的高斯分布，其似然函数 $\mathcal{L}(D | \theta)$ 可以通过卡方 $\chi^2(\theta)$ 来表示：

$mathcal{L}(D | \theta) \propto \exp\left(-\frac{1}{2} \chi^2(\theta)\right)$

**卡方计算**: 卡方值衡量了模型光谱与观测光谱之间的差异，并考虑了观测误差（用逆方差 `ivar` 表示）：

$chi^2(\theta) = \sum_{j \in \text{valid}} \left( \frac{ \text{flux}_{\text{obs}, j}^{\text{norm}} - \text{flux}_{\text{model}, j}^{\text{norm}}(\theta) }{ \sigma_j^{\text{norm}} } \right)^2 = \sum_{j \in \text{valid}} \left( \text{flux}_{\text{obs}, j}^{\text{norm}} - \text{flux}_{\text{model}, j}^{\text{norm}}(\theta) \right)^2 \cdot \text{ivar}_{\text{obs}, j}^{\text{norm}}$

其中：
*   $j$ 遍历所有有效的像素点（通常指 `mask` 值为 0 且 `ivar` > 0 的像素）。
*   $\text{flux}^{\text{norm}}$ 表示归一化后的流量。代码中使用了简单的中值归一化。
*   $\text{flux}_{\text{model}, j}^{\text{norm}}(\theta)$ 是将参数为 $\theta$ 的 PHOENIX 模型光谱重采样到观测波长网格 $\text{wave}_{\text{obs}}$，并进行相同归一化后的模型流量。
*   $\text{ivar}_{\text{obs}, j}^{\text{norm}}$ 是归一化观测流量对应的逆方差。注意：理论上，归一化操作会改变逆方差，但当前代码实现中直接使用了原始光谱的 `ivar` 值进行计算，这可能是一个简化处理。

**对数似然**: 在实际计算中，通常使用对数似然 $\ln \mathcal{L}$，以避免数值下溢并简化计算：

$ \ln \mathcal{L}(D | \theta) = -\frac{1}{2} \chi^2(\theta) + \text{const} $

代码中的 `calculate_log_likelihood` 函数计算并返回了 $-0.5 \chi^2(\theta)$ 部分。

**参数估计**: 项目通过计算 PHOENIX 模型网格中每个参数点 $\theta_i$ 对应的对数似然值，然后选择使对数似然最大化的参数 $\hat{\theta}$ 作为最佳估计：

$ \hat{\theta} = \underset{\theta_i \in \text{Grid}}{\operatorname{argmax}} \ln \mathcal{L}(D | \theta_i) $

这种方法等价于假设在模型参数网格点上具有均匀先验分布时的最大后验概率估计 (Maximum A Posteriori, MAP)。最终得到的 $\hat{\theta} = \{\hat{T}_{\text{eff}}, \hat{\log g}, [\widehat{\text{Fe/H}}]\}$ 即为估计的恒星参数。 