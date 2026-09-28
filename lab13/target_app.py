import json
import os

VARIANT_FILE = "variant_3.json"

with open(VARIANT_FILE, "r", encoding="utf-8") as f:
    VARIANT = json.load(f)


BASE_DIR = "app_data"

INCOMING_DIR = os.path.join(BASE_DIR, "incoming")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
LOG_DIR = os.path.join(BASE_DIR, "logs")

ATTACK_TARGET = VARIANT["attack_target"]
NUM_CONTENT_FILES = VARIANT["num_content_files"]


def setup_environment():
    """
    Створює робочу структуру каталогів
    для застосунку log_aggregator.
    """

    os.makedirs(INCOMING_DIR, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    # Конфігурація агрегатора логів
    config_path = os.path.join(CONFIG_DIR, "aggregator.conf")

    with open(config_path, "w", encoding="utf-8") as f:
        f.write("poll_interval=5\n")
        f.write("output_file=combined.log\n")

    # Створення тестових лог-файлів
    for i in range(1, NUM_CONTENT_FILES + 1):
        log_path = os.path.join(INCOMING_DIR, f"source_{i}.log")

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"2026-09-28 INFO Test message from source {i}\n")


def read_config():
    """
    Легітимна операція:
    читання конфігурації застосунку.
    """

    config_path = os.path.join(CONFIG_DIR, "aggregator.conf")

    with open(config_path, "r", encoding="utf-8") as f:
        return f.read()


def aggregate_logs():
    """
    Легітимна операція:
    читання вхідних логів та формування
    загального лог-файлу.
    """

    combined_log = ""

    for i in range(1, NUM_CONTENT_FILES + 1):
        log_path = os.path.join(INCOMING_DIR, f"source_{i}.log")

        with open(log_path, "r", encoding="utf-8") as f:
            combined_log += f.read()

    output_path = os.path.join(LOG_DIR, "combined.log")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(combined_log)

    return combined_log


def write_service_log(message: str):
    """
    Легітимна операція:
    запис службового повідомлення.
    """

    log_path = os.path.join(LOG_DIR, "service.log")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def suspicious_access_attempt():
    """
    Нелегітимна операція:
    спроба читання файлу, заданого
    сценарієм атаки для варіанта №3.
    """

    try:
        with open(ATTACK_TARGET, "r", encoding="utf-8") as f:
            return f.read()

    except (PermissionError, FileNotFoundError, OSError):
        return None


def main():
    setup_environment()

    print("=== Log Aggregator ===")

    config = read_config()
    print("\nКонфігурацію прочитано:")
    print(config)

    aggregated = aggregate_logs()
    print("Об'єднані логи:")
    print(aggregated)

    write_service_log("Log aggregation completed successfully")

    print("Службовий лог успішно записано.")

    result = suspicious_access_attempt()

    print(f"\nСпроба доступу до: {ATTACK_TARGET}")

    if result is not None:
        print("[!] УВАГА: доступ до системного файлу отримано.")
    else:
        print("[OK] Доступ до системного файлу не отримано.")


if __name__ == "__main__":
    main()
