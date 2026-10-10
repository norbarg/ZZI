import json
import random
import sys

SUBNET_OPTIONS = [
    "192.168.10",
    "192.168.20",
    "10.0.5",
    "172.16.8",
]

OUTBOUND_POLICY_OPTIONS = [
    [("TCP", 80), ("TCP", 443)],
    [("TCP", 80), ("TCP", 443), ("UDP", 53)],
    [("TCP", 443), ("UDP", 53), ("TCP", 22)],
    [("TCP", 80), ("TCP", 443), ("UDP", 53), ("TCP", 21)],
]

LEGITIMATE_REQUESTS = [
    "GET /index.html HTTP/1.1",
    "GET /product?id={} HTTP/1.1",
    "GET /search?q=laptop HTTP/1.1",
    "GET /about.html HTTP/1.1",
    "POST /contact HTTP/1.1 name=John&email=john@example.com",
]

ATTACK_TEMPLATES = [
    (
        "sqli_tautology",
        "POST /login HTTP/1.1 username=admin' OR 1=1 -- &password=x",
    ),
    (
        "directory_traversal",
        "GET /files?path=../../../etc/passwd HTTP/1.1",
    ),
    (
        "scanner_ua",
        "GET / HTTP/1.1 User-Agent: sqlmap/1.6.12",
    ),
    (
        "sqli_union",
        "GET /profile?id=1 UNION SELECT username,password FROM users HTTP/1.1",
    ),
    (
        "xss_script",
        "POST /comment HTTP/1.1 text=<script>alert('xss')</script>",
    ),
]


def generate_variant(n: int) -> dict:
    if not (1 <= n <= 30):
        raise ValueError("Номер варіанта має бути в діапазоні від 1 до 30")

    rng = random.Random(n)

    subnet = SUBNET_OPTIONS[n % len(SUBNET_OPTIONS)]
    client_ip = f"{subnet}.{rng.randint(2, 254)}"
    outbound_policy = OUTBOUND_POLICY_OPTIONS[n % len(OUTBOUND_POLICY_OPTIONS)]

    num_legit = rng.randint(4, 6)
    num_attacks = rng.randint(2, 4)

    legit_requests = [
        rng.choice(LEGITIMATE_REQUESTS).format(rng.randint(1, 999))
        for _ in range(num_legit)
    ]

    chosen_attacks = rng.sample(
        ATTACK_TEMPLATES,
        k=min(num_attacks, len(ATTACK_TEMPLATES)),
    )

    attack_requests = [payload for _, payload in chosen_attacks]
    attack_types = [name for name, _ in chosen_attacks]

    traffic_stream = legit_requests + attack_requests
    rng.shuffle(traffic_stream)

    return {
        "variant": n,
        "internal_subnet": subnet,
        "client_ip": client_ip,
        "outbound_policy": [f"{proto}:{port}" for proto, port in outbound_policy],
        "traffic_stream": traffic_stream,
        "expected_attack_types": attack_types,
        "expected_num_alerts": len(attack_requests),
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
    print(
        f"Внутрішня підмережа: {variant['internal_subnet']}.0/24, "
        f"IP клієнта: {variant['client_ip']}"
    )
    print(f"Дозволена вихідна політика firewall: {variant['outbound_policy']}")
    print(f"Потік трафіку для IDS ({len(variant['traffic_stream'])} запитів):")

    for i, req in enumerate(variant["traffic_stream"]):
        print(f"  [{i}] {req}")

    print(f"Типи атак, які мають бути виявлені: {variant['expected_attack_types']}")
    print(f"Очікувана кількість тривог: {variant['expected_num_alerts']}")
    print(f"\nФайл створено: {out_path}")
    print("Використайте stateful_firewall.py та signature_ids.py з цими параметрами.")


if __name__ == "__main__":
    main()
