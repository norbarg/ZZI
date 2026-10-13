import json
import sys
from pathlib import Path


def modify_test_data(round_number):
    with open("variant_3.json", "r", encoding="utf-8") as file:
        variant = json.load(file)

    max_rounds = variant["num_incremental_rounds"]

    if not 1 <= round_number <= max_rounds:
        raise ValueError(f"Номер раунду має бути від 1 до {max_rounds}")

    root = Path("production_data")

    if not root.is_dir():
        raise FileNotFoundError("Директорію production_data не знайдено")

    directories = variant["directory_structure"]

    # Для кожного раунду змінюємо по одному файлу в кожній директорії.
    file_index = round_number

    print("=" * 60)
    print(f"РАУНД {round_number}. МОДИФІКАЦІЯ ТЕСТОВИХ ФАЙЛІВ")
    print("=" * 60)

    for directory_name in directories:
        file_path = root / directory_name / f"file_{file_index:02d}.txt"

        if not file_path.is_file():
            raise FileNotFoundError(f"Файл не знайдено: {file_path}")

        with open(file_path, "a", encoding="utf-8") as file:
            file.write(
                f"\nІнкрементна зміна, раунд {round_number}\n"
                f"Оновлення тестових даних для резервного копіювання.\n"
            )

        print(f"[MODIFIED] {file_path}")

    print("\nЗмінено файлів: 3")
    print("[OK] Модифікацію завершено!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Використання: python modify_test_data.py <номер_раунду>")
        sys.exit(1)

    modify_test_data(int(sys.argv[1]))
