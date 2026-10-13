import csv
import json

import numpy as np
from lsb_stego import (
    compute_mse,
    compute_psnr,
    lsb_matching_embed,
    lsb_replacement_embed,
)
from PIL import Image
from scipy import stats


# 1. Гістограма яскравості
def compute_histogram(pixels):
    histogram, _ = np.histogram(
        pixels.flatten(),
        bins=256,
        range=(0, 256),
    )
    return histogram


# 2. Статистичний тест хі-квадрат
def chi_square_pov_test(pixels):
    histogram = compute_histogram(pixels)

    chi_square_stat = 0.0
    degrees_of_freedom = 0

    for k in range(128):
        observed_even = histogram[2 * k]
        observed_odd = histogram[2 * k + 1]

        total = observed_even + observed_odd

        if total == 0:
            continue

        expected = total / 2

        chi_square_stat += (observed_even - expected) ** 2 / expected
        chi_square_stat += (observed_odd - expected) ** 2 / expected

        degrees_of_freedom += 1

    p_value = float(stats.chi2.sf(chi_square_stat, degrees_of_freedom))

    return {
        "chi_square": float(chi_square_stat),
        "degrees_of_freedom": degrees_of_freedom,
        "p_value": p_value,
        "suspected_lsb": p_value > 0.05,
    }


# 3. Аналіз пар значень
def analyze_pair_ratios(pixels, num_pairs=5):
    histogram = compute_histogram(pixels)

    pairs = []

    for k in range(128):
        even = int(histogram[2 * k])
        odd = int(histogram[2 * k + 1])
        total = even + odd

        if total == 0:
            continue

        ratio = even / odd if odd != 0 else float("inf")

        pairs.append(
            {
                "pair": (2 * k, 2 * k + 1),
                "even": even,
                "odd": odd,
                "ratio": ratio,
                "total": total,
            }
        )

    pairs.sort(key=lambda item: item["total"], reverse=True)

    return pairs[:num_pairs]


# 4. Основна програма
def main():
    with open("variant_3.json", "r", encoding="utf-8") as file:
        variant = json.load(file)

    seed = variant["image_seed"]
    fill_percentage = variant["fill_percentage"]

    cover = np.array(
        Image.open("cover.bmp").convert("L"),
        dtype=np.uint8,
    )

    capacity = cover.size

    percentages = sorted(set([25, 50, fill_percentage]))

    rng = np.random.default_rng(seed)
    random_bits = rng.integers(0, 2, size=capacity, dtype=np.uint8)

    print("=" * 70)
    print("ЛАБОРАТОРНА РОБОТА №22")
    print("СТЕГАНОГРАФІЯ В ЦИФРОВИХ ЗОБРАЖЕННЯХ")
    print("=" * 70)

    print(f"Варіант: {variant['variant']}")
    print(f"Розмір зображення: {cover.shape[1]}x{cover.shape[0]}")
    print(f"Ємність контейнера: {capacity} біт")
    print(f"Відсотки заповнення: {percentages}")

    cover_result = chi_square_pov_test(cover)

    print("\n" + "=" * 70)
    print("АНАЛІЗ ОРИГІНАЛЬНОГО ЗОБРАЖЕННЯ")
    print("=" * 70)

    print(f"Chi-square: {cover_result['chi_square']:.2f}")
    print(f"p-value: {cover_result['p_value']:.6f}")
    print(f"Підозра на LSB: {cover_result['suspected_lsb']}")

    results = []

    # 5. Експерименти для різних відсотків
    for percentage in percentages:
        num_bits = int(capacity * percentage / 100)
        payload = random_bits[:num_bits]

        replacement = lsb_replacement_embed(cover, payload)
        matching = lsb_matching_embed(cover, payload, rng_seed=seed)

        replacement_result = chi_square_pov_test(replacement)
        matching_result = chi_square_pov_test(matching)

        print("\n" + "=" * 70)
        print(f"ЕКСПЕРИМЕНТ: ЗАПОВНЕННЯ {percentage}%")
        print("=" * 70)

        print(f"Кількість вбудованих бітів: {num_bits}")

        print(
            f"\n{'Зображення':20} "
            f"{'Chi-square':>12} "
            f"{'p-value':>12} "
            f"{'Підозра LSB':>14}"
        )
        print("-" * 65)

        experiment = [
            ("Оригінал", cover, cover_result),
            ("LSB Replacement", replacement, replacement_result),
            ("LSB Matching", matching, matching_result),
        ]

        for name, image, result in experiment:
            print(
                f"{name:20} "
                f"{result['chi_square']:>12.2f} "
                f"{result['p_value']:>12.6f} "
                f"{result['suspected_lsb']!s:>14}"
            )

            results.append(
                {
                    "fill_percentage": percentage,
                    "method": name,
                    "chi_square": round(result["chi_square"], 2),
                    "p_value": result["p_value"],
                    "suspected_lsb": result["suspected_lsb"],
                    "mse": round(compute_mse(cover, image), 6),
                    "psnr": round(compute_psnr(cover, image), 2),
                }
            )

        # Зберігаємо зображення для порівняння
        Image.fromarray(replacement).save(f"replacement_{percentage}.bmp")
        Image.fromarray(matching).save(f"matching_{percentage}.bmp")

        if percentage == fill_percentage:
            print("\nАНАЛІЗ ПАР ЗНАЧЕНЬ LSB REPLACEMENT")

            pairs = analyze_pair_ratios(replacement)

            for pair in pairs:
                print(
                    f"Пара {pair['pair']}: "
                    f"{pair['even']} / {pair['odd']}, "
                    f"ratio = {pair['ratio']:.3f}"
                )

    # 6. Пошук мінімального відсотка виявлення
    detected = [
        result["fill_percentage"]
        for result in results
        if result["method"] == "LSB Replacement" and result["suspected_lsb"]
    ]

    print("\n" + "=" * 70)
    print("ПІДСУМОК")
    print("=" * 70)

    if detected:
        print(
            "Мінімальний перевірений відсоток заповнення, "
            f"за якого виявлено LSB Replacement: {min(detected)}%"
        )
    else:
        print("LSB Replacement не виявлено за перевірених відсотків заповнення.")

    # 7. Експорт таблиці для звіту
    with open(
        "steganalysis_results.csv",
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "fill_percentage",
                "method",
                "chi_square",
                "p_value",
                "suspected_lsb",
                "mse",
                "psnr",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    print("\nРезультати збережено у steganalysis_results.csv")
    print("Експерименти завершено успішно!")


if __name__ == "__main__":
    main()
