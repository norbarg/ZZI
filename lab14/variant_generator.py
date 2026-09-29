import json
import random
import string
import sys

THRESHOLD_OPTIONS = [0x7FFFF, 0xFFFFF, 0x1FFFFF, 0x3FFFFF]
LOOP_SIZE_OPTIONS = [500, 1000, 2000, 5000]


def generate_license_key(rng: random.Random) -> str:
    """Генерує унікальний ліцензійний ключ у форматі XXXX-XXXX-XXXX."""
    groups = []

    for _ in range(3):
        group = "".join(rng.choices(string.ascii_uppercase + string.digits, k=4))
        groups.append(group)

    return "-".join(groups)


def generate_variant(n: int) -> dict:
    if not (1 <= n <= 30):
        raise ValueError("Номер варіанта має бути в діапазоні від 1 до 30")

    rng = random.Random(n)

    license_key = generate_license_key(rng)
    anomaly_threshold = rng.choice(THRESHOLD_OPTIONS)
    loop_size = rng.choice(LOOP_SIZE_OPTIONS)

    return {
        "variant": n,
        "license_key": license_key,
        "anomaly_threshold": anomaly_threshold,
        "anomaly_threshold_hex": hex(anomaly_threshold),
        "loop_size": loop_size,
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

    print(f"Ліцензійний ключ для crackme.c: {variant['license_key']}")

    print(
        f"Поріг аномалії для anti_debug.c: "
        f"{variant['anomaly_threshold_hex']} "
        f"({variant['anomaly_threshold']} тактів)"
    )

    print(f"Розмір робочого циклу критичної ділянки: {variant['loop_size']} ітерацій")

    print(f"\nФайл створено: {out_path}")

    print(
        "Замініть SECRET-KEY у crackme.c на ваш ключ, "
        "ANOMALY_THRESHOLD та розмір циклу у anti_debug.c "
        "на ваші значення."
    )


if __name__ == "__main__":
    main()
