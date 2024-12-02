from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple


@dataclass
class FileInfo:
    absolute_path: Path | None
    relative_path: str
    is_dir: bool
    data: bytes = b''
    encoded_data: bytes = b''
    extra_bits: int = 0
    original_size: int = 0
    compressed_size: int = 0


class EncryptedData(NamedTuple):
    nonce: bytes
    data: bytes


class ArchiveHeader(NamedTuple):
    has_password: bool
    salt: bytes
    nonce_meta: bytes


class EncryptedFilesInfo(NamedTuple):
    encrypted_metadata: bytes
    encrypted_file_data: list[EncryptedData]
    salt: bytes
    nonce_meta: bytes


class EncodedBytesData(NamedTuple):
    encoded_bytes: bytes
    extra_bits_count: int


class SymbolFrequency(NamedTuple):
    symbol: int
    frequency: int
