from codeTable import CodeTable
from typing import Any
import logging

class Decoder:
    @staticmethod
    def decode_data(encoded_bytes: bytes, extra_bits: int, code_table: CodeTable) -> bytes:
        """
        Декодирует данные с использованием кодовой таблицы.
        """
        reverse_codes = {code: byte for byte, code in code_table.codes.items()}

        encoded_bits = ''.join(f'{byte:08b}' for byte in encoded_bytes)
        if extra_bits:
            encoded_bits = encoded_bits[:-extra_bits]

        decoded_bytes = bytearray()
        buffer = ''
        for bit in encoded_bits:
            buffer += bit
            if buffer in reverse_codes:
                decoded_bytes.append(reverse_codes[buffer])
                buffer = ''
        return bytes(decoded_bytes)

    @staticmethod
    def decode_files_data(file_info_list: list[dict[str, Any]], code_table: CodeTable) -> None:
        """
        Декодирует данные каждого файла в списке `file_info_list`.
        """
        for file_info in file_info_list:
            if not file_info['is_dir']:
                decoded_data = Decoder.decode_data(
                    file_info['encoded_data'],
                    file_info['extra_bits'],
                    code_table
                )
                file_info['decoded_data'] = decoded_data
                file_info['encoded_data'] = None
                logging.debug(f"Файл '{file_info['relative_path']}' декодирован.")
