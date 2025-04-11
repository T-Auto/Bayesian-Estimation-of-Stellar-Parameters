import os
import logging
import multiprocessing
from functools import partial
import numpy as np
from astropy.table import Table
from tqdm import tqdm

# 导入配置
from config import settings

# 导入功能模块
from src.utils.logging_config import setup_logging
from src.loading.load_data import (
    load_lamost_catalog,
    build_catalog_lookup,
    scan_and_parse_lamost_spectra,
    build_phoenix_grid,
    load_phoenix_wavelength
)
from src.tasks.worker import process_spectrum_task

def save_results_to_fits(results, output_path, columns, formats):
    """将结果保存到 FITS 文件."""
    if not results:
        logging.info("没有生成任何结果，不创建 output.fits 文件。")
        return

    logging.info("开始保存结果到 FITS 文件...")
    try:
        # 直接从结果字典列表创建Table
        result_table = Table(rows=results, names=columns, masked=True)

        # 设置列格式
        for col, fmt in formats.items():
            if col in result_table.colnames:
                result_table[col].format = fmt
            else:
                logging.warning(f"尝试设置格式的列 '{col}' 不在结果表中。")

        result_table.write(output_path, format='fits', overwrite=True)
        logging.info(f"结果已成功保存到 {output_path}")
    except Exception as e:
        logging.error(f"保存结果到 FITS 文件时出错: {e}")

