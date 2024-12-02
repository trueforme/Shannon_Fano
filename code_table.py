from collections import Counter
import pickle
from typing import Any
from util_classes import SymbolFrequency


class CodeTable:
    def __init__(self):
        self.codes: dict[int, str] = {}

    def build(self, data: bytes) -> None:
        """
        Строит кодовую таблицу Шеннона-Фано на основе входных данных.
        """
        freq_counter = Counter(data)
        symbols: list[SymbolFrequency] = sorted(
            [SymbolFrequency(symbol, freq) for symbol, freq in
             freq_counter.items()],
            key=lambda sf: sf.frequency,
            reverse=True
        )
        self.encode_symbols(symbols, prefix='')

    def encode_symbols(
            self,
            symbols: list[SymbolFrequency],
            prefix: str,
            max_depth: int = 100
    ) -> None:
        """
        Рекурсивно кодирует символы с помощью алгоритма Шеннона-Фано.
        """
        if self._is_base_case(symbols, max_depth):
            self._handle_base_case(symbols, prefix)
            return

        split_index = self._find_split_index(symbols)
        if split_index == 0 or split_index == len(symbols):
            split_index = 1 if len(symbols) > 1 else 0

        left_symbols = symbols[:split_index]
        right_symbols = symbols[split_index:]

        self.encode_symbols(left_symbols, prefix + '0', max_depth - 1)
        self.encode_symbols(right_symbols, prefix + '1', max_depth - 1)

    @staticmethod
    def _is_base_case(symbols: list[SymbolFrequency], max_depth: int) -> bool:
        """
        Проверяет, достигнута ли базовая ситуация.
        """
        return max_depth <= 0 or len(symbols) <= 1

    @staticmethod
    def _find_split_index(symbols: list[SymbolFrequency]) -> int:
        """
        Находит индекс разделения списка символов для минимизации разницы в суммарных частотах.
        """
        total = sum(sf.frequency for sf in symbols)
        acc = 0
        split_index = 0
        min_diff = float('inf')

        for i in range(1, len(symbols)):
            acc += symbols[i - 1].frequency
            diff = abs((total / 2) - acc)
            if diff < min_diff:
                min_diff = diff
                split_index = i

        return split_index

    def _handle_base_case(self, symbols: list[SymbolFrequency],
                          prefix: str) -> None:
        """
        Обрабатывает базовый случай, назначая коды символам.
        """
        for sf in symbols:
            self.codes[sf.symbol] = prefix or '0'

    def serialize(self) -> bytes:
        """
        Сериализует кодовую таблицу для сохранения в файл.
        """
        return pickle.dumps(self.codes)

    @staticmethod
    def deserialize(serialized_data: bytes) -> 'CodeTable':
        """
        Десериализует кодовую таблицу из байтовой строки.
        """
        codes = pickle.loads(serialized_data)
        code_table = CodeTable()
        code_table.codes = codes
        return code_table

    @staticmethod
    def restore_code_table_from_meta(metadata: dict[str, Any]) -> 'CodeTable':
        """
        Восстанавливает кодовую таблицу из метаданных.
        """
        code_table_data = metadata['code_table']
        code_table = CodeTable.deserialize(code_table_data)
        return code_table
