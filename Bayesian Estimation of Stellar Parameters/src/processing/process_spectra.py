import logging
import numpy as np
from scipy.interpolate import interp1d

# 导入配置参数
from config.settings import WAVE_INTERPOLATE_BOUNDS_ERROR, WAVE_INTERPOLATE_FILL_VALUE

def resample_spectrum(target_wave, source_wave, source_flux, bounds_error=WAVE_INTERPOLATE_BOUNDS_ERROR, fill_value=WAVE_INTERPOLATE_FILL_VALUE):
    r"""将源光谱重采样到目标波长网格."""
    try:
        if not np.all(np.diff(source_wave) > 0):
            logging.warning(f"源波长非单调递增，无法插值。Source wave shape: {source_wave.shape}")
            return None
        # 确保目标波长也在源波长的有效范围内 (或使用填充值)
        if not bounds_error:
            target_wave_clipped = np.clip(target_wave, source_wave[0], source_wave[-1])
        else:
            target_wave_clipped = target_wave

        interpolator = interp1d(source_wave, source_flux, kind='linear', bounds_error=bounds_error, fill_value=fill_value)
        resampled_flux = interpolator(target_wave_clipped)
        return resampled_flux
    except ValueError as e:
        # 检查是否是因为 target_wave 超出范围且 bounds_error=True 导致
        if bounds_error and (np.min(target_wave) < source_wave[0] or np.max(target_wave) > source_wave[-1]):
             logging.debug(f"光谱重采样失败，目标波长超出源波长范围: {e}")
        else:
             logging.warning(f"光谱重采样失败: {e}")
        return None
    except Exception as e:
        logging.error(f"光谱重采样时发生意外错误: {e}")
        return None

def normalize_spectrum(flux):
    r"""对光谱流量进行简单的中值归一化."""
    try:
        # 计算时忽略 NaN 值
        median_flux = np.nanmedian(flux)
        if median_flux is not None and median_flux > 0 and np.isfinite(median_flux):
            normalized_flux = flux / median_flux
            return normalized_flux
        elif median_flux == 0:
            logging.warning("中值归一化失败，中值为 0。返回原始流量。")
            return flux
        else:
            logging.warning("无法进行中值归一化 (中值无效或非有限值)，返回原始流量。")
            return flux
    except Exception as e:
        logging.error(f"光谱归一化时出错: {e}")
        return flux # 返回原始流量以允许流程继续

def calculate_log_likelihood(obs_flux_norm, obs_ivar, model_flux_norm):
    r"""计算归一化后的对数似然 (基于卡方)。 L ~ exp(-0.5 * chi2).

    Args:
        obs_flux_norm (np.ndarray): 归一化的观测流量。
        obs_ivar (np.ndarray): 对应的逆方差。
        model_flux_norm (np.ndarray): 归一化的模型流量 (已重采样到观测波长)。

    Returns:
        tuple: (对数似然值, 用于计算的有效像素点数)。
    """
    try:
        # 确保输入是 numpy 数组
        obs_flux_norm = np.asarray(obs_flux_norm)
        obs_ivar = np.asarray(obs_ivar)
        model_flux_norm = np.asarray(model_flux_norm)
        
        # 输入长度检查
        if not (obs_flux_norm.shape == obs_ivar.shape == model_flux_norm.shape):
            logging.error(f"计算对数似然时输入数组形状不匹配: obs={obs_flux_norm.shape}, ivar={obs_ivar.shape}, model={model_flux_norm.shape}")
            return -np.inf, 0
            
        # 筛选有效像素点：观测流量和模型流量都必须是有限的，且逆方差大于0
        valid_comparison = np.isfinite(obs_flux_norm) & np.isfinite(model_flux_norm) & (obs_ivar > 0)
        n_valid = np.sum(valid_comparison)

        if n_valid == 0:
            # logging.debug("计算对数似然时没有有效的比较像素点。")
            return -np.inf, 0 # 没有有效点，似然为负无穷

        # 提取有效点的数据
        obs_f = obs_flux_norm[valid_comparison]
        mod_f = model_flux_norm[valid_comparison]
        ivar_f = obs_ivar[valid_comparison]
        
        # 计算卡方值
        chi2 = np.sum(((obs_f - mod_f)**2) * ivar_f)

        # 检查 chi2 是否有效
        if not np.isfinite(chi2) or chi2 < 0:
            logging.warning(f"计算得到无效的卡方值: {chi2}. 有效点数: {n_valid}. 返回 -inf.")
            return -np.inf, n_valid

        # 计算对数似然
        log_likelihood = -0.5 * chi2

        # 再次检查最终结果
        if not np.isfinite(log_likelihood):
            logging.warning(f"计算得到非有限对数似然值: {log_likelihood}, chi2={chi2}. 有效点数: {n_valid}. 返回 -inf.")
            return -np.inf, n_valid

        return log_likelihood, n_valid

    except Exception as e:
        logging.error(f"计算对数似然时发生意外错误: {e}")
        return -np.inf, 0 # 出错时返回负无穷和0个有效点 