from fileHandler import *
from codeTable import *

class Encoder:
    def __init__(self, file_path: str):
        self.file_handler = FileHandler(file_path)

    def encode(self) -> None:
        if not self.file_handler.file_exists():
            logging.error(f"Файл '{self.file_handler.file_path}' не найден.")
            return

        data = self.file_handler.read_file()
        if data is None:
            return

        if not data:
            self._handle_empty_file()
            return

        code_table = CodeTable()
        code_table.build(data)

        encoded_bytes, extra_bits = self._encode_data(data, code_table)
        codes_serialized = code_table.serialize()

        encoded_file_path = self.file_handler.get_encoded_filename()
        self.file_handler.write_encoded_file(encoded_file_path, codes_serialized, extra_bits, self.file_handler.extension, encoded_bytes)

    @staticmethod
    def _encode_data(data: bytes, code_table: CodeTable) -> Tuple[bytes, int]:
        """
        Кодирует данные с использованием кодовой таблицы.

        :param data: исходные данные в виде байтовой строки
        :param code_table: экземпляр CodeTable с построенной кодовой таблицей
        :return: кортеж из закодированных байтов и количества дополнительных битов
        """
        encoded_bits = ''.join(code_table.codes[byte] for byte in data)
        extra_bits = (8 - len(encoded_bits) % 8) % 8
        encoded_bits += '0' * extra_bits

        encoded_bytes = bytearray()
        for i in range(0, len(encoded_bits), 8):
            byte = encoded_bits[i:i + 8]
            encoded_bytes.append(int(byte, 2))

        return bytes(encoded_bytes), extra_bits

    def _handle_empty_file(self) -> None:
        """
        Обрабатывает случай пустого входного файла при кодировании.
        """
        codes_size = 0
        extra_bits = 0
        extension_bytes = self.file_handler.extension.encode('utf-8')
        extension_length = len(extension_bytes)

        try:
            with open(self.file_handler.get_encoded_filename(), 'wb') as file:
                file.write(struct.pack('I', codes_size))
                file.write(bytes([extra_bits]))
                file.write(struct.pack('I', extension_length))
                file.write(extension_bytes)
        except IOError as e:
            logging.exception(f"Ошибка при записи пустого закодированного файла '{self.file_handler.get_encoded_filename()}': {e}")
