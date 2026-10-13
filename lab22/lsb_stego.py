import json
import random

import numpy as np
from PIL import Image


# 1. Перетворення повідомлення на біти
def message_to_bits(message: bytes) -> np.ndarray:
    length_bits = np.unpackbits(np.array([len(message)], dtype=">u4").view(np.uint8))
    message_bits = np.unpackbits(np.frombuffer(message, dtype=np.uint8))
    return np.concatenate([length_bits, message_bits])


def bits_to_message(bits: np.ndarray) -> bytes:
    length = int.from_bytes(np.packbits(bits[:32]).tobytes(), byteorder="big")
    message_bits = bits[32 : 32 + length * 8]
    return np.packbits(message_bits).tobytes()


# 2. LSB Replacement
def lsb_replacement_embed(pixels, bits):
    flat = pixels.flatten().copy()

    if len(bits) > len(flat):
        raise ValueError("Повідомлення перевищує ємність зображення")

    flat[: len(bits)] = (flat[: len(bits)] & 254) | bits.astype(np.uint8)
    return flat.reshape(pixels.shape)


def lsb_replacement_extract(pixels, num_bits):
    return (pixels.flatten()[:num_bits] & 1).astype(np.uint8)


# 3. LSB Matching
def lsb_matching_embed(pixels, bits, rng_seed=42):
    rng = random.Random(rng_seed)
    flat = pixels.flatten().copy().astype(np.int16)

    if len(bits) > len(flat):
        raise ValueError("Повідомлення перевищує ємність зображення")

    for i, bit in enumerate(bits):
        value = int(flat[i])

        if (value & 1) == bit:
            continue

        if value == 0:
            flat[i] = 1
        elif value == 255:
            flat[i] = 254
        else:
            flat[i] = value + (1 if rng.random() < 0.5 else -1)

    return flat.astype(np.uint8).reshape(pixels.shape)


def lsb_matching_extract(pixels, num_bits):
    return lsb_replacement_extract(pixels, num_bits)


# 4. Метрики якості
def compute_mse(original, modified):
    diff = original.astype(np.float64) - modified.astype(np.float64)
    return float(np.mean(diff**2))


def compute_psnr(original, modified):
    mse = compute_mse(original, modified)

    if mse == 0:
        return float("inf")

    return 10 * np.log10(255**2 / mse)


# 5. Генерація тестового зображення
def create_test_image(width, height, seed):
    rng = np.random.RandomState(seed)
    image = np.full((height, width), 128, dtype=np.float64)

    num_blobs = max(10, (width * height) // 2000)
    yy, xx = np.ogrid[:height, :width]

    for _ in range(num_blobs):
        cx = rng.randint(0, width)
        cy = rng.randint(0, height)
        radius = rng.randint(
            min(width, height) // 15,
            min(width, height) // 5,
        )
        brightness = rng.randint(20, 235)

        mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius**2
        image[mask] = brightness

    noise = rng.normal(0, 3, (height, width))
    return np.clip(image + noise, 0, 255).astype(np.uint8)


# 6. Основна програма
def main():
    with open("variant_3.json", "r", encoding="utf-8") as file:
        variant = json.load(file)

    width = variant["image_width"]
    height = variant["image_height"]
    seed = variant["image_seed"]
    secret_text = variant["secret_message"]

    cover = create_test_image(width, height, seed)

    message = secret_text.encode("utf-8")
    bits = message_to_bits(message)

    print("=" * 60)
    print("КРОК 1. ПІДГОТОВКА ЗОБРАЖЕННЯ")
    print("=" * 60)
    print(f"Варіант: {variant['variant']}")
    print(f"Розмір: {width}x{height}")
    print(f"Seed: {seed}")
    print(f"Повідомлення: {secret_text}")
    print(f"Розмір повідомлення: {len(bits)} біт")
    print(f"Ємність контейнера: {width * height} біт")

    print("\n" + "=" * 60)
    print("КРОК 2. LSB REPLACEMENT")
    print("=" * 60)

    replacement = lsb_replacement_embed(cover, bits)
    extracted_bits = lsb_replacement_extract(replacement, len(bits))
    recovered = bits_to_message(extracted_bits).decode("utf-8")

    print(f"Вилучене повідомлення: {recovered}")
    print(f"Коректність: {recovered == secret_text}")
    print(f"MSE: {compute_mse(cover, replacement):.6f}")
    print(f"PSNR: {compute_psnr(cover, replacement):.2f} дБ")

    print("\n" + "=" * 60)
    print("КРОК 3. LSB MATCHING")
    print("=" * 60)

    matching = lsb_matching_embed(cover, bits, rng_seed=seed)
    extracted_bits = lsb_matching_extract(matching, len(bits))
    recovered = bits_to_message(extracted_bits).decode("utf-8")

    print(f"Вилучене повідомлення: {recovered}")
    print(f"Коректність: {recovered == secret_text}")
    print(f"MSE: {compute_mse(cover, matching):.6f}")
    print(f"PSNR: {compute_psnr(cover, matching):.2f} дБ")

    print("\n" + "=" * 60)
    print("КРОК 4. ПОРІВНЯННЯ МЕТОДІВ")
    print("=" * 60)

    print(f"{'Метод':20} {'MSE':>12} {'PSNR (дБ)':>12}")
    print("-" * 46)

    for name, result in [
        ("LSB Replacement", replacement),
        ("LSB Matching", matching),
    ]:
        print(
            f"{name:20} "
            f"{compute_mse(cover, result):>12.6f} "
            f"{compute_psnr(cover, result):>12.2f}"
        )

    Image.fromarray(cover).save("cover.bmp")
    Image.fromarray(replacement).save("stego_replacement.bmp")
    Image.fromarray(matching).save("stego_matching.bmp")

    print("\nЗображення успішно збережено:")
    print(" - cover.bmp")
    print(" - stego_replacement.bmp")
    print(" - stego_matching.bmp")


if __name__ == "__main__":
    main()
