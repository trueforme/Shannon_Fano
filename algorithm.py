import os
from collections import Counter
import pickle
import struct

class CodeTable:
    def __init__(self):
        self.codes = {}

    def build(self, data):
        freq_counter = Counter(data)
        symbols = sorted(freq_counter.items(), key=lambda item: item[1], reverse=True)
        self.shannon_fano_encode(symbols, self.codes)

    def shannon_fano_encode(self, symbols, codes, prefix=''):
        if len(symbols) == 1:
            symbol = symbols[0][0]
            codes[symbol] = prefix or '0'
            return
        total = sum(freq for symbol, freq in symbols)
        acc = 0
        split_index = 0
        for i, (symbol, freq) in enumerate(symbols):
            acc += freq
            if acc >= total / 2:
                split_index = i + 1
                break
        self.shannon_fano_encode(symbols[:split_index], codes, prefix + '0')
        self.shannon_fano_encode(symbols[split_index:], codes, prefix + '1')

    def serialize(self):
        return pickle.dumps(self.codes)

    @staticmethod
    def deserialize(serialized_data):
        codes = pickle.loads(serialized_data)
        code_table = CodeTable()
        code_table.codes = codes
        return code_table

class ShannonFanoCodec:
    AVAILABLE_EXTENSIONS = ['.txt']
    def __init__(self, base_name):
        self.base_name = base_name
        self.input_txt = f"{self.base_name}.txt"
        self.encoded_file = f"{self.base_name}_encoded.bin"
        self.decoded_file = f"{self.base_name}_decoded.txt"

    def encode(self):
        if not os.path.exists(self.input_txt):
            print(f"Файл '{self.input_txt}' не найден.")
            return
        with open(self.input_txt, 'rb') as file:
            data = file.read()

        if not data:
            codes_size = 0
            with open(self.encoded_file, 'wb') as file:
                file.write(struct.pack('I', codes_size))
                file.write(bytes([0]))
            print(f"Исходный файл '{self.input_txt}' пуст.")
            return

        code_table = CodeTable()
        code_table.build(data)

        encoded_bits = ''.join(code_table.codes[byte] for byte in data)

        extra_bits = (8 - len(encoded_bits) % 8) % 8
        encoded_bits += '0' * extra_bits

        encoded_bytes = bytearray()
        for i in range(0, len(encoded_bits), 8):
            byte = encoded_bits[i:i+8]
            encoded_bytes.append(int(byte, 2))

        codes_serialized = code_table.serialize()
        codes_size = len(codes_serialized)

        with open(self.encoded_file, 'wb') as file:
            # размер кодовой таблицы (4 байта, unsigned int)
            file.write(struct.pack('I', codes_size))
            # Записываем кодовую таблицу
            file.write(codes_serialized)
            # Записываем количество дополнительных битов (1 байт)
            file.write(bytes([extra_bits]))
            # Записываем закодированные данные
            file.write(encoded_bytes)

        print(f"Файл '{self.input_txt}' закодирован в '{self.encoded_file}'.")

    def decode(self):
        if not os.path.exists(self.encoded_file):
            print(f"Файл '{self.encoded_file}' не найден.")
            return

        with open(self.encoded_file, 'rb') as file:
            # Читаем размер кодовой таблицы (4 байта)
            codes_size_data = file.read(4)
            # if len(codes_size_data) < 4:
            #     print("Ошибка: Файл поврежден или имеет неверный формат (недостаточно данных для размера кодовой таблицы).")
            #     return
            codes_size = struct.unpack('I', codes_size_data)[0]

            if codes_size == 0:
                with open(self.decoded_file, 'wb') as out_file:
                    pass
                print(f"Закодированный файл '{self.encoded_file}' указывает на пустой исходный файл. Создан пустой декодированный файл '{self.decoded_file}'.")
                return

            codes_serialized = file.read(codes_size)
            if len(codes_serialized) < codes_size:
                print("Ошибка: Файл поврежден или имеет неверный формат (недостаточно данных для кодовой таблицы).")
                return

            try:
                code_table = CodeTable.deserialize(codes_serialized)
            except (pickle.UnpicklingError, EOFError) as e:
                print("Ошибка: Не удалось десериализовать кодовую таблицу.")
                return

            reverse_codes = {code: byte for byte, code in code_table.codes.items()}

            extra_bits_data = file.read(1)
            extra_bits = extra_bits_data[0]

            encoded_bytes = file.read()
            if not encoded_bytes and extra_bits != 0:
                print("Ошибка: Файл поврежден или имеет неверный формат (нет закодированных данных, но указано наличие дополнительных битов).")
                return

        encoded_bits = ''.join(f'{byte:08b}' for byte in encoded_bytes)

        if extra_bits:
            encoded_bits = encoded_bits[:-extra_bits]

        # Декодирование данных
        decoded_bytes = bytearray()
        buffer = ''
        for bit in encoded_bits:
            buffer += bit
            if buffer in reverse_codes:
                decoded_bytes.append(reverse_codes[buffer])
                buffer = ''

        with open(self.decoded_file, 'wb') as file:
            file.write(decoded_bytes)

        print(f"Файл '{self.encoded_file}' успешно декодирован в '{self.decoded_file}'.")

    def verify_integrity(self):
        if not os.path.exists(self.input_txt) or not os.path.exists(self.decoded_file):
            print("Ошибка: Один из файлов не существует для проверки целостности.")
            return

        original_size = os.path.getsize(self.input_txt)
        decoded_size = os.path.getsize(self.decoded_file)

        if original_size != decoded_size:
            print("Ошибка: Размеры исходного и декодированного файлов не совпадают.")
            return

        if original_size == 0:
            print("Исходный файл пуст. Пустой декодированный файл создан успешно.")
            return

        with open(self.input_txt, 'rb') as f1, open(self.decoded_file, 'rb') as f2:
            original = f1.read()
            decoded = f2.read()
            if original == decoded:
                print("Успешное декодирование: декодированный файл совпадает с исходным.")
            else:
                print("Ошибка: декодированный файл отличается от исходного.")


