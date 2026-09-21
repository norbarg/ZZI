import re
import subprocess

BUFFER_SIZE = 48
PAYLOAD_SIZES = [6, 48, 63, 160]

BINARIES = {
    "unprotected": {
        "path": r"builds\vuln_unprotected.exe",
        "protections": {
            "NX": False,
            "Canary": False,
            "ASLR": False,
        },
    },
    "nx_only": {
        "path": r"builds\vuln_nx_only.exe",
        "protections": {
            "NX": True,
            "Canary": False,
            "ASLR": False,
        },
    },
    "canary": {
        "path": r"builds\vuln_canary.exe",
        "protections": {
            "NX": True,
            "Canary": True,
            "ASLR": False,
        },
    },
    "full_protection": {
        "path": r"builds\vuln_full_protection.exe",
        "protections": {
            "NX": True,
            "Canary": True,
            "ASLR": True,
        },
    },
}


def run_binary(binary_path, payload_size, has_canary=False):
    payload = "A" * payload_size

    try:
        result = subprocess.run(
            [binary_path, payload],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )

        stdout = result.stdout
        stderr = result.stderr

        if result.returncode == 0:
            classification = "НОРМАЛЬНЕ"

        elif has_canary and payload_size >= BUFFER_SIZE:
            classification = "ЗАБЛОКОВАНО (Canary)"

        else:
            classification = "АВАРІЙНЕ"

        return {
            "payload_size": payload_size,
            "returncode": result.returncode,
            "classification": classification,
            "stdout": stdout,
            "stderr": stderr,
        }

    except subprocess.TimeoutExpired:
        return {
            "payload_size": payload_size,
            "returncode": None,
            "classification": "ТАЙМАУТ",
            "stdout": "",
            "stderr": "",
        }


def measure_aslr(binary_path, runs=5):
    addresses = []

    for _ in range(runs):
        result = subprocess.run(
            [binary_path, "test"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )

        match = re.search(
            r"print_secret_flag:\s*(?:0x)?([0-9a-fA-F]+)",
            result.stdout,
        )

        if match:
            addresses.append(match.group(1))

    unique_addresses = set(addresses)

    return {
        "addresses": addresses,
        "unique_count": len(unique_addresses),
        "aslr_active": len(unique_addresses) > 1,
    }


def protections_to_string(protections):
    result = []

    for name, enabled in protections.items():
        result.append(f"{name}{'+' if enabled else '-'}")

    return ", ".join(result)


def main():
    print("=" * 110)
    print("МАТРИЦЯ СТІЙКОСТІ")
    print("=" * 110)

    header = f"{'Варіант':22}{'Захисти':30}"

    for size in PAYLOAD_SIZES:
        header += f"{('payload=' + str(size)):22}"

    print(header)
    print("-" * 110)

    all_results = {}

    for name, config in BINARIES.items():
        protections = protections_to_string(config["protections"])

        row = f"{name:22}{protections:30}"

        all_results[name] = {}

        for size in PAYLOAD_SIZES:
            result = run_binary(
                config["path"],
                size,
                config["protections"]["Canary"],
            )

            all_results[name][size] = result

            row += f"{result['classification'][:21]:22}"

        print(row)

    print()
    print("=" * 110)
    print("ДЕТАЛЬНИЙ РЕЗУЛЬТАТ ДЛЯ НАЙБІЛЬШОГО PAYLOAD")
    print("=" * 110)

    largest_payload = max(PAYLOAD_SIZES)

    for name, config in BINARIES.items():
        result = all_results[name][largest_payload]

        print(f"\n{name}:")
        print(f"  Захисти: {config['protections']}")
        print(f"  Payload: {largest_payload}")
        print(f"  Результат: {result['classification']}")
        print(f"  Код завершення: {result['returncode']}")

    print()
    print("=" * 110)
    print("ПЕРЕВІРКА ASLR — 5 ЗАПУСКІВ")
    print("=" * 110)

    for name in ["unprotected", "full_protection"]:
        config = BINARIES[name]

        result = measure_aslr(config["path"], 5)

        print(f"\n{name}:")
        print(f"  ASLR у конфігурації: {config['protections']['ASLR']}")
        print(f"  Адреси: {result['addresses']}")
        print(
            f"  Унікальних адрес: {result['unique_count']} з {len(result['addresses'])}"
        )
        print(f"  ASLR активний: {result['aslr_active']}")


if __name__ == "__main__":
    main()
