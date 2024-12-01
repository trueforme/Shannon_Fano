import logging
from pathlib import Path
from typing import Any, Optional

from encoder import Encoder
from decoder import Decoder
from fileHandler import FileHandler
from codeTable import CodeTable
from pathHandler import PathHandler
from metadata_handler import MetadataHandler
from encrypter import (
    derive_key,
    get_files_encrypt_info,
    read_archive_header,
    read_and_decrypt_metadata,
    read_and_decrypt_file_data,
)


class Archiver:
    def __init__(self) -> None:
        """
        Инициализирует объект архива.
        """
        self._archive_file_path: Path = Path()
        self._base_directory: Path = Path()
        self._pathHandler: Optional[PathHandler] = None
        self._encoder = Encoder()
        self._decoder = Decoder()
        self._salt_size = 16
        self._nonce_size = 12

    def add_paths(self, paths: list[str]) -> None:
        """
        Добавляет файлы или каталоги для архивации.
        """
        absolute_paths = [Path(path).resolve() for path in paths]
        existing_paths = [path for path in absolute_paths if path.exists()]
        non_existing_paths = [path for path in absolute_paths if
                              not path.exists()]

        for path in non_existing_paths:
            logging.error(f"Путь '{path}' не существует и будет пропущен.")

        if not existing_paths:
            logging.error(
                "Нет существующих файлов или каталогов для архивации.")
            return

        self._pathHandler = PathHandler(existing_paths)
        self._base_directory = self._pathHandler.get_base_directory()
        self._pathHandler.collect_file_info()

    def archive(self, archive_file_path: str,
                password: str | None = None) -> None:
        """
        Создает архив из добавленных файлов и каталогов с опциональной парольной защитой.
        """
        if not self._pathHandler:
            logging.error("Нет файлов или каталогов для архивации.")
            return

        file_info_list = self._pathHandler.get_file_info_list()

        if not FileHandler.validate_files_for_archiving(file_info_list):
            return

        self._archive_file_path = Path(archive_file_path).resolve()
        logging.debug(f"Путь архива: {self._archive_file_path}")

        if self._archive_file_path.is_dir():
            logging.error(
                f"Путь '{self._archive_file_path}' указывает на директорию. Укажите полный путь к файлу архива.")
            return

        all_data = FileHandler.read_files_data(file_info_list)
        if not all_data:
            logging.error("Нет данных для кодирования.")
            return

        code_table = self._encoder.build_code_table(bytes(all_data))
        logging.debug(f"Кодовая таблица построена: {code_table.codes}")

        self._encoder.encode_files_data(file_info_list, code_table)
        metadata_serialized = MetadataHandler.serialize_metadata(
            file_info_list, code_table)

        encrypted_info = get_files_encrypt_info(
            salt_size=self._salt_size,
            file_info_list=file_info_list,
            metadata_serialized=metadata_serialized,
            password=password
        )

        FileHandler.write_archive_file(
            self._archive_file_path,
            encrypted_info.encrypted_metadata,
            encrypted_info.encrypted_file_data,
            encrypted_info.salt,
            encrypted_info.nonce_meta,
            password
        )

        self._log_compression_info(file_info_list)

    def extract(self, archive_file_path: str, extract_path: str | None = None,
                password: str | None = None) -> None:
        """
        Извлекает файлы и каталоги из архива.
        """
        archive_path = Path(archive_file_path).resolve()
        if not archive_path.exists():
            logging.error(f"Архив '{archive_path}' не найден.")
            return

        extract_path = Path(
            extract_path).resolve() if extract_path else Path.cwd()
        logging.debug(f"Извлечение архива '{archive_path}' в '{extract_path}'")

        try:
            with open(archive_path, 'rb') as archive_file:
                has_password, salt, nonce_meta = read_archive_header(
                    archive_file)

                if has_password:
                    if not password:
                        print("Этот архив защищён паролем.")
                        password = input(
                            "Введите пароль для извлечения: ").strip()
                    key = derive_key(password, salt)
                else:
                    key = None

                metadata = read_and_decrypt_metadata(archive_file, key,
                                                     nonce_meta, has_password)
                if metadata is None:
                    return

                code_table = CodeTable.deserialize(metadata['code_table'])
                file_info_list = metadata['file_info_list']

                self._extract_files_and_directories(
                    archive_file,
                    extract_path,
                    file_info_list,
                    code_table,
                    key,
                    has_password
                )

                logging.info(
                    f"Архив '{archive_path}' успешно извлечён в '{extract_path}'.")

        except IOError as e:
            logging.exception(
                f"Ошибка при чтении архива '{archive_path}': {e}")
        except Exception as e:
            logging.exception(
                f"Ошибка при извлечении архива '{archive_path}': {e}")

    def _extract_files_and_directories(
            self,
            archive_file,
            extract_path: Path,
            file_info_list: list[dict[str, Any]],
            code_table: CodeTable,
            key: bytes | None,
            has_password: bool
    ) -> None:
        """
        Извлекает файлы и каталоги из архива.
        """
        for file_info in file_info_list:
            relative_path = Path(file_info['relative_path'])
            full_path = extract_path / relative_path
            if file_info['is_dir']:
                full_path.mkdir(parents=True, exist_ok=True)
            else:
                description = f"файла '{full_path}'"
                encoded_data = read_and_decrypt_file_data(
                    archive_file,
                    key,
                    has_password,
                    description
                )
                if encoded_data is None:
                    return

                decoded_data = self._decoder.decode_data(encoded_data,
                                                         file_info[
                                                             'extra_bits'],
                                                         code_table)
                full_path.parent.mkdir(parents=True, exist_ok=True)
                FileHandler.write_file(str(full_path), decoded_data)

    @staticmethod
    def _log_compression_info(file_info_list: list[dict[str, Any]]) -> None:
        """
        Записывает информацию о сжатии каждого файла в лог.
        """
        for file_info in file_info_list:
            if not file_info['is_dir']:
                relative_path = file_info['relative_path']
                original_size = file_info['original_size']
                compressed_size = file_info['compressed_size']
                compression_ratio = (
                                            1 - compressed_size / original_size) * 100 \
                    if original_size != 0 else 0
                logging.info(f"Файл: {relative_path}")
                logging.info(f"Исходный размер: {original_size} байт")
                logging.info(f"Размер в архиве: {compressed_size} байт")
                logging.info(f"Степень сжатия: {compression_ratio:.2f}%")
