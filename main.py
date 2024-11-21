from algorithm import *


def main():
    base_name = input("Введите имя файла без расширения: ").strip()
    if not base_name:
        print("Ошибка: Имя файла не может быть пустым.")
        return

    # Создание экземпляра кодека
    codec = ShannonFanoCodec(base_name)

    # Кодирование файла
    codec.encode()

    # Декодирование файла
    codec.decode()

    # Проверка целостности
    codec.verify_integrity()

if __name__ == "__main__":
    main()