import os
import re
import logging
from astropy.io import fits
from astropy.table import Table
import numpy as np
from tqdm import tqdm

# --- LAMOST 数据加载 --- 

def load_lamost_catalog(catalog_path):
    r"""加载 LAMOST 总星表 FITS 文件."""
    try:
        with fits.open(catalog_path) as hdul:
            catalog_data = Table(hdul[1].data)
        logging.info(f"成功加载 LAMOST 星表: {catalog_path}, 共 {len(catalog_data)} 条记录.")
        return catalog_data
    except FileNotFoundError:
        logging.error(f"错误: LAMOST 星表文件未找到: {catalog_path}")
        return None
    except Exception as e:
        logging.error(f"加载 LAMOST 星表时出错: {e}")
        return None

def build_catalog_lookup(catalog):
    r"""根据星表构建 (lmjd, planid, spid, fiberid) -> row_index 的查找字典."""
    logging.info("开始构建 LAMOST 星表查找字典...")
    lookup = {}
    required_cols = ['lmjd', 'planid', 'spid', 'fiberid']
    if not all(col in catalog.colnames for col in required_cols):
        logging.error(f"星表缺少构建查找字典所需的列: {required_cols}")
        return None

    # 预处理 planid 列，去除所有行的前后空格
    # 创建新列以避免修改原始 Table
    planid_clean = np.char.strip(catalog['planid'].astype(str))

    for i in tqdm(range(len(catalog)), desc="构建星表查找字典"):
        try:
            key = (int(catalog['lmjd'][i]), planid_clean[i], int(catalog['spid'][i]), int(catalog['fiberid'][i]))
            if key not in lookup:
                lookup[key] = i
        except (ValueError, TypeError) as e:
            logging.warning(f"构建查找字典时跳过行 {i}: 无法处理键值 ({catalog['lmjd'][i]}, {catalog['planid'][i]}, {catalog['spid'][i]}, {catalog['fiberid'][i]}). Error: {e}")
            continue

    logging.info(f"星表查找字典构建完成，包含 {len(lookup)} 个唯一键。")
    return lookup

def scan_and_parse_lamost_spectra(spectra_dir):
    r"""扫描 LAMOST 光谱目录，解析文件名，返回包含光谱信息和路径的列表."""
    logging.info(f"开始扫描 LAMOST 光谱目录: {spectra_dir}")
    available_spectra = []
    spec_pattern = re.compile(r"spec-(\d{5})-([A-Za-z0-9\-]+)_sp(\d{2})-(\d{3})\.fits(?:\.gz)?")

    try:
        if not os.path.isdir(spectra_dir):
            raise FileNotFoundError(f"LAMOST 光谱目录不存在: {spectra_dir}")

        all_files = os.listdir(spectra_dir)
        logging.info(f"在目录中找到 {len(all_files)} 个文件/子目录。")
        for filename in tqdm(all_files, desc="扫描光谱文件"):
            filepath = os.path.join(spectra_dir, filename)
            if os.path.isfile(filepath):
                match = spec_pattern.match(filename)
                if match:
                    try:
                        lmjd = int(match.group(1))
                        planid = match.group(2).strip()
                        spid = int(match.group(3))
                        fiberid = int(match.group(4))
                        available_spectra.append({
                            'lmjd': lmjd,
                            'planid': planid,
                            'spid': spid,
                            'fiberid': fiberid,
                            'filepath': filepath,
                            'is_compressed': filename.endswith('.gz')
                        })
                    except (ValueError, TypeError) as e:
                        logging.warning(f"解析文件名时出错: {filename}. Error: {e}")
                        continue
    except FileNotFoundError as e:
        logging.error(e)
        return None
    except Exception as e:
        logging.error(f"扫描 LAMOST 光谱目录时出错: {e}")
        return None

    logging.info(f"扫描完成，找到 {len(available_spectra)} 个有效格式的光谱文件。")
    if not available_spectra:
        logging.warning("目录中未找到有效格式的 LAMOST 光谱文件。")
        return None
    return available_spectra

