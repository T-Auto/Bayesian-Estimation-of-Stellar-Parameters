# 基于贝叶斯估计的恒星参数推断
[[Englishi]](README.md)

[[简体中文]](README_zh.md)✅
## 1. 项目概要

本项目可以读取来自LAMOST或Gaia天文望远镜提供的光谱文件，对恒星的关键物理参数（有效温度 $T_{\text{eff}}$、表面重力 $\log g$、金属丰度 $[\text{Fe/H}]$）进行贝叶斯估计，并将估计结果保存为.fits文件。

本团队的另一个项目[A python tool library for astronomy](https://github.com/T-Auto/Python-tools-for-Astronomy)提供了本方案所需的信息读取、星表交叉、误差计算等工具。

## 2. 使用方法

使用示例视频：

https://private-user-images.githubusercontent.com/160485532/433817983-edfbe05c-6cfd-4b5d-8ee7-5cf5f71df3f1.mp4?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDQ3MTc4MTcsIm5iZiI6MTc0NDcxNzUxNywicGF0aCI6Ii8xNjA0ODU1MzIvNDMzODE3OTgzLWVkZmJlMDVjLTZjZmQtNGI1ZC04ZWU3LTVjZjVmNzFkZjNmMS5tcDQ_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUwNDE1JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MDQxNVQxMTQ1MTdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1iNzYyMDcxZGE2ZDE1NzgwZGQ2OGMyOWEyM2I2NjQ3MDYzMmU2YWE0YWNiMTJiYTFiZmM1ZDMyNWNlN2Q3NjNjJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.LapN4AunfZwT9oYrjbDpe9G2QuArTgyd3d36WFWPgH0

以使用LAMOST (Large Sky Area Multi-Object Fiber Spectroscopic Telescope) 巡天项目提供的低分辨率光谱数据进行参数推算为例。

1. **准备数据**: 确保 `config/settings.py` 中指定的数据路径下存在所需的 LAMOST 星表、LAMOST 光谱文件、PHOENIX 模型光谱文件和 PHOENIX 波长文件。

2. **运行脚本**: 在项目根目录下，执行以下命令：

   ```bash
   python start.py
   ```

3. **查看结果**: 程序将执行参数估计流程，并在 `config/settings.py` 中指定的 `OUTPUT_FITS_PATH` （默认为 `output.fits`）生成包含估计参数的 FITS 文件。

程序运行时会输出日志信息，显示处理进度和可能遇到的警告或错误。

## 3. 参数配置

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
