import pickle
from codeTable import CodeTable
from typing import Any


class MetadataHandler:
    @staticmethod
    def serialize_metadata(file_info_list: list[dict[str, Any]],
                           code_table: CodeTable) -> bytes:
        """
        Сериализует метаданные для сохранения в архив.
        """
        metadata = {
            'file_info_list': [{
                'relative_path': file_info['relative_path'],
                'is_dir': file_info['is_dir'],
                'extra_bits': file_info.get('extra_bits', 0),
                'data_size': len(file_info['encoded_data']) if not file_info[
                    'is_dir'] else 0,
            } for file_info in file_info_list],
            'code_table': code_table.serialize()
        }
        metadata_serialized = pickle.dumps(metadata)
        return metadata_serialized

    @staticmethod
    def deserialize_metadata(metadata_serialized: bytes) -> dict[str, Any]:
        """
        Десериализует метаданные из байтовой строки.
        """
        metadata = pickle.loads(metadata_serialized)
        return metadata
