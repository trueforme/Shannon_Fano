import logging
from pathlib import Path
import struct
from typing import Any

from encrypter import EncryptedData


class FileHandler:
    size_bytes_count = 4
    """
    Размер каждой логической части (кроме наличия пароля) в файле кодируется 4 байтами.
    """

    @staticmethod
    def read_files_data(file_info_list: list[dict[str, Any]]) -> bytearray:
        """
        Читает данные файлов для архивации и собирает их в один байтовый массив.
        """
        all_data = bytearray()
        for file_info in file_info_list:
            if not file_info['is_dir']:
                data = FileHandler.read_file_static(
                    str(file_info['absolute_path']))
                if data is None:
                    logging.error(
                        f"Ошибка при чтении файла '{file_info['absolute_path']}'.")
                    return bytearray()
                file_info['data'] = data
                all_data.extend(data)
        return all_data

    @staticmethod
    def read_file_static(file_path: str) -> bytes | None:
        """
        Читает данные из файла по заданному пути.
        """
        try:
            path = Path(file_path).resolve()
            logging.debug(f"Попытка открытия файла: {path}")
            return path.read_bytes()
        except IOError as e:
            logging.exception(f"Ошибка при чтении файла '{file_path}': {e}")
            return None

    @staticmethod
    def read_bytes_with_size(file, description: str) -> bytes:
        """
        Читает из файла данные с предварительно записанным размером.
        """
        size_data = file.read(FileHandler.size_bytes_count)
        if len(size_data) < FileHandler.size_bytes_count:
            logging.error(
                f"Архив поврежден или имеет неверный формат (недостаточно данных для размера {description})."
            )
            raise ValueError("Неверный формат архива")
        size = struct.unpack('I', size_data)[0]
        data = file.read(size)
        if len(data) < size:
            logging.error(
                f"Архив поврежден или имеет неверный формат (недостаточно данных для {description})."
            )
            raise ValueError("Неверный формат архива")
        return data

    @staticmethod
    def write_bytes_with_size(file, data: bytes) -> None:
        """
        Записывает данные в файл с предварительной записью их размера.
        """
        size = len(data)
        file.write(struct.pack('I', size))
        if size > 0:
            file.write(data)

    @staticmethod
    def write_file(file_path: str, data: bytes) -> None:
        """
        Записывает данные в файл по заданному пути.
        """
        try:
            path = Path(file_path).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        except IOError as e:
            logging.exception(f"Ошибка при записи файла '{file_path}': {e}")

    @staticmethod
    def validate_files_for_archiving(
            file_info_list: list[dict[str, Any]]) -> bool:
        """
        Проверяет наличие файлов или каталогов для архивации.
        """
        if not file_info_list:
            logging.error("Нет файлов или каталогов для архивации.")
            return False
        return True

    @staticmethod
    def write_archive_file(
            archive_file_path: Path,
            encrypted_metadata: bytes,
            encrypted_file_data: list[EncryptedData],
            salt: bytes,
            nonce_meta: bytes,
            password: str | None
    ) -> None:
        """
        Записывает данные в файл архива.
        """
        try:
            with open(archive_file_path, 'wb') as archive_file:

                archive_file.write(bytes(
                    [1 if password else 0]))

                FileHandler.write_bytes_with_size(archive_file, salt)

                FileHandler.write_bytes_with_size(archive_file, nonce_meta)

                FileHandler.write_bytes_with_size(archive_file,
                                                  encrypted_metadata)

                for encrypted_data in encrypted_file_data:
                    FileHandler.write_bytes_with_size(archive_file,
                                                      encrypted_data.nonce)
                    FileHandler.write_bytes_with_size(archive_file,
                                                      encrypted_data.data)
            logging.info(f"Архив '{archive_file_path}' успешно создан.")
        except IOError as e:
            logging.exception(
                f"Ошибка при записи архива '{archive_file_path}': {e}")
