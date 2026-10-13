import json
import random
import sys

DISASTER_SCENARIOS = [
    ("ransomware", "Атака шифрувальника-вимагача (Ransomware)"),
    ("hardware_failure", "Апаратний збій (вихід з ладу накопичувача)"),
]

DIRECTORY_STRUCTURES = [
    ["database", "config", "logs"],
    ["database", "config", "logs", "uploads"],
    ["accounting", "hr_records", "contracts"],
    ["source_code", "build_artifacts", "documentation"],
    ["customer_data", "invoices", "backups_meta"],
]

FILE_CONTENT_TEMPLATES = [
    "Client records: {names}",
    "Financial report Q{quarter} {year}: revenue {amount}",
    "Employee record #{id}: department {dept}",
    "Configuration: max_connections={conn}, timeout={timeout}",
]


def generate_variant(n: int) -> dict:
    if not (1 <= n <= 30):
        raise ValueError("Номер варіанта має бути в діапазоні від 1 до 30")

    rng = random.Random(n)

    disaster_type, disaster_description = DISASTER_SCENARIOS[
        n % len(DISASTER_SCENARIOS)
    ]

    directory_structure = DIRECTORY_STRUCTURES[n % len(DIRECTORY_STRUCTURES)]

    mtd_hours = rng.choice([8, 12, 16, 24, 48])
    rto_hours = round(rng.uniform(1, mtd_hours * 0.4), 1)
    wrt_hours = round(rng.uniform(0.5, mtd_hours * 0.25), 1)
    rpo_hours = rng.choice([0.5, 1, 2, 4, 8])

    num_files = rng.randint(3, 6)
    num_incremental_rounds = rng.randint(2, 4)

    return {
        "variant": n,
        "disaster_type": disaster_type,
        "disaster_description": disaster_description,
        "directory_structure": directory_structure,
        "mtd_hours": mtd_hours,
        "rto_hours": rto_hours,
        "wrt_hours": wrt_hours,
        "rpo_hours": rpo_hours,
        "num_files": num_files,
        "num_incremental_rounds": num_incremental_rounds,
    }


def main():
    if len(sys.argv) != 2:
        print("Використання: python variant_generator.py <номер_варіанта>")
        sys.exit(1)

    n = int(sys.argv[1])
    variant = generate_variant(n)

    out_path = f"variant_{n}.json"

    with open(out_path, "w", encoding="utf-8") as file:
        json.dump(variant, file, ensure_ascii=False, indent=2)

    print(f"Варіант №{n}")
    print(f"Сценарій інциденту: {variant['disaster_description']}")
    print(f"Структура файлової системи: {variant['directory_structure']}")

    print(
        f"Вимоги BIA: MTD={variant['mtd_hours']} год, "
        f"RTO={variant['rto_hours']} год, "
        f"WRT={variant['wrt_hours']} год, "
        f"RPO={variant['rpo_hours']} год"
    )

    total = round(variant["rto_hours"] + variant["wrt_hours"], 1)

    valid = total <= variant["mtd_hours"]

    print(
        f"Перевірка RTO + WRT <= MTD: "
        f"{total} <= {variant['mtd_hours']} -> "
        f"{'ВИКОНУЄТЬСЯ' if valid else 'ПОРУШЕНО'}"
    )

    print(f"Кількість файлів у кожній директорії: {variant['num_files']}")
    print(f"Кількість раундів інкрементних змін: {variant['num_incremental_rounds']}")

    print(f"\nФайл створено: {out_path}")


if __name__ == "__main__":
    main()
