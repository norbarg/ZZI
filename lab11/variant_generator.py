import json
import random
import sys

FLAG_PREFIXES = [
    "ACCESS_GRANTED",
    "ROOT_SHELL_OBTAINED",
    "PRIVILEGE_ESCALATED",
    "SECRET_DATA_LEAKED",
    "AUTH_BYPASSED",
    "SYSTEM_COMPROMISED",
]

BUFFER_SIZES = [32, 48, 64, 96, 128]


def generate_variant(n: int) -> dict:
    if not (1 <= n <= 30):
        raise ValueError("Номер варіанта має бути в діапазоні від 1 до 30")

    rng = random.Random(n)

    buffer_size = rng.choice(BUFFER_SIZES)

    flag_prefix = FLAG_PREFIXES[n % len(FLAG_PREFIXES)]
    flag_suffix = "".join(rng.choices("0123456789ABCDEF", k=8))
    flag_value = f"{flag_prefix}_{flag_suffix}"

    payload_sizes = sorted(
        [
            max(4, buffer_size // 8),
            buffer_size,
            buffer_size + rng.randint(8, 24),
            buffer_size + rng.randint(100, 150),
        ]
    )

    return {
        "variant": n,
        "buffer_size": buffer_size,
        "flag_value": flag_value,
        "payload_sizes": payload_sizes,
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
    print(f"Розмір вразливого буфера: {variant['buffer_size']} байт")
    print(f"Значення секретного прапора: {variant['flag_value']}")
    print(f"Розміри payload для тестування: {variant['payload_sizes']}")

    print(f"\nФайл створено: {out_path}")
    print(
        f"Змініть у vulnerable.c: char buffer[{variant['buffer_size']}]; "
        f"та рядок printf у print_secret_flag() на значення прапора вище."
    )


if __name__ == "__main__":
    main()
