import csv
import hashlib
import shutil
from pathlib import Path

BACKUP_DIR = Path("backups")
LOG_FILE = BACKUP_DIR / "backup_log.csv"
TEST_DIR = Path("corruption_test")


def compute_sha256(path):
    hasher = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def load_backup_entries():
    entries = []

    with open(LOG_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) < 5:
                continue

            timestamp, backup_type, filename, size, checksum = row[:5]

            entries.append(
                {
                    "timestamp": timestamp,
                    "type": backup_type,
                    "filename": filename,
                    "checksum": checksum,
                }
            )

    return entries


def verify_archive(path, expected_hash):
    if not path.exists():
        return False

    actual_hash = compute_sha256(path)
    return actual_hash == expected_hash


def main():
    entries = load_backup_entries()

    print("=" * 65)
    print("ПЕРЕВІРКА ЦІЛІСНОСТІ РЕЗЕРВНИХ КОПІЙ")
    print("=" * 65)

    passed = 0
    failed = 0

    for entry in entries:
        archive_path = BACKUP_DIR / entry["filename"]

        valid = verify_archive(archive_path, entry["checksum"])

        status = "[OK]" if valid else "[ERROR]"

        print(f"{status} {entry['filename']}")

        if valid:
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 65)
    print("РЕЗУЛЬТАТ ПЕРЕВІРКИ")
    print("=" * 65)
    print(f"Перевірено архівів: {len(entries)}")
    print(f"Успішно: {passed}")
    print(f"Помилок: {failed}")

    if failed:
        print("[ERROR] Є пошкоджені архіви!")
        return

    print("[OK] Усі резервні копії цілісні!")

    print("\n" + "=" * 65)
    print("ТЕСТ НАВМИСНОГО ПОШКОДЖЕННЯ АРХІВУ")
    print("=" * 65)

    TEST_DIR.mkdir(exist_ok=True)

    original = BACKUP_DIR / entries[-1]["filename"]
    corrupted = TEST_DIR / f"corrupted_{original.name}"

    shutil.copy2(original, corrupted)

    with open(corrupted, "ab") as file:
        file.write(b"INTENTIONAL_CORRUPTION_TEST")

    expected_hash = entries[-1]["checksum"]
    actual_hash = compute_sha256(corrupted)

    print(f"Тестовий архів: {corrupted}")
    print(f"Очікуваний SHA-256: {expected_hash}")
    print(f"Фактичний SHA-256: {actual_hash}")

    if not verify_archive(corrupted, expected_hash):
        print("\n[OK] Пошкодження архіву успішно виявлено!")
    else:
        print("\n[ERROR] Пошкодження не виявлено!")

    print("\nОригінальні резервні копії не змінено.")


if __name__ == "__main__":
    main()
