import logging
from pathlib import Path

from encoder import Encoder
from decoder import Decoder
from file_handler import FileHandler
from code_table import CodeTable
from path_handler import PathHandler
from util_classes import FileInfo
from metadata_handler import MetadataHandler, Metadata
from encrypter import (
    get_files_encrypt_info,
    read_and_decrypt_metadata_with_password,
    read_and_decrypt_file_data,
)


class Archiver:
    def __init__(self):
        """
        Инициализирует объект архива.
        """
        self._archive_file_path: Path | None = None
        self._base_directory: Path | None = None
        self._pathHandler: PathHandler | None = None
        self._encoder = Encoder()
        self._decoder = Decoder()
        self._salt_size = 16
        self._nonce_size = 12

    def add_paths(self, paths: list[Path]) -> None:
        """
        Добавляет файлы или каталоги для архивации.
        """
        existing_paths = []
        for path in paths:
            resolved_path = path.resolve()
            if resolved_path.exists():
                existing_paths.append(resolved_path)
            else:
                logging.error(
                    f"Путь '{resolved_path}' не существует и будет пропущен.")

        if not existing_paths:
            logging.error(
                "Нет существующих файлов или каталогов для архивации.")
            return

        self._pathHandler = PathHandler(existing_paths)
        self._base_directory = self._pathHandler.get_base_directory()
        self._pathHandler.collect_file_info()

    def archive(self, archive_file_path: Path,
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

        self._archive_file_path = archive_file_path.resolve()
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

    def extract(
            self,
            archive_file_path: Path,
            extract_path: Path | None = None,
            password: str | None = None
    ) -> None:
        """
        Извлекает файлы и каталоги из архива.
        """
        archive_path = archive_file_path.resolve()
        if not archive_path.exists():
            logging.error(f"Архив '{archive_path}' не найден.")
            return

        extract_path = extract_path.resolve() if extract_path else Path.cwd()
        logging.debug(f"Извлечение архива '{archive_path}' в '{extract_path}'")

        try:
            with archive_path.open('rb') as archive_file:
                result: tuple[
                            Metadata, bytes | None] | None = read_and_decrypt_metadata_with_password(
                    archive_file, password)
                if result is None:
                    logging.error(
                        "Не удалось прочитать или дешифровать метаданные.")
                    return
                metadata, key = result

                code_table = metadata.code_table
                file_info_list = metadata.file_info_list

                self._extract_files_and_directories(
                    archive_file,
                    extract_path,
                    file_info_list,
                    code_table,
                    key,
                    metadata.code_table is not None
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
            file_info_list: list[FileInfo],
            code_table: CodeTable,
            key: bytes | None,
            has_password: bool
    ) -> None:
        """
        Извлекает файлы и каталоги из архива.
        """
        for file_info in file_info_list:
            relative_path = Path(file_info.relative_path)
            full_path = extract_path / relative_path
            if file_info.is_dir:
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
                    logging.error(
                        f"Не удалось дешифровать данные для '{full_path}'.")
                    return

                decoded_data = self._decoder.decode_data(
                    encoded_data,
                    file_info.extra_bits,
                    code_table
                )
                full_path.parent.mkdir(parents=True, exist_ok=True)
                FileHandler.write_file(full_path, decoded_data)

    @staticmethod
    def _log_compression_info(file_info_list: list[FileInfo]) -> None:
        """
        Записывает информацию о сжатии каждого файла в лог.
        """
        for file_info in file_info_list:
            if not file_info.is_dir:
                relative_path = file_info.relative_path
                original_size = file_info.original_size
                compressed_size = file_info.compressed_size

                if original_size != 0:
                    compression_ratio = (
                                                1 - compressed_size / original_size) * 100
                else:
                    compression_ratio = 0

                logging.info(f"Файл: {relative_path}")
                logging.info(f"Исходный размер: {original_size} байт")
                logging.info(f"Размер в архиве: {compressed_size} байт")
                logging.info(f"Степень сжатия: {compression_ratio:.2f}%")