def load_lamost_spectrum(filepath, obsid_for_log="未知"):
    r"""加载单个 LAMOST 光谱文件，返回 flux, ivar, wave, mask.

    Args:
        filepath (str): 光谱文件的完整路径。
        obsid_for_log (int or str): 用于日志记录的obsid。
    """
    obsid_log_str = f"obsid={obsid_for_log}"
    try:
        # 注意: LAMOST 光谱文件可能是 gzip 压缩的, 但 fits.open 会自动处理
        with fits.open(filepath) as hdul:
            if len(hdul) < 2 or not isinstance(hdul[1], fits.BinTableHDU):
                logging.warning(f"跳过 {obsid_log_str}: 文件结构不符合预期 (没有 BinTableHDU 在索引1): {filepath}")
                return None
            data = hdul[1].data
            required_cols = ['FLUX', 'IVAR', 'WAVELENGTH', 'ANDMASK', 'ORMASK']
            if not all(col in data.columns.names for col in required_cols):
                logging.warning(f"跳过 {obsid_log_str}: 光谱缺少必需列 {required_cols}: {filepath}")
                return None

            flux = data['FLUX'][0].astype(np.float64)
            ivar = data['IVAR'][0].astype(np.float64)
            wave = data['WAVELENGTH'][0].astype(np.float64)
            andmask_raw = data['ANDMASK'][0]
            ormask_raw = data['ORMASK'][0]

            try:
                andmask = andmask_raw.astype(np.uint32)
                ormask = ormask_raw.astype(np.uint32)
                mask = andmask | ormask
            except (TypeError, ValueError) as cast_err:
                logging.error(f"跳过 {obsid_log_str}: 无法将 ANDMASK 或 ORMASK 转换为整数进行位运算: {filepath}. Error: {cast_err}")
                return None

            if not (len(flux) == len(ivar) == len(wave) == len(mask)) or len(flux) == 0:
                logging.warning(f"跳过 {obsid_log_str}: 光谱数据长度不一致或为空: {filepath}")
                return None

            return {
                'flux': flux,
                'ivar': ivar,
                'wave': wave,
                'mask': mask,
                'filepath': filepath
            }

    except FileNotFoundError:
        logging.warning(f"跳过 {obsid_log_str}: 尝试加载但找不到文件 (可能是竞态条件): {filepath}")
        return None
    except Exception as e:
        logging.error(f"加载 LAMOST 光谱时出错 ({obsid_log_str}, file={filepath}): {e}", exc_info=False)
        return None

# --- PHOENIX 数据加载 --- 

def parse_phoenix_filename(filename):
    r"""解析 PHOENIX 文件名以提取参数 Teff, log g, [Fe/H]."""
    match = re.match(r'lte(?P<teff>\d{5})-(?P<logg>\d\.\d{2})-(?P<feh>[-+]?\d\.\d)', filename)
    if match:
        teff = int(match.group('teff'))
        logg = float(match.group('logg'))
        feh = float(match.group('feh'))
        return teff, logg, feh
    else:
        logging.debug(f"无法解析 PHOENIX 文件名: {filename}")
        return None

def build_phoenix_grid(phoenix_dir):
    r"""扫描 PHOENIX 目录, 解析文件名, 构建参数网格."""
    phoenix_grid = []
    param_set = set()
    logging.info(f"开始扫描 PHOENIX 目录: {phoenix_dir}")
    try:
        if not os.path.isdir(phoenix_dir):
            raise FileNotFoundError(f"PHOENIX 目录不存在: {phoenix_dir}")
        for filename in os.listdir(phoenix_dir):
            if filename.endswith('.fits') and filename.startswith('lte'):
                filepath = os.path.join(phoenix_dir, filename)
                params = parse_phoenix_filename(filename)
                if params:
                    teff, logg, feh = params
                    param_key = (teff, logg, feh)
                    if param_key not in param_set:
                        phoenix_grid.append({'teff': teff, 'logg': logg, 'feh': feh, 'filepath': filepath})
                        param_set.add(param_key)
        if not phoenix_grid:
            logging.warning(f"在目录 {phoenix_dir} 中未找到有效的 PHOENIX 光谱文件。")
            return None
        logging.info(f"成功构建 PHOENIX 参数网格，共 {len(phoenix_grid)} 个独立参数点。")
        phoenix_grid.sort(key=lambda x: (x['teff'], x['logg'], x['feh']))
        return phoenix_grid
    except FileNotFoundError as e:
        logging.error(e)
        return None
    except Exception as e:
        logging.error(f"扫描 PHOENIX 目录时出错: {e}")
        return None

def load_phoenix_wavelength(wave_path):
    r"""加载 PHOENIX 波长文件."""
    logging.info(f"尝试加载 PHOENIX 波长文件: {wave_path}")
    try:
        with fits.open(wave_path) as hdul:
            if len(hdul) > 0 and hdul[0].data is not None:
                wave_data = hdul[0].data.astype(np.float64)
                logging.info(f"成功加载 PHOENIX 波长，共 {len(wave_data)} 个点。单位假设为 Angstrom.")
                if not np.all(np.diff(wave_data) > 0):
                    logging.warning("PHOENIX 波长数组非单调递增，可能导致插值问题！")
                return wave_data
            else:
                logging.error(f"错误: 在 {wave_path} 中未找到有效的波长数据HDU。")
                return None
    except FileNotFoundError:
        logging.error(f"错误: PHOENIX 波长文件未找到: {wave_path}")
        return None
    except Exception as e:
        logging.error(f"加载 PHOENIX 波长时出错: {e}")
        return None

def load_phoenix_spectrum(filepath):
    r"""加载单个 PHOENIX 光谱文件的流量数据."""
    try:
        with fits.open(filepath) as hdul:
            if len(hdul) > 0 and hdul[0].data is not None:
                flux_data = hdul[0].data.astype(np.float64)
                return flux_data
            else:
                logging.warning(f"跳过: 在 {filepath} 中未找到有效的流量数据HDU。")
                return None
    except FileNotFoundError:
        logging.error(f"错误: 尝试加载 PHOENIX 光谱但文件未找到: {filepath}")
        return None
    except Exception as e:
        logging.error(f"加载 PHOENIX 光谱流量时出错 (文件: {filepath}): {e}")
        return None 