import json
import random
import sys

IMAGE_SIZES = [
    (150, 100),
    (200, 150),
    (180, 120),
    (220, 160),
    (160, 140),
]

SECRET_MESSAGES = [
    "Зустріч перенесено на 15:00",
    "Пароль до сервера: Xk9mP2",
    "Документи передано кур'єром",
    "Термінова нарада о 10 ранку",
    "Резервна копія на диску D",
    "Контракт підписано вчора",
    "Перевірка системи завершена",
    "Новий ключ доступу активовано",
]

FILL_PERCENTAGE_OPTIONS = [25, 50, 75, 100]


def generate_variant(n: int) -> dict:
    if not (1 <= n <= 30):
        raise ValueError("Номер варіанта має бути в діапазоні від 1 до 30")

    rng = random.Random(n)

    width, height = IMAGE_SIZES[n % len(IMAGE_SIZES)]
    secret_message = SECRET_MESSAGES[n % len(SECRET_MESSAGES)]
    fill_percentage = FILL_PERCENTAGE_OPTIONS[n % len(FILL_PERCENTAGE_OPTIONS)]
    image_seed = rng.randint(1, 100000)

    return {
        "variant": n,
        "image_width": width,
        "image_height": height,
        "image_seed": image_seed,
        "secret_message": secret_message,
        "fill_percentage": fill_percentage,
    }


def main():
    if len(sys.argv) != 2:
        print("Использование: python variant_generator.py <номер_варианта>")
        sys.exit(1)

    n = int(sys.argv[1])
    variant = generate_variant(n)

    out_path = f"variant_{n}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(variant, f, ensure_ascii=False, indent=2)

    print(f"Варіант №{n}")
    print(
        f"Розмір тестового зображення: "
        f"{variant['image_width']}x{variant['image_height']}"
    )
    print(f"Seed для генерації зображення: {variant['image_seed']}")
    print(f"Секретне повідомлення: '{variant['secret_message']}'")
    print(f"Відсоток заповнення: {variant['fill_percentage']}%")
    print(f"\nФайл створено: {out_path}")


if __name__ == "__main__":
    main()
