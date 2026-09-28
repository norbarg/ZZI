import builtins
import json
import os

import target_app

VARIANT_FILE = "variant_3.json"

with open(VARIANT_FILE, "r", encoding="utf-8") as f:
    VARIANT = json.load(f)


class FileAccessTracer:
    """
    Перехоплює виклики open() та зберігає
    шлях до файлу і режим доступу.
    """

    def __init__(self):
        self.access_log = []
        self._original_open = None

    def _traced_open(self, file, mode="r", *args, **kwargs):
        if isinstance(file, (str, bytes, os.PathLike)):
            abs_path = os.path.abspath(file)
        else:
            abs_path = str(file)

        self.access_log.append((abs_path, mode))

        return self._original_open(file, mode, *args, **kwargs)

    def __enter__(self):
        self._original_open = builtins.open
        builtins.open = self._traced_open

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        builtins.open = self._original_open


def get_unique_accesses(access_log):
    """
    Об'єднує всі режими доступу для кожного файлу.
    """

    result = {}

    for path, mode in access_log:
        if path not in result:
            result[path] = set()

        result[path].add(mode)

    return result


def mode_to_permissions(mode):
    """
    Перетворює Python-режим open()
    на умовні AppArmor-права.
    """

    permissions = set()

    if "r" in mode or "+" in mode:
        permissions.add("r")

    if "w" in mode or "x" in mode or "+" in mode:
        permissions.add("w")

    if "a" in mode:
        permissions.add("a")

    return "".join(sorted(permissions))


def generate_apparmor_profile(accesses):
    """
    Формує текст профілю на основі
    реально зафіксованих файлових операцій.
    """

    profile_lines = []

    profile_lines.append("# Generated profile for variant 3")

    profile_lines.append("profile log_aggregator {")

    profile_lines.append("")

    profile_lines.append("    # Explicitly denied capabilities")

    for capability in VARIANT["denied_capabilities"]:
        profile_lines.append(f"    deny capability {capability},")

    profile_lines.append("")

    profile_lines.append("    # File access rules")

    for path in sorted(accesses):
        all_permissions = set()

        for mode in accesses[path]:
            permissions = mode_to_permissions(mode)

            for permission in permissions:
                all_permissions.add(permission)

        permission_string = "".join(sorted(all_permissions))

        normalized_path = path.replace("\\", "/")

        profile_lines.append(f"    {normalized_path} {permission_string},")

    profile_lines.append("}")

    return "\n".join(profile_lines)


def check_access_against_profile(accesses, path, requested_mode):
    """
    Імітація режиму Enforce.

    Доступ дозволяється лише тоді,
    коли цей файл і необхідні права
    вже зустрічались під час трасування.
    """

    abs_path = os.path.abspath(path)

    if abs_path not in accesses:
        return False

    required_permissions = set(mode_to_permissions(requested_mode))

    allowed_permissions = set()

    for mode in accesses[abs_path]:
        permissions = mode_to_permissions(mode)

        for permission in permissions:
            allowed_permissions.add(permission)

    return required_permissions.issubset(allowed_permissions)


def run_legitimate_trace():
    with FileAccessTracer() as tracer:
        target_app.setup_environment()

        target_app.read_config()
        target_app.aggregate_logs()

        target_app.write_service_log("Profile generation test")

    return tracer.access_log


def main():
    print("=== Автоматична генерація профілю ===")

    access_log = run_legitimate_trace()

    print("\nЗафіксовані файлові операції:")

    for path, mode in access_log:
        print(f"{mode:>3} -> {path}")

    accesses = get_unique_accesses(access_log)

    profile = generate_apparmor_profile(accesses)

    profile_file = "log_aggregator.profile"

    with open(profile_file, "w", encoding="utf-8") as f:
        f.write(profile)

    print(f"\nПрофіль створено: {profile_file}")

    print("\n=== Згенерований профіль ===")
    print(profile)

    print("\n=== Перевірка режиму Enforce ===")

    legitimate_file = os.path.join(target_app.CONFIG_DIR, "aggregator.conf")

    legitimate_result = check_access_against_profile(accesses, legitimate_file, "r")

    print(
        f"\nЧитання {legitimate_file}: {'ALLOWED' if legitimate_result else 'DENIED'}"
    )

    attack_target = VARIANT["attack_target"]

    attack_result = check_access_against_profile(accesses, attack_target, "r")

    print(f"Читання {attack_target}: {'ALLOWED' if attack_result else 'DENIED'}")


if __name__ == "__main__":
    main()
