import pickle
from dataclasses import dataclass

from util_classes import FileInfo
from code_table import CodeTable


@dataclass
class Metadata:
    code_table: CodeTable
    file_info_list: list[FileInfo]


class MetadataHandler:
    @staticmethod
    def serialize_metadata(file_info_list: list[FileInfo],
                           code_table: CodeTable) -> bytes:
        """
        Сериализует метаданные для сохранения в архив.
        """
        metadata = {
            'file_info_list': [{
                'relative_path': file_info.relative_path,
                'is_dir': file_info.is_dir,
                'extra_bits': file_info.extra_bits,
                'encoded_data': file_info.encoded_data,
            } for file_info in file_info_list],
            'code_table': code_table.serialize()
        }
        metadata_serialized = pickle.dumps(metadata)
        return metadata_serialized

    @staticmethod
    def deserialize_metadata(metadata_serialized: bytes) -> Metadata | None:
        """
        Десериализует метаданные из байтовой строки.
        """
        try:
            metadata_dict = pickle.loads(metadata_serialized)
            code_table = CodeTable.deserialize(metadata_dict['code_table'])
            file_info_list = [
                FileInfo(
                    absolute_path=None,
                    relative_path=fi['relative_path'],
                    is_dir=fi['is_dir'],
                    encoded_data=fi['encoded_data'] if not fi[
                        'is_dir'] else b'',
                    extra_bits=fi['extra_bits'],
                    data=b'',
                    original_size=0,
                    compressed_size=len(fi['encoded_data']) if not fi[
                        'is_dir'] else 0,
                )
                for fi in metadata_dict['file_info_list']
            ]
            metadata = Metadata(
                code_table=code_table,
                file_info_list=file_info_list
            )
            return metadata
        except Exception as e:
            import logging
            logging.error(f"Ошибка при десериализации метаданных: {e}")
            return None
