import json
import random
from pathlib import Path


def setup_test_data():
    with open("variant_3.json", "r", encoding="utf-8") as file:
        variant = json.load(file)

    rng = random.Random(variant["variant"])
    root = Path("production_data")

    if root.exists():
        raise FileExistsError(
            "Папка production_data вже існує. Щоб не втратити дані, створення зупинено."
        )

    directories = variant["directory_structure"]
    files_per_directory = variant["num_files"]

    print("=" * 60)
    print("СТВОРЕННЯ ТЕСТОВОГО СЕРЕДОВИЩА")
    print("=" * 60)

    total_files = 0

    for directory_name in directories:
        directory = root / directory_name
        directory.mkdir(parents=True, exist_ok=True)

        print(f"\nДиректорія: {directory}")

        for index in range(1, files_per_directory + 1):
            file_path = directory / f"file_{index:02d}.txt"

            content = (
                f"Лабораторна робота №24\n"
                f"Варіант: {variant['variant']}\n"
                f"Директорія: {directory_name}\n"
                f"Файл: {index}\n"
                f"Ідентифікатор: {rng.randint(10000, 99999)}\n"
                f"Версія даних: 1\n"
                f"Стан: початковий\n"
            )

            file_path.write_text(content, encoding="utf-8")
            total_files += 1

            print(f"  [OK] {file_path.name}")

    print("\n" + "=" * 60)
    print(f"Створено директорій: {len(directories)}")
    print(f"Файлів у кожній: {files_per_directory}")
    print(f"Загальна кількість файлів: {total_files}")
    print(f"Шлях: {root.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    setup_test_data()
