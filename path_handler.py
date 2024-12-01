import os
import logging
from pathlib import Path
from typing import Any

class PathHandler:
    """
    Класс для обработки путей и сбора информации о файлах и каталогах.
    """
    def __init__(self, paths: list[Path]) -> None:
        """
        Инициализирует PathHandler с путями.
        """
        self._paths = paths
        self._base_directory = self._set_base_directory()
        self._file_info_list: list[dict[str, Any]] = []

    def _set_base_directory(self) -> Path:
        """
        Устанавливает базовый каталог для архивации.
        """
        paths = self._paths
        if len(paths) == 1:
            base_directory = paths[0].parent
        else:
            base_directory = Path(os.path.commonpath([str(path) for path in paths]))
            if not all(str(path).startswith(str(base_directory)) for path in paths):
                base_directory = Path.cwd()
        logging.debug(f"Базовый каталог для архивации: {base_directory}")
        return base_directory

    def get_base_directory(self) -> Path:
        return self._base_directory

    def collect_file_info(self) -> list[dict[str, Any]]:
        """
        Собирает информацию о файлах и каталогах.
        """
        for path in self._paths:
            if path.is_file():
                self._collect_file_info(path)
            elif path.is_dir():
                self._collect_directory_info(path)
        return self._file_info_list

    def _collect_file_info(self, file_path: Path) -> None:
        """
        Собирает информацию о файле для архивации.
        """
        relative_path = file_path.relative_to(self._base_directory)
        file_info = {
            'absolute_path': file_path,
            'relative_path': relative_path.as_posix(),
            'is_dir': False,
            'data': None,
            'encoded_data': None,
            'extra_bits': 0,
            'original_size': file_path.stat().st_size,
            'compressed_size': 0,
        }
        self._file_info_list.append(file_info)

    def _collect_directory_info(self, dir_path: Path) -> None:
        """
        Собирает информацию о каталоге и его содержимом для архивации.
        """
        relative_dir_path = dir_path.relative_to(self._base_directory)
        self._file_info_list.append({
            'absolute_path': dir_path,
            'relative_path': relative_dir_path.as_posix(),
            'is_dir': True,
            'data': None,
            'encoded_data': b'',
            'extra_bits': 0,
            'original_size': 0,
            'compressed_size': 0,
        })

        for root, dirs, files in os.walk(dir_path):
            root_path = Path(root)
            for dir_name in dirs:
                dir_full_path = root_path / dir_name
                self._collect_directory_info(dir_full_path)
            for file in files:
                file_path = root_path / file
                self._collect_file_info(file_path)

    def get_file_info_list(self) -> list[dict[str, Any]]:
        return self._file_info_list
