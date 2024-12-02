import os
import logging
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

from file_handler import FileHandler
from util_classes import FileInfo, EncryptedFilesInfo, EncryptedData, \
    ArchiveHeader
from metadata_handler import MetadataHandler, Metadata


def derive_key(password: str, salt: bytes) -> bytes:
    """Генерирует ключ шифрования из пароля и соли."""
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2 ** 14,
        r=8,
        p=1,
    )
    key = kdf.derive(password.encode())
    return key


def encrypt_data(key: bytes, data: bytes) -> EncryptedData:
    """Шифрует данные с использованием AES-GCM."""
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    encrypted_data = aesgcm.encrypt(nonce, data, None)
    return EncryptedData(nonce, encrypted_data)


def decrypt_data(key: bytes, nonce: bytes, encrypted_data: bytes) -> bytes:
    """Дешифрует данные с использованием AES-GCM."""
    aesgcm = AESGCM(key)
    data = aesgcm.decrypt(nonce, encrypted_data, None)
    return data


def read_archive_header(archive_file) -> ArchiveHeader:
    """Читает заголовок архива, включая флаг пароля, соль и нонс метаданных."""
    pass_length = 1
    password_flag = archive_file.read(pass_length)
    if len(password_flag) < pass_length:
        logging.error(
            "Архив поврежден или имеет неверный формат (нет флага пароля)."
        )
        raise ValueError("Неверный формат архива")
    has_password = bool(password_flag[0])

    salt = FileHandler.read_bytes_with_size(archive_file, "соль")
    nonce_meta = FileHandler.read_bytes_with_size(archive_file,
                                                  "нонс метаданных")

    return ArchiveHeader(has_password, salt, nonce_meta)


def read_and_decrypt_metadata(
        archive_file,
        key: bytes | None,
        nonce_meta: bytes,
        has_password: bool
) -> Metadata | None:
    """Читает и дешифрует метаданные из архива."""
    try:
        encrypted_metadata = FileHandler.read_bytes_with_size(archive_file,
                                                              "метаданных")
    except ValueError:
        return None

    if has_password:
        if key is None:
            logging.error("Ключ шифрования не предоставлен.")
            return None
        try:
            metadata_serialized = decrypt_data(key, nonce_meta,
                                               encrypted_metadata)
        except InvalidTag:
            logging.error("Неверный пароль.")
            return None
        except Exception as e:
            logging.error(f"Ошибка при дешифровании метаданных: {e}")
            return None
    else:
        metadata_serialized = encrypted_metadata

    try:
        metadata_obj = MetadataHandler.deserialize_metadata(
            metadata_serialized)
        logging.debug(f"Метаданные загружены: {metadata_obj}")
        return metadata_obj
    except Exception as e:
        logging.error(f"Ошибка при десериализации метаданных: {e}")
        return None


def read_and_decrypt_metadata_with_password(
        archive_file,
        password: str | None
) -> tuple[Metadata, bytes | None] | None:
    """
    Читает заголовок архива, обрабатывает ввод пароля и дешифрует метаданные.
    Возвращает объект Metadata и ключ дешифрования (если пароль установлен).
    """
    try:
        has_password, salt, nonce_meta = read_archive_header(archive_file)
    except ValueError:
        return None

    if has_password:
        if not password:
            print("Этот архив защищён паролем.")
            password = input("Введите пароль для извлечения: ").strip()
        key = derive_key(password, salt)
    else:
        key = None

    metadata = read_and_decrypt_metadata(archive_file, key, nonce_meta,
                                         has_password)
    if metadata is None:
        return None

    return metadata, key


def get_files_encrypt_info(
        salt_size: int,
        file_info_list: list[FileInfo],
        metadata_serialized: bytes,
        password: str | None
) -> EncryptedFilesInfo:
    """Шифрует метаданные и данные файлов, если пароль установлен."""
    if password:
        salt = os.urandom(salt_size)
        key = derive_key(password, salt)

        encrypted_meta = encrypt_data(key, metadata_serialized)
        encrypted_file_data = encrypt_file_data(file_info_list, key)

        logging.debug("Данные успешно зашифрованы.")
    else:
        salt = b''
        encrypted_meta = EncryptedData(nonce=b'', data=metadata_serialized)
        encrypted_file_data = [
            EncryptedData(nonce=b'', data=file_info.encoded_data)
            for file_info in file_info_list if not file_info.is_dir
        ]
    return EncryptedFilesInfo(
        encrypted_metadata=encrypted_meta.data,
        encrypted_file_data=encrypted_file_data,
        salt=salt,
        nonce_meta=encrypted_meta.nonce
    )


def encrypt_file_data(
        file_info_list: list[FileInfo],
        key: bytes
) -> list[EncryptedData]:
    """Шифрует данные файлов."""
    encrypted_file_data = []
    for file_info in file_info_list:
        if not file_info.is_dir:
            encrypted_data = encrypt_data(key, file_info.encoded_data)
            encrypted_file_data.append(encrypted_data)
    return encrypted_file_data


def read_and_decrypt_file_data(
        archive_file,
        key: bytes | None,
        has_password: bool,
        description: str
) -> bytes | None:
    """Читает и дешифрует данные файла из архива."""
    try:
        nonce_data = FileHandler.read_bytes_with_size(archive_file,
                                                      f"нонса {description}")
        encrypted_data = FileHandler.read_bytes_with_size(archive_file,
                                                          f"данных {description}")
    except ValueError:
        return None

    if has_password:
        if key is None:
            logging.error("Ключ шифрования не предоставлен.")
            return None
        try:
            data = decrypt_data(key, nonce_data, encrypted_data)
        except InvalidTag:
            logging.error("Неверный пароль.")
            return None
        except Exception as e:
            logging.error(f"Ошибка при дешифровании {description}: {e}")
            return None
    else:
        data = encrypted_data

    return data
