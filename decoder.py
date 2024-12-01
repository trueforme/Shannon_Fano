from fileHandler import *
from codeTable import CodeTable


class Decoder:
    def __init__(self, encoded_file_path: str):
        self.file_handler = FileHandler(encoded_file_path)
        self.decoded_file_name: str = ''

    def decode(self) -> None:
        if not self.file_handler.file_exists():
            # logging.error(f"Файл '{self.file_handler.file_path}' не найден.")
            return

        read_result = self.file_handler.read_encoded_file()
        if read_result is None:
            return

        codes_serialized, extra_bits, encoded_bytes, extension = read_result

        encoded_file_name = os.path.basename(self.file_handler.file_path)

        if encoded_file_name.endswith('_encoded.bin'):
            base_name = encoded_file_name[:-len('_encoded.bin')]
        else:
            base_name = os.path.splitext(encoded_file_name)[0]

        self.decoded_file_name = self.file_handler.generate_unique_filename(
            base_name, extension)

        if not codes_serialized:
            self._handle_empty_decoded_file()
            return

        code_table = CodeTable.deserialize(codes_serialized)
        decoded_data = self._decode_data(encoded_bytes, extra_bits, code_table)

        self.file_handler.write_file(self.decoded_file_name, decoded_data)

    @staticmethod
    def _decode_data(encoded_bytes: bytes, extra_bits_count: int,
                     code_table: CodeTable) -> bytes:
        """
        Декодирует данные с использованием кодовой таблицы.

        :param encoded_bytes: закодированные данные в виде байтовой строки
        :param extra_bits_count: количество дополнительных битов
        :param code_table: экземпляр CodeTable с восстановленной кодовой таблицей
        :return: декодированные данные в виде байтовой строки
        """
        reverse_codes = {code: byte for byte, code in code_table.codes.items()}

        encoded_bits = ''.join(f'{byte:08b}' for byte in encoded_bytes)
        if extra_bits_count:
            encoded_bits = encoded_bits[:-extra_bits_count]

        decoded_bytes = bytearray()
        buffer = ''
        for bit in encoded_bits:
            buffer += bit
            if buffer in reverse_codes:
                decoded_bytes.append(reverse_codes[buffer])
                buffer = ''

        return bytes(decoded_bytes)

    def _handle_empty_decoded_file(self) -> None:
        """
        Обрабатывает случай пустого закодированного файла при декодировании.
        """
        with open(self.decoded_file_name, 'wb'):
            pass
