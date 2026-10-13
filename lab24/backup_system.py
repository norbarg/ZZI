import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

SOURCE_DIR = Path("production_data")
BACKUP_DIR = Path("backups")
MANIFEST_FILE = BACKUP_DIR / "file_manifest.json"
LOG_FILE = BACKUP_DIR / "backup_log.csv"
CHECKSUM_FILE = BACKUP_DIR / "checksums.sha256"


def compute_sha256(file_path):
    hasher = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def get_file_manifest():
    manifest = {}

    for file_path in sorted(SOURCE_DIR.rglob("*")):
        if file_path.is_file():
            relative_path = file_path.relative_to(SOURCE_DIR).as_posix()
            manifest[relative_path] = compute_sha256(file_path)

    return manifest


def load_previous_manifest():
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    return None


def create_backup():
    if not SOURCE_DIR.is_dir():
        raise FileNotFoundError("Директорію production_data не знайдено")

    BACKUP_DIR.mkdir(exist_ok=True)

    previous_manifest = load_previous_manifest()
    current_manifest = get_file_manifest()

    backup_type = "full" if previous_manifest is None else "incremental"

    if backup_type == "full":
        changed_files = sorted(current_manifest)
    else:
        changed_files = sorted(
            path
            for path, checksum in current_manifest.items()
            if previous_manifest.get(path) != checksum
        )

    deleted_files = (
        sorted(set(previous_manifest) - set(current_manifest))
        if previous_manifest is not None
        else []
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    archive_name = f"backup_{backup_type}_{timestamp}.zip"
    archive_path = BACKUP_DIR / archive_name

    print("=" * 65)
    print("АВТОМАТИЗОВАНЕ РЕЗЕРВНЕ КОПІЮВАННЯ")
    print("=" * 65)
    print(f"Тип резервної копії: {backup_type.upper()}")
    print(f"Джерело: {SOURCE_DIR}")
    print(f"Архів: {archive_name}")
    print(f"Усього файлів: {len(current_manifest)}")
    print(f"Файлів для копіювання: {len(changed_files)}")
    print(f"Видалених файлів: {len(deleted_files)}")

    with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
        for relative_path in changed_files:
            archive.write(
                SOURCE_DIR / relative_path,
                arcname=f"production_data/{relative_path}",
            )
            print(f"  [BACKUP] {relative_path}")

        # Метадані потрібні для правильного відновлення видалених файлів.
        archive.writestr(
            "_backup_metadata.json",
            json.dumps(
                {
                    "type": backup_type,
                    "deleted_files": deleted_files,
                },
                ensure_ascii=False,
                indent=2,
            ),
        )

    archive_size = archive_path.stat().st_size
    archive_hash = compute_sha256(archive_path)

    with open(CHECKSUM_FILE, "a", encoding="utf-8") as file:
        file.write(f"{archive_hash}  {archive_name}\n")

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                timestamp,
                backup_type,
                archive_name,
                archive_size,
                archive_hash,
            ]
        )

    # Оновлюємо стан лише після успішного створення архіву.
    with open(MANIFEST_FILE, "w", encoding="utf-8") as file:
        json.dump(
            current_manifest,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 65)
    print("РЕЗУЛЬТАТ")
    print("=" * 65)
    print(f"Архів створено: {archive_path}")
    print(f"Розмір архіву: {archive_size} байт")
    print(f"SHA-256: {archive_hash}")
    print(f"Журнал: {LOG_FILE}")
    print("[OK] Резервне копіювання завершено успішно!")


if __name__ == "__main__":
    create_backup()
