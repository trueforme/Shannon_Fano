from collections import Counter
import pickle
from typing import List, Tuple, Dict


class CodeTable:
    def __init__(self):
        self.codes: Dict[int, str] = {}

    def build(self, data: bytes) -> None:
        """
        Строит кодовую таблицу Шеннона-Фано на основе входных данных.

        :param data: байтовые данные, для которых необходимо построить кодовую таблицу
        """
        freq_counter = Counter(data)
        symbols: List[Tuple[int, int]] = list(freq_counter.items())
        self.encode_symbols(symbols, self.codes)

    def encode_symbols(
            self,
            symbols: List[Tuple[int, int]],
            codes: Dict[int, str],
            prefix: str = ''
    ) -> None:
        """
        Кодирует байты из файла рекурсивным вызовом с помощью алгоритма Shannon-Fano.

        :param symbols: список кортежей (байт, частота)
        :param codes: словарь для хранения кодов
        :param prefix: текущий префикс для кодов
        """
        if len(symbols) == 1:
            symbol = symbols[0][0]
            codes[symbol] = prefix or '0'
            return
        total = sum(freq for _, freq in symbols)
        acc = 0
        split_index = 0
        for i, (_, freq) in enumerate(symbols):
            acc += freq
            if acc >= total / 2:
                split_index = i + 1
                break
        self.encode_symbols(symbols[:split_index], codes, prefix + '0')
        self.encode_symbols(symbols[split_index:], codes, prefix + '1')

    def serialize(self) -> bytes:
        """
        Сериализует кодовую таблицу для сохранения в файл.

        :return: байтовая строка сериализованной кодовой таблицы
        """
        return pickle.dumps(self.codes)

    @staticmethod
    def deserialize(serialized_data: bytes) -> 'CodeTable':
        """
        Десериализует кодовую таблицу из байтовой строки.

        :param serialized_data: байтовая строка сериализованной кодовой таблицы
        :return: экземпляр класса CodeTable с восстановленной кодовой таблицей
        """
        codes = pickle.loads(serialized_data)
        code_table = CodeTable()
        code_table.codes = codes
        return code_table
