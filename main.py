from encoder import Encoder
from decoder import Decoder


def main() -> None:
    while True:
        print("\n=== Shannon-Fano Codec ===")
        print("Выберите действие:")
        print("1. Кодировать файл")
        print("2. Декодировать файл")
        print("3. Выйти из программы")

        choice = input("Введите номер действия: ").strip()

        if choice == '1':
            file_path = input("Введите полный путь к файлу для кодирования (с расширением): ").strip()
            if not file_path:
                print("Ошибка: Путь к файлу не может быть пустым.")
                continue
            encoder = Encoder(file_path)
            encoder.encode()

        elif choice == '2':
            encoded_file_path = input("Введите полный путь к закодированному файлу для декодирования: ").strip()
            if not encoded_file_path:
                print("Ошибка: Путь к закодированному файлу не может быть пустым.")
                continue

            decoder = Decoder(encoded_file_path)
            decoder.decode()

        elif choice == '3':
            break


if __name__ == "__main__":
    main()
