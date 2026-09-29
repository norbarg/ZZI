import subprocess


def compile_variant(source_modifications: str, output_name: str) -> None:
    with open("anti_debug.c", "r", encoding="utf-8") as f:
        code = f.read()

    start_marker = "for (int i = 0; i < 5000; i++) {"
    end_marker = "result += i;"

    start = code.find(start_marker)

    if start == -1:
        raise ValueError(
            "Не знайдено цикл 'for (int i = 0; i < 5000; i++)' в anti_debug.c"
        )

    end = code.find(end_marker, start)

    if end == -1:
        raise ValueError("Не знайдено рядок 'result += i;' в anti_debug.c")

    end = code.find("}", end)

    if end == -1:
        raise ValueError("Не знайдено кінець циклу в anti_debug.c")

    end += 1

    modified_code = code[:start] + source_modifications + code[end:]

    with open(f"{output_name}.c", "w", encoding="utf-8") as f:
        f.write(modified_code)

    subprocess.run(
        [
            "gcc",
            "-O0",
            "-o",
            output_name,
            f"{output_name}.c",
            "-w",
        ],
        check=True,
    )


def main():
    print("=" * 70)
    print("Порівняння: штатне виконання vs емуляція покрокового трасування")
    print("=" * 70)

    # Варіант А: штатне виконання
    normal_code = """for (int i = 0; i < 5000; i++) {
        result += i;
    }"""

    compile_variant(normal_code, "variant_normal")

    # Варіант Б: емуляція покрокового трасування
    traced_code = """for (int i = 0; i < 5000; i++) {
        result += i;

        volatile unsigned long long delay = 0;

        for (volatile long j = 0; j < 100000L; j++) {
            delay += j;
        }
    }"""

    compile_variant(traced_code, "variant_traced")

    print("\n--- Варіант А: штатне виконання (5 запусків) ---")

    for _ in range(5):
        result = subprocess.run(
            ["./variant_normal"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        for line in result.stdout.splitlines():
            if "різниця" in line or "[!]" in line or "[OK]" in line:
                print(f" {line}")

    print("\n--- Варіант Б: емуляція покрокового трасування (1 запуск) ---")

    result = subprocess.run(
        ["./variant_traced"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )

    for line in result.stdout.splitlines():
        print(f" {line}")

    print(
        f" Код завершення процесу: {result.returncode} "
        f"({'аварійно завершено через exit(1)' if result.returncode == 1 else 'штатно'})"
    )


if __name__ == "__main__":
    main()
