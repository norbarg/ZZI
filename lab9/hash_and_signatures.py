import hashlib
import json
import random

# ---------------------------------------------------------------------
# Завантаження індивідуального варіанта
# ---------------------------------------------------------------------


def load_variant(path: str = "variant_3.json") -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# ---------------------------------------------------------------------
# ЧАСТИНА 1. Лавинний ефект SHA-256
# ---------------------------------------------------------------------


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hamming_distance_bits(hex_a: str, hex_b: str) -> int:
    """
    Кількість бітів, що відрізняються між двома хеш-значеннями.
    """
    int_a = int(hex_a, 16)
    int_b = int(hex_b, 16)

    xor_result = int_a ^ int_b

    return bin(xor_result).count("1")


def demonstrate_avalanche_effect(message: bytes, bit_position: int) -> dict:

    original_hash = sha256_hex(message)

    mutated = bytearray(message)

    # Інвертуємо заданий біт першого байта
    mutated[0] ^= 1 << bit_position

    mutated_hash = sha256_hex(bytes(mutated))

    diff_bits = hamming_distance_bits(original_hash, mutated_hash)

    total_bits = 256

    percentage = (diff_bits / total_bits) * 100

    return {
        "original_message": message,
        "mutated_message": bytes(mutated),
        "original_hash": original_hash,
        "mutated_hash": mutated_hash,
        "differing_bits": diff_bits,
        "total_bits": total_bits,
        "percentage_changed": round(percentage, 2),
    }


# ---------------------------------------------------------------------
# ЧАСТИНА 2. Схема підпису Шнорра
# ---------------------------------------------------------------------


class SchnorrSignature:

    def __init__(self, p: int, q: int, g: int):
        self.p = p
        self.q = q
        self.g = g

    def generate_keypair(self) -> tuple[int, int]:
        """
        x — приватний ключ.
        y = g^x mod p — публічний ключ.
        """

        x = random.randrange(1, self.q)

        y = pow(self.g, x, self.p)

        return x, y

    def _hash_challenge(self, message: bytes, t: int) -> int:

        data = message + str(t).encode()

        digest = hashlib.sha256(data).hexdigest()

        return int(digest, 16) % self.q

    def sign(
        self, message: bytes, private_key: int, nonce_k: int = None
    ) -> tuple[int, int]:

        if nonce_k is None:
            r = random.randrange(1, self.q)
        else:
            r = nonce_k

        t = pow(self.g, r, self.p)

        c = self._hash_challenge(message, t)

        s = (r - c * private_key) % self.q

        return c, s

    def verify(
        self, message: bytes, signature: tuple[int, int], public_key: int
    ) -> bool:

        c, s = signature

        t_recovered = (pow(self.g, s, self.p) * pow(public_key, c, self.p)) % self.p

        c_recomputed = self._hash_challenge(message, t_recovered)

        return c == c_recomputed


# ---------------------------------------------------------------------
# ЧАСТИНА 3. Катастрофа Nonce
# ---------------------------------------------------------------------


def demonstrate_nonce_catastrophe(
    scheme: SchnorrSignature, private_key: int, message_1: bytes, message_2: bytes
) -> dict:

    # ПОМИЛКА:
    # той самий nonce використовується двічі
    shared_k = random.randrange(1, scheme.q)

    c1, s1 = scheme.sign(message_1, private_key, nonce_k=shared_k)

    c2, s2 = scheme.sign(message_2, private_key, nonce_k=shared_k)

    q = scheme.q

    denom = (c2 - c1) % q

    if denom == 0:
        raise ValueError("c1 == c2. Запустіть програму ще раз.")

    denom_inv = pow(denom, -1, q)

    recovered_x = ((s1 - s2) * denom_inv) % q

    return {
        "shared_nonce_k": shared_k,
        "signature_1": (c1, s1),
        "signature_2": (c2, s2),
        "recovered_private_key": recovered_x,
        "actual_private_key": private_key,
        "attack_successful": (recovered_x == private_key),
    }


# ---------------------------------------------------------------------
# Основна програма
# ---------------------------------------------------------------------


def main():

    variant = load_variant()

    print("=" * 70)
    print("ІНДИВІДУАЛЬНИЙ ВАРІАНТ")
    print("=" * 70)

    print(f"Варіант: " f"{variant['variant']}")

    print(f"Алгоритм підпису: " f"{variant['signature_algorithm']}")

    print(f"Домен: " f"{variant['certificate_domain']}")

    # -------------------------------------------------------------
    # Частина 1
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print("Частина 1. Лавинний ефект SHA-256")
    print("=" * 70)

    message = variant["avalanche_test_message"].encode()

    bit_position = variant["avalanche_bit_position"]

    result = demonstrate_avalanche_effect(message, bit_position)

    print(f"Оригінальне повідомлення: " f"{result['original_message']}")

    print(f"Позиція інвертованого біта: " f"{bit_position}")

    print(f"Хеш оригіналу:\n" f"{result['original_hash']}")

    print(f"\nХеш після інвертування одного біта:\n" f"{result['mutated_hash']}")

    print(
        f"\nКількість змінених бітів: "
        f"{result['differing_bits']} "
        f"з {result['total_bits']}"
    )

    print(f"Відсоток зміни: " f"{result['percentage_changed']}%")

    # -------------------------------------------------------------
    # Частина 2
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print("Частина 2. Схема підпису Шнорра")
    print("=" * 70)

    # Навчальні параметри з методички
    p = 467
    q = 233
    g = 4

    scheme = SchnorrSignature(p, q, g)

    private_key, public_key = scheme.generate_keypair()

    print(f"Параметри групи: " f"p={p}, q={q}, g={g}")

    print(f"Приватний ключ x = " f"{private_key}")

    print(f"Публічний ключ y = " f"{public_key}")

    schnorr_message = variant["avalanche_test_message"].encode()

    signature = scheme.sign(schnorr_message, private_key)

    print(f"\nПовідомлення: " f"{schnorr_message}")

    print(f"Підпис (c, s): " f"{signature}")

    is_valid = scheme.verify(schnorr_message, signature, public_key)

    print("Перевірка підпису: " + ("ВАЛІДНИЙ" if is_valid else "НЕВАЛІДНИЙ"))

    forged_message = b"Modified message"

    is_valid_forged = scheme.verify(forged_message, signature, public_key)

    print(
        "Перевірка підпису "
        "для зміненого повідомлення: "
        + ("ВАЛІДНИЙ" if is_valid_forged else "НЕВАЛІДНИЙ (правильно)")
    )

    # -------------------------------------------------------------
    # Частина 3
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print("Частина 3. Катастрофа Nonce")
    print("=" * 70)

    msg_a = variant["nonce_message_a"].encode()

    msg_b = variant["nonce_message_b"].encode()

    attack = demonstrate_nonce_catastrophe(scheme, private_key, msg_a, msg_b)

    print(f"Повідомлення A: " f"{msg_a}")

    print(f"Повідомлення B: " f"{msg_b}")

    print(f"\nСпільний nonce k = " f"{attack['shared_nonce_k']}")

    print(f"Підпис A: " f"{attack['signature_1']}")

    print(f"Підпис B: " f"{attack['signature_2']}")

    print(f"\nВідновлений приватний ключ: " f"{attack['recovered_private_key']}")

    print(f"Справжній приватний ключ: " f"{attack['actual_private_key']}")

    print(f"Атака успішна: " f"{attack['attack_successful']}")


if __name__ == "__main__":
    main()
