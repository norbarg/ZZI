import csv
import hashlib
import json
import shutil
import time
from pathlib import Path
from zipfile import ZipFile

SOURCE_DIR = Path("production_data")
BACKUP_DIR = Path("backups")
DRILL_DIR = Path("drill_workspace")
TEST_PRODUCTION = DRILL_DIR / "production_data"
RESTORED_DIR = DRILL_DIR / "restored"


def sha256_file(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def snapshot_files(directory):
    return {
        file.relative_to(directory).as_posix(): sha256_file(file)
        for file in directory.rglob("*")
        if file.is_file()
    }


def read_backup_log():
    entries = []
    with open(BACKUP_DIR / "backup_log.csv", newline="", encoding="utf-8") as file:
        for row in csv.reader(file):
            if len(row) >= 5:
                entries.append(
                    {
                        "type": row[1],
                        "filename": row[2],
                        "checksum": row[4],
                    }
                )
    return entries


def get_backup_chain():
    entries = read_backup_log()
    full_indices = [i for i, entry in enumerate(entries) if entry["type"] == "full"]

    if not full_indices:
        raise RuntimeError("Повний бекап не знайдено!")

    chain = entries[full_indices[-1] :]

    if any(entry["type"] != "incremental" for entry in chain[1:]):
        raise RuntimeError("Некоректний ланцюжок резервних копій")

    return chain


def restore_from_chain(chain):
    RESTORED_DIR.mkdir(parents=True, exist_ok=True)

    for entry in chain:
        archive_path = BACKUP_DIR / entry["filename"]

        if sha256_file(archive_path) != entry["checksum"]:
            raise RuntimeError(f"Порушено цілісність архіву: {entry['filename']}")

        with ZipFile(archive_path) as archive:
            metadata = json.loads(archive.read("_backup_metadata.json"))

            # Архіви сформовано нашим backup_system.py.
            for member in archive.namelist():
                if member == "_backup_metadata.json":
                    continue

                target = RESTORED_DIR / member
                if not target.resolve().is_relative_to(RESTORED_DIR.resolve()):
                    raise RuntimeError("Небезпечний шлях в архіві")

                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source:
                    with open(target, "wb") as destination:
                        shutil.copyfileobj(source, destination)

            for deleted in metadata["deleted_files"]:
                target = RESTORED_DIR / "production_data" / deleted
                if target.is_file():
                    target.unlink()


def main():
    with open("variant_3.json", encoding="utf-8") as file:
        variant = json.load(file)

    if variant["disaster_type"] != "hardware_failure":
        raise ValueError("Очікується сценарій hardware_failure")

    if not SOURCE_DIR.is_dir():
        raise FileNotFoundError("Папку production_data не знайдено")

    if DRILL_DIR.exists():
        raise FileExistsError(
            "drill_workspace вже існує. Перевір її вміст перед повторним запуском."
        )

    print("=" * 65)
    print("DR DRILL: СИМУЛЯЦІЯ АПАРАТНОГО ЗБОЮ")
    print("=" * 65)

    shutil.copytree(SOURCE_DIR, TEST_PRODUCTION)
    before = snapshot_files(TEST_PRODUCTION)

    print(f"Файлів до аварії: {len(before)}")

    chain = get_backup_chain()
    print(f"Довжина ланцюжка: {len(chain)}")
    for entry in chain:
        print(f"  {entry['type'].upper()}: {entry['filename']}")

    print("\nСИМУЛЯЦІЯ ВТРАТИ НАКОПИЧУВАЧА")
    shutil.rmtree(TEST_PRODUCTION)
    print("[OK] Тестові виробничі дані видалено")

    print("\nВІДНОВЛЕННЯ З РЕЗЕРВНИХ КОПІЙ")
    start = time.perf_counter()

    restore_from_chain(chain)

    measured_rto = time.perf_counter() - start

    recovered = RESTORED_DIR / "production_data"
    after = snapshot_files(recovered)

    verified = before == after

    print(f"\nВиміряний RTO: {measured_rto:.6f} секунд")
    print(f"Файлів до аварії: {len(before)}")
    print(f"Файлів після відновлення: {len(after)}")
    print(f"Цілісність даних: {verified}")

    if verified:
        print("\n[OK] Аварійне відновлення успішне!")
    else:
        print("\n[ERROR] Відновлені дані відрізняються!")
        raise SystemExit(1)

    print("\nОригінальна production_data залишилася без змін.")


if __name__ == "__main__":
    main()
