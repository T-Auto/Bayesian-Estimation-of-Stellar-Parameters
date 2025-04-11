import logging
import numpy as np
import os

# 导入配置
from config.settings import MIN_VALID_PIXELS

# 导入数据加载和处理函数
from src.loading.load_data import load_lamost_spectrum, load_phoenix_spectrum
from src.processing.process_spectra import resample_spectrum, normalize_spectrum, calculate_log_likelihood

def process_spectrum_task(task_data, phoenix_grid, phoenix_wave):
    r"""处理单个 LAMOST 光谱的任务函数 (用于多进程).

    Args:
        task_data (dict): 包含 'spec_info' (光谱文件信息) 和 'target_info' (包含obsid,ra,dec的字典).
        phoenix_grid (list): PHOENIX 模型网格列表。
        phoenix_wave (np.ndarray): PHOENIX 波长数组。

    Returns:
        dict or None: 包含结果的字典，如果处理失败则返回 None。
    """
    spec_info = task_data['spec_info']
    target_info = task_data['target_info']
    obsid = target_info.get('obsid', '未知')
    filepath = spec_info['filepath']

    # --- 光谱加载与处理 --- 
    # 在子进程中，日志通常需要特殊配置才能输出到主控制台
    # logging.debug(f"[Worker {os.getpid()}] 处理光谱文件: {filepath} (obsid={obsid})")
    lamost_spec_data = load_lamost_spectrum(filepath, obsid_for_log=obsid)
    if lamost_spec_data is None:
        return None

    # 预处理 LAMOST 光谱
    good_pixels = (lamost_spec_data['mask'] == 0) & \
                  (lamost_spec_data['ivar'] > 0) & \
                  np.isfinite(lamost_spec_data['flux']) & \
                  np.isfinite(lamost_spec_data['ivar'])
    n_good_pixels = np.sum(good_pixels)

    if n_good_pixels < MIN_VALID_PIXELS:
        # logging.debug(f"[Worker {os.getpid()}] 跳过 obsid={obsid}: 有效像素点过少 ({n_good_pixels}). 文件: {filepath}")
        return None

    obs_flux = lamost_spec_data['flux'][good_pixels]
    obs_ivar = lamost_spec_data['ivar'][good_pixels]
    obs_wave = lamost_spec_data['wave'][good_pixels]

    # 归一化观测光谱
    obs_flux_norm = normalize_spectrum(obs_flux)
    if obs_flux_norm is None:
        # logging.warning(f"[Worker {os.getpid()}] 跳过 obsid={obsid}: 观测光谱归一化失败。")
        return None

    # --- 参数推断 --- 
    best_log_likelihood = -np.inf
    best_n_valid = 0
    best_params = None

    for model_params in phoenix_grid:
        phoenix_flux = load_phoenix_spectrum(model_params['filepath'])
        if phoenix_flux is None:
            continue
            
        if len(phoenix_flux) != len(phoenix_wave):
            # logging.warning(f"[Worker {os.getpid()}] 跳过模型 {model_params['filepath']} (obsid={obsid}): 流量长度 ({len(phoenix_flux)}) 与波长长度 ({len(phoenix_wave)}) 不匹配。")
            continue
            
        # 重采样模型光谱到观测波长网格
        model_flux_resampled = resample_spectrum(obs_wave, phoenix_wave, phoenix_flux)
        if model_flux_resampled is None:
            # 重采样失败的消息已在 resample_spectrum 中记录
            continue
            
        # 归一化模型光谱
        model_flux_norm = normalize_spectrum(model_flux_resampled)
        if model_flux_norm is None:
            # logging.warning(f"[Worker {os.getpid()}] 跳过模型 {model_params['filepath']} for obsid={obsid}: 模型归一化失败。")
            continue
            
        # 计算对数似然
        current_log_likelihood, current_n_valid = calculate_log_likelihood(obs_flux_norm, obs_ivar, model_flux_norm)

        # 更新最佳匹配
        if current_log_likelihood > best_log_likelihood:
            best_log_likelihood = current_log_likelihood
            best_n_valid = current_n_valid
            best_params = model_params

    # --- 准备结果 --- 
    if best_params is not None:
        ra_val = target_info.get('ra', np.nan)
        dec_val = target_info.get('dec', np.nan)
        result_dict = {
            'obsid': obsid,
            'ra': ra_val,
            'dec': dec_val,
            'teff_est': best_params['teff'],
            'logg_est': best_params['logg'],
            'feh_est': best_params['feh'],
            'best_logL': best_log_likelihood,
            'n_valid_pix': best_n_valid,
            'phoenix_model_path': os.path.basename(best_params['filepath'])
        }
        # logging.debug(f"[Worker {os.getpid()}] 成功处理 obsid={obsid}")
        return result_dict
    else:
        # logging.warning(f"[Worker {os.getpid()}] 未能为 obsid={obsid} (文件: {filepath}) 找到合适的 PHOENIX 模型匹配。")
        return None 