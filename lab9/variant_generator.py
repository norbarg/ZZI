"""
Заняття №9. Генератор індивідуального варіанта.

Студент самостійно (без участі викладача) отримує свій варіант,
ввівши власний номер за списком групи (від 1 до 30). Генератор
детерміновано (seed = номер варіанта) визначає:
– унікальний фіктивний домен для сертифіката;
– алгоритм підпису (RSA-2048 vs ECDSA);
– індивідуальне повідомлення для перевірки лавинного ефекту;
– індивідуальну пару повідомлень для катастрофи Nonce.

Запуск:
    python3 variant_generator.py <номер_варіанта>
"""

import json
import random
import sys

SURNAMES_LATIN = [
    "shevchenko",
    "kovalenko",
    "bondarenko",
    "tkachenko",
    "kravchenko",
    "melnyk",
    "kravets",
    "polishchuk",
    "oliynyk",
    "shevchuk",
    "boyko",
    "moroz",
    "marchenko",
    "savchenko",
    "rudenko",
    "voloshyn",
    "hnatiuk",
    "kucher",
    "pavlenko",
    "sydorenko",
]

SIGNATURE_ALGORITHMS = [
    ("RSA-2048", "sha256WithRSAEncryption", "RSA"),
    ("ECDSA-P256", "ecdsa-with-SHA256", "EC"),
]

AVALANCHE_MESSAGES = [
    "Confirm transfer of 500 UAH",
    "Grant admin access to server",
    "Approve leave request for John",
    "Release payment to vendor XYZ",
    "Authorize password reset",
    "Delete user account permanently",
]

NONCE_MESSAGE_PAIRS = [
    ("Approve invoice 1001", "Approve invoice 1002"),
    ("Grant access level 1", "Revoke access level 1"),
    ("Ship order to warehouse A", "Ship order to warehouse B"),
    ("Sign contract version 1", "Sign contract version 2"),
    ("Authorize refund request", "Deny refund request"),
]


def generate_variant(n: int) -> dict:
    if not (1 <= n <= 30):
        raise ValueError("Номер варіанта має бути в діапазоні від 1 до 30")

    rng = random.Random(n)

    surname = SURNAMES_LATIN[n % len(SURNAMES_LATIN)]
    domain = f"{surname}.sec.local"

    sig_alg_name, sig_alg_oid, key_type = SIGNATURE_ALGORITHMS[
        n % len(SIGNATURE_ALGORITHMS)
    ]

    avalanche_message = AVALANCHE_MESSAGES[n % len(AVALANCHE_MESSAGES)]

    nonce_msg_a, nonce_msg_b = NONCE_MESSAGE_PAIRS[n % len(NONCE_MESSAGE_PAIRS)]

    # Індивідуальний позиція біта для інвертування в тесті лавинного ефекту
    bit_position_to_flip = rng.randint(0, 7)  # у межах першого байта

    return {
        "variant": n,
        "certificate_domain": domain,
        "signature_algorithm": sig_alg_name,
        "signature_algorithm_oid": sig_alg_oid,
        "key_type": key_type,
        "avalanche_test_message": avalanche_message,
        "avalanche_bit_position": bit_position_to_flip,
        "nonce_message_a": nonce_msg_a,
        "nonce_message_b": nonce_msg_b,
    }


def main():
    if len(sys.argv) != 2:
        print("Використання: python3 variant_generator.py <номер_варіанта: 1-30>")
        sys.exit(1)

    n = int(sys.argv[1])
    variant = generate_variant(n)

    out_path = f"variant_{n}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(variant, f, ensure_ascii=False, indent=2)

    print(f"Варіант №{n}")
    print(f"Фіктивний домен для сертифіката: " f"{variant['certificate_domain']}")
    print(
        f"Алгоритм підпису: {variant['signature_algorithm']} "
        f"({variant['key_type']})"
    )
    print(
        f"Повідомлення для тесту лавинного ефекту: "
        f"'{variant['avalanche_test_message']}'"
    )
    print(f"Позиція біта для інвертування: " f"{variant['avalanche_bit_position']}")
    print("Пара повідомлень для катастрофи Nonce:")
    print(f" A: '{variant['nonce_message_a']}'")
    print(f" B: '{variant['nonce_message_b']}'")

    print(f"\nФайл створено: {out_path}")
    print(
        "Використайте hash_and_signatures.py та pki_setup.sh "
        "(змінна DOMAIN) з цими параметрами."
    )


if __name__ == "__main__":
    main()
