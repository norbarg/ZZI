import json
import random
import sys

APP_TYPES = [
    ("mail_relay", ["queue", "config", "logs"], "поштовий релей-сервер"),
    ("web_app", ["www", "config", "logs"], "вебзастосунок (за зразком методички)"),
    ("db_backup_agent", ["dumps", "config", "logs"], "агент резервного копіювання БД"),
    ("log_aggregator", ["incoming", "config", "logs"], "збирач логів з кількох джерел"),
    ("ftp_service", ["uploads", "config", "logs"], "FTP-сервіс завантаження файлів"),
]


ATTACK_TARGETS = [
    "/etc/shadow",
    "/etc/passwd",
    "/etc/ssh/ssh_host_rsa_key",
    "/root/.ssh/id_rsa",
    "/etc/sudoers",
]


CAPABILITY_SETS = [
    ["chown", "sys_time", "sys_admin"],
    ["sys_admin", "sys_module", "dac_override"],
    ["chown", "fsetid", "sys_ptrace"],
    ["sys_time", "net_admin", "sys_admin"],
]


def generate_variant(n: int) -> dict:
    if not (1 <= n <= 30):
        raise ValueError("Номер варіанта має бути в діапазоні від 1 до 30")

    rng = random.Random(n)

    app_name, subdirs, app_description = APP_TYPES[n % len(APP_TYPES)]

    attack_target = ATTACK_TARGETS[n % len(ATTACK_TARGETS)]

    denied_capabilities = CAPABILITY_SETS[n % len(CAPABILITY_SETS)]

    # Унікальна кількість тестових легітимних файлів
    num_content_files = rng.randint(2, 4)

    return {
        "variant": n,
        "app_name": app_name,
        "app_description": app_description,
        "subdirectories": subdirs,
        "num_content_files": num_content_files,
        "attack_target": attack_target,
        "denied_capabilities": denied_capabilities,
    }


def main():
    if len(sys.argv) != 2:
        print("Використання: python variant_generator.py <номер_варіанта: 1-30>")
        sys.exit(1)

    n = int(sys.argv[1])

    variant = generate_variant(n)

    out_path = f"variant_{n}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(variant, f, ensure_ascii=False, indent=2)

    print(f"Варіант №{n}")
    print(f"Тип застосунку: {variant['app_name']} – {variant['app_description']}")
    print(f"Піддиректорії: {variant['subdirectories']}")
    print(f"Кількість тестових файлів контенту: {variant['num_content_files']}")
    print(f"Ціль сценарію атаки: {variant['attack_target']}")
    print(f"Можливості ядра для явної заборони: {variant['denied_capabilities']}")

    print(f"\nФайл створено: {out_path}")
    print("Адаптуйте target_app.py та profile_generator.py під ці параметри.")


if __name__ == "__main__":
    main()
