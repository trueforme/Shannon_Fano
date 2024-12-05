from code_table import CodeTable
import logging
from util_classes import FileInfo
from util_classes import EncodedBytesData

byte_length = 8


class Encoder:
    @staticmethod
    def build_code_table(data: bytes) -> CodeTable:
        """
        Строит кодовую таблицу для данных.
        """
        code_table = CodeTable()
        code_table.build(data)
        return code_table

    @staticmethod
    def encode_data(data: bytes, code_table: CodeTable) -> EncodedBytesData:
        """
        Кодирует данные с использованием кодовой таблицы.
        """
        encoded_bits = ''.join(code_table.codes[byte] for byte in data)
        extra_bits = (byte_length - len(
            encoded_bits) % byte_length) % byte_length
        encoded_bits += '0' * extra_bits

        encoded_bytes = bytearray()
        for i in range(0, len(encoded_bits), byte_length):
            byte = encoded_bits[i:i + byte_length]
            encoded_bytes.append(int(byte, 2))

        return EncodedBytesData(bytes(encoded_bytes), extra_bits)

    @staticmethod
    def encode_files_data(file_info_list: list[FileInfo],
                          code_table: CodeTable) -> None:
        """
        Кодирует данные каждого файла в списке `file_info_list`.
        """
        for file_info in file_info_list:
            if not file_info.is_dir:
                result = Encoder.encode_data(file_info.data, code_table)
                file_info.encoded_data = result.encoded_bytes
                file_info.extra_bits = result.extra_bits_count
                file_info.data = b''
                file_info.compressed_size = len(result.encoded_bytes)
                logging.debug(
                    f"Файл '{file_info.relative_path}' закодирован с {result.extra_bits_count} дополнительными битами.")
