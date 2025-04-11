import os
import numpy as np

# --- 数据路径 ---
LAMOST_CATALOG_PATH = 'data/LAMOST/dr11_v1.1_LRS_catalogue.fits'
LAMOST_SPECTRA_DIR = 'data/LAMOST/光谱'
PHOENIX_SPECTRA_DIR = 'data/phoenix_v2'
OUTPUT_FITS_PATH = 'output.fits'
PHOENIX_WAVE_PATH = 'data/WAVE_PHOENIX-ACES-AGSS-COND-2011.fits'

# --- 筛选条件 ---
TARGET_CLASS = 'STAR'
MIN_SNRG = 10 # g波段信噪比阈值

# --- 处理参数 ---
MIN_VALID_PIXELS = 100 # 处理光谱所需的最少有效像素点
WAVE_INTERPOLATE_BOUNDS_ERROR = False # 插值时是否因超出边界而报错
WAVE_INTERPOLATE_FILL_VALUE = np.nan # 插值超出边界时的填充值

# --- 多进程配置 ---
# 使用 CPU 核心数减 1，留一个核心给系统, 最少为 1
NUM_PROCESSES = max(1, os.cpu_count() - 1 if os.cpu_count() else 1)

# --- 限制处理数量 (用于测试) ---
# 设置为 None 则处理所有通过筛选的光谱
MAX_SPECTRA_TO_PROCESS = 500 # 或者 None

# --- 输出FITS文件列 ---
OUTPUT_COLUMNS = ['obsid', 'ra', 'dec', 'teff_est', 'logg_est', 'feh_est', 'best_logL', 'n_valid_pix', 'phoenix_model_path']
OUTPUT_FORMATS = {
    'ra': '%.6f',
    'dec': '%.6f',
    'teff_est': '%d',
    'logg_est': '%.2f',
    'feh_est': '%.2f',
    'best_logL': '%.4e',
    'n_valid_pix': '%d',
    'phoenix_model_path': '%s'
} 