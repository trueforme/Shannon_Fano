import os
import struct
from typing import *
import logging

class FileHandler:
    def __init__(self, file_path: str) -> None:
        """
        Инициализирует объект обработчика файлов с полным путём к файлу.

        :param file_path: полный путь к файлу
        """
        self.file_path: str = file_path
        self.directory: str = os.path.dirname(file_path)
        self.base_name: str = os.path.splitext(os.path.basename(file_path))[0]
        self.extension: str = os.path.splitext(os.path.basename(file_path))[1]

    def read_file(self) -> Optional[bytes]:
        """
        Читает данные из файла.

        :return: данные файла в виде байтовой строки или None в случае ошибки
        """
        try:
            with open(self.file_path, 'rb') as file:
                return file.read()
        except IOError as e:
            logging.exception(f"Ошибка при чтении файла '{self.file_path}': {e}")
            return None

    @staticmethod
    def write_file(file_path: str, data: bytes) -> None:
        """
        Записывает данные в файл.

        :param file_path: путь к файлу
        :param data: данные для записи (байтовая строка)
        """
        try:
            with open(file_path, 'wb') as file:
                file.write(data)
        except IOError as e:
            logging.exception(f"Ошибка при записи файла '{file_path}': {e}")

    def file_exists(self) -> bool:
        """
        Проверяет, существует ли файл.
        """
        return os.path.exists(self.file_path)

    def generate_unique_filename(self, base_name: str, extension: str) -> str:
        """
        Генерирует уникальное имя файла, добавляя (x) к имени файла, если файл уже существует.

        :param base_name: базовое имя файла
        :param extension: расширение файла
        :return: уникальный путь к файлу
        """
        filename = f"{base_name}{extension}"
        full_path = os.path.join(self.directory, filename)
        counter = 1
        while os.path.exists(full_path):
            filename = f"{base_name}({counter}){extension}"
            full_path = os.path.join(self.directory, filename)
            counter += 1
        return full_path

    def get_encoded_filename(self) -> str:
        """
        Возвращает путь к закодированному файлу.

        :return: путь к закодированному файлу
        """
        return os.path.join(self.directory, f"{self.base_name}_encoded.bin")

    def get_decoded_filename(self, extension: str) -> str:
        """
        Генерирует уникальное имя для декодированного файла.

        :param extension: расширение файла
        :return: уникальный путь к декодированному файлу
        """
        return self.generate_unique_filename(self.base_name + "_decoded", extension)

    @staticmethod
    def write_encoded_file(encoded_file_path: str, codes_serialized: bytes, extra_bits: int, extension: str, encoded_bytes: bytes) -> None:
        """
        Записывает закодированные данные и кодовую таблицу в файл, включая информацию об оригинальном расширении.

        :param encoded_file_path: путь к закодированному файлу
        :param codes_serialized: сериализованная кодовая таблица
        :param extra_bits: количество дополнительных битов
        :param extension: оригинальное расширение файла
        :param encoded_bytes: закодированные данные в виде байтовой строки
        """
        codes_size = len(codes_serialized)
        extension_bytes = extension.encode('utf-8')
        extension_length = len(extension_bytes)

        try:
            with open(encoded_file_path, 'wb') as file:
                # Записываем размер кодовой таблицы (4 байта, unsigned int)
                file.write(struct.pack('I', codes_size))
                # Записываем кодовую таблицу
                file.write(codes_serialized)
                # Записываем количество дополнительных битов (1 байт)
                file.write(bytes([extra_bits]))
                # Записываем длину расширения (4 байта, unsigned int)
                file.write(struct.pack('I', extension_length))
                # Записываем само расширение
                file.write(extension_bytes)
                # Записываем закодированные данные
                file.write(encoded_bytes)
        except IOError as e:
            logging.exception(f"Ошибка при записи закодированного файла '{encoded_file_path}': {e}")

    def read_encoded_file(self) -> Optional[Tuple[bytes, int, bytes, str]]:
        """
        Читает закодированный файл и извлекает кодовую таблицу, дополнительные биты, расширение и закодированные данные.

        :return: кортеж из сериализованной кодовой таблицы, количества дополнительных битов, закодированных байтов и расширения
                 или все None в случае ошибки
        """
        #сделать декомпоз
        try:
            with open(self.file_path, 'rb') as file:
                codes_size_data = file.read(4)
                if len(codes_size_data) < 4:
                    logging.error("Файл поврежден или имеет неверный формат (недостаточно данных для размера кодовой таблицы).")
                    return None
                codes_size = struct.unpack('I', codes_size_data)[0]

                if codes_size > 0:
                    codes_serialized = file.read(codes_size)
                    if len(codes_serialized) < codes_size:
                        logging.error("Файл поврежден или имеет неверный формат (недостаточно данных для кодовой таблицы).")
                        return None
                else:
                    codes_serialized = b''

                extra_bits, extension = self._read_extra_bits_and_extension(file)
                if extra_bits is None or extension is None:
                    return None

                if codes_size > 0:
                    encoded_bytes = file.read()
                    if not encoded_bytes and extra_bits != 0:
                        logging.error("Файл поврежден или имеет неверный формат (нет закодированных данных, но указано наличие дополнительных битов).")
                        return None
                else:
                    encoded_bytes = b''

                return codes_serialized, extra_bits, encoded_bytes, extension

        except IOError as e:
            logging.exception(f"Ошибка при чтении файла '{self.file_path}': {e}")
            return None

    @staticmethod
    def _read_extra_bits_and_extension(file) -> Tuple[Optional[int], Optional[str]]:
        """
        Читает количество дополнительных битов и расширение файла из закодированного файла.

        :param file: файловый объект
        :return: кортеж из количества дополнительных битов и расширения файла или (None, None) в случае ошибки
        """
        try:
            extra_bits_data = file.read(1)
            if len(extra_bits_data) < 1:
                logging.error("Файл поврежден или имеет неверный формат (недостаточно данных для количества дополнительных битов).")
                return None, None
            extra_bits = extra_bits_data[0]

            extension_length_data = file.read(4)
            if len(extension_length_data) < 4:
                logging.error("Файл поврежден или имеет неверный формат (недостаточно данных для длины расширения).")
                return None, None
            extension_length = struct.unpack('I', extension_length_data)[0]

            extension_data = file.read(extension_length)
            if len(extension_data) < extension_length:
                logging.error("Файл поврежден или имеет неверный формат (недостаточно данных для расширения).")
                return None, None
            extension = extension_data.decode('utf-8')

            return extra_bits, extension

        except Exception as e:
            logging.exception(f"Ошибка при чтении дополнительных битов и расширения: {e}")
            return None, None