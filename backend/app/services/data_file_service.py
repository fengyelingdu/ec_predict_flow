import pandas as pd
import os
import shutil
from datetime import datetime
from typing import List, Optional
from app.core.config import settings


class DataFileService:
    """数据文件管理服务"""

    @staticmethod
    def list_data_files(directory: str = None) -> List[dict]:
        """列出指定目录下的所有pkl文件"""
        if directory is None:
            directory = settings.RAW_DATA_DIR

        files = []
        if not os.path.exists(directory):
            return files

        for filename in os.listdir(directory):
            if filename.endswith('.pkl'):
                filepath = os.path.join(directory, filename)
                stat = os.stat(filepath)

                files.append({
                    'filename': filename,
                    'filepath': filepath,
                    'size': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created_time': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'modified_time': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })

        # 按修改时间降序排列
        files.sort(key=lambda x: x['modified_time'], reverse=True)
        return files

    @staticmethod
    def delete_data_file(filename: str, directory: str = None) -> bool:
        """删除指定的数据文件"""
        if directory is None:
            directory = settings.RAW_DATA_DIR

        filepath = os.path.join(directory, filename)

        # 安全检查
        if not os.path.exists(filepath):
            return False

        if not filepath.endswith('.pkl'):
            return False

        if not filepath.startswith(directory):
            return False

        try:
            os.remove(filepath)
            return True
        except Exception as e:
            print(f"Delete file error: {e}")
            return False

    @staticmethod
    def preview_data_file(filename: str, directory: str = None, rows: int = 10) -> dict:
        """预览数据文件的前几行"""
        if directory is None:
            directory = settings.RAW_DATA_DIR

        filepath = os.path.join(directory, filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filename}")

        try:
            df_raw = pd.read_pickle(filepath)
            df=df_raw.copy().dropna()

            preview_data = {
                'filename': filename,
                'total_rows': len(df),
                'columns': list(df.columns),
                'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'preview': df.head(rows).to_dict('records'),
                'stats': {
                    'start_time': str(df['datetime'].min()) if 'datetime' in df.columns else None,
                    'end_time': str(df['datetime'].max()) if 'datetime' in df.columns else None
                }
            }

            return preview_data
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")

    @staticmethod
    def delete_directory(dirname: str, parent_directory: str) -> bool:
        """删除指定的目录及其所有内容"""
        dirpath = os.path.join(parent_directory, dirname)

        # 安全检查
        if not os.path.exists(dirpath):
            return False

        if not os.path.isdir(dirpath):
            return False

        if not dirpath.startswith(parent_directory):
            return False

        try:
            shutil.rmtree(dirpath)
            return True
        except Exception as e:
            print(f"Delete directory error: {e}")
            return False
