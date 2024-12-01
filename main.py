import logging
from enum import Enum
from archiver import Archiver
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='archiver.log',
    filemode='w',
    encoding='utf-8'
)

class Command(str, Enum):
    ENCODE = '1'
    EXTRACT = '2'
    EXIT = '3'

def main() -> None:
    while True:
        archiver = Archiver()
        print("\n=== Shannon-Fano Archiver ===")
        print("Выберите действие:")
        print(f"{Command.ENCODE.value}. Создать архив")
        print(f"{Command.EXTRACT.value}. Извлечь архив")
        print(f"{Command.EXIT.value}. Выйти из программы")

        choice = input(f"Введите номер действия ({Command.ENCODE.value}/{Command.EXTRACT.value}/{Command.EXIT.value}): ").strip()

        if choice == Command.ENCODE.value:
            paths_input = input(
                "Введите пути к файлам или каталогам для архивации (разделяйте запятыми): ").strip()
            if not paths_input:
                print("Ошибка: Путь(и) не могут быть пустыми.")
                continue
            paths = [path.strip() for path in paths_input.split(',')]
            archiver.add_paths(paths)

            archive_file_path = input(
                "Введите путь для сохранения архива (например, C:\\Games\\test_for_shannon\\archive.bin): ").strip()
            if not archive_file_path:
                print("Ошибка: Путь для архива не может быть пустым.")
                continue

            password = input(
                "Установите пароль для архива (оставьте пустым для отсутствия пароля): ").strip()

            archive_path = Path(archive_file_path).resolve()
            if archive_path.is_dir():
                archive_path = archive_path / "archive.bin"
                print(
                    f"Указан путь к директории. Архив будет сохранён как '{archive_path}'."
                )

            archiver.archive(str(archive_path), password if password else None)

        elif choice == Command.EXTRACT.value:
            archive_file_path = input(
                "Введите путь к архиву для извлечения (например, C:\\Games\\test_for_shannon\\archive.bin): ").strip()
            if not archive_file_path:
                print("Ошибка: Путь к архиву не может быть пустым.")
                continue
            extract_path = input(
                "Введите путь для извлечения файлов (оставьте пустым для текущего каталога): ").strip()
            extract_path = extract_path if extract_path else None

            password = input(
                "Введите пароль для извлечения (если архив не защищён паролем, оставьте пустым): ").strip()

            archiver.extract(archive_file_path, extract_path,
                             password if password else None)

        elif choice == Command.EXIT.value:
            print("Выход из программы.")
            break

        else:
            print("Некорректный выбор.")

if __name__ == "__main__":
    main()