def main():
    """主程序入口."""
    setup_logging()
    logging.info("开始执行恒星参数估计流程...")
    logging.info(f"将使用 {settings.NUM_PROCESSES} 个工作进程。")
    if settings.MAX_SPECTRA_TO_PROCESS is not None:
        logging.warning(f"注意: 配置了处理数量上限 MAX_SPECTRA_TO_PROCESS = {settings.MAX_SPECTRA_TO_PROCESS}")

    # --- 数据加载和预准备 --- 
    logging.info("步骤 1/6: 扫描可用的 LAMOST 光谱文件...")
    available_spectra_info = scan_and_parse_lamost_spectra(settings.LAMOST_SPECTRA_DIR)
    if not available_spectra_info:
        logging.error("未能找到任何可用的 LAMOST 光谱文件，程序退出。")
        return # 使用 return 替代 exit()

    logging.info("步骤 2/6: 加载 LAMOST 星表...")
    lamost_catalog = load_lamost_catalog(settings.LAMOST_CATALOG_PATH)
    if lamost_catalog is None:
        logging.error("加载 LAMOST 星表失败，程序退出。")
        return

    logging.info("步骤 3/6: 构建星表查找字典...")
    catalog_lookup = build_catalog_lookup(lamost_catalog)
    if catalog_lookup is None:
        logging.error("构建星表查找字典失败，程序退出。")
        return

    logging.info("步骤 4/6: 构建 PHOENIX 模型网格...")
    phoenix_grid = build_phoenix_grid(settings.PHOENIX_SPECTRA_DIR)
    if phoenix_grid is None:
        logging.error("构建 PHOENIX 模型网格失败，程序退出。")
        return

    logging.info("步骤 5/6: 加载 PHOENIX 波长...")
    phoenix_wave = load_phoenix_wavelength(settings.PHOENIX_WAVE_PATH)
    if phoenix_wave is None:
        logging.error("无法加载 PHOENIX 波长，程序退出。")
        return

    # --- 预筛选任务 --- 
    logging.info("步骤 6/6: 预筛选光谱任务...")
    tasks_to_process = []
    skipped_match_fail = 0
    skipped_filter_fail = 0

    # 如果 build_catalog_lookup 返回了 planid_clean，现在它不存在于原始 catalog 中
    # 我们在查找时需要自己处理 planid 的 strip
    planid_col_exists = 'planid' in lamost_catalog.colnames

    for spec_info in tqdm(available_spectra_info, desc="预筛选任务"):
        # 直接在循环内处理 planid strip
        try:
            lookup_key = (
                spec_info['lmjd'],
                spec_info['planid'].strip(), # 在这里 strip
                spec_info['spid'],
                spec_info['fiberid']
            )
        except Exception as e:
            logging.warning(f"为光谱 {spec_info.get('filepath', '未知路径')} 构建查找键时出错: {e}")
            skipped_match_fail += 1
            continue

        target_row_index = catalog_lookup.get(lookup_key)

        if target_row_index is None:
            # logging.debug(f"光谱文件 {spec_info['filepath']} 无匹配星表条目 (key={lookup_key})。")
            skipped_match_fail += 1
            continue
            
        try:
            target_row = lamost_catalog[target_row_index]
            obsid = target_row.get('obsid', '未知')

            # 检查筛选条件
            target_class_val = str(target_row['class']).strip()
            target_snrg_val = float(target_row['snrg'])

            if not (
                target_class_val == settings.TARGET_CLASS and 
                target_snrg_val > settings.MIN_SNRG and 
                np.isfinite(target_snrg_val)
            ):
                # logging.debug(f"光谱文件 {spec_info['filepath']} (obsid={obsid}) 未通过筛选 (class='{target_class_val}', snrg={target_snrg_val:.2f})。")
                skipped_filter_fail += 1
                continue
            
            # 创建子进程所需的信息字典
            target_info = {
                'obsid': obsid,
                'ra': target_row.get('ra', np.nan),
                'dec': target_row.get('dec', np.nan)
            }
            
            tasks_to_process.append({'spec_info': spec_info, 'target_info': target_info})

            # 检查是否达到处理上限
            if settings.MAX_SPECTRA_TO_PROCESS is not None and len(tasks_to_process) >= settings.MAX_SPECTRA_TO_PROCESS:
                logging.info(f"已达到处理上限 MAX_SPECTRA_TO_PROCESS = {settings.MAX_SPECTRA_TO_PROCESS}，停止筛选更多任务。")
                break

        except (KeyError, ValueError, TypeError) as filter_err:
            obsid_err = locals().get('obsid', '未知') # 获取局部变量 obsid
            logging.warning(f"光谱文件 {spec_info['filepath']} (obsid={obsid_err}) 筛选时出错: {filter_err}")
            skipped_filter_fail += 1
            continue
            
    num_tasks_final = len(tasks_to_process)
    logging.info(f"预筛选完成。共 {num_tasks_final} 个任务待处理。")
    logging.info(f"(预筛选期间: {skipped_match_fail} 个无法匹配星表, {skipped_filter_fail} 个未通过 class/snrg 筛选)")

    if not tasks_to_process:
        logging.info("没有需要处理的任务，程序结束。")
        return

    # --- 使用多进程处理任务 --- 
    results = []
    logging.info(f"开始使用 {settings.NUM_PROCESSES} 个进程并行处理 {num_tasks_final} 个光谱任务...")
    
    # 使用 partial 预先绑定不变的参数
    worker_func = partial(process_spectrum_task, phoenix_grid=phoenix_grid, phoenix_wave=phoenix_wave)

    # 推荐的 chunksize 计算方式
    chunksize = max(1, num_tasks_final // (settings.NUM_PROCESSES * 4))
    logging.info(f"多进程池 chunksize 设置为: {chunksize}")

    with multiprocessing.Pool(processes=settings.NUM_PROCESSES) as pool:
        # 使用 imap_unordered 以获得更好的内存效率和进度反馈
        # 使用 tqdm 显示进度条
        imap_results = pool.imap_unordered(worker_func, tasks_to_process, chunksize=chunksize)
        
        for result in tqdm(imap_results, total=num_tasks_final, desc="并行处理光谱"):
            if result is not None:
                results.append(result)

    logging.info(f"并行处理完成。成功获取 {len(results)} 条有效结果。")

    # --- 保存结果 --- 
    save_results_to_fits(
        results,
        settings.OUTPUT_FITS_PATH,
        settings.OUTPUT_COLUMNS,
        settings.OUTPUT_FORMATS
    )

    logging.info("恒星参数估计流程执行完毕。")

if __name__ == "__main__":
    # Windows 平台需要这个保护，防止子进程重新执行主模块代码
    multiprocessing.freeze_support()
    main() 