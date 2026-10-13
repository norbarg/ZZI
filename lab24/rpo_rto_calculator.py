import json
from dataclasses import dataclass


@dataclass
class BIAScenario:
    name: str
    mtd_hours: float
    rto_hours: float
    wrt_hours: float
    rpo_hours: float

    @property
    def is_plan_viable(self):
        return self.rto_hours + self.wrt_hours <= self.mtd_hours

    @property
    def safety_margin_hours(self):
        return self.mtd_hours - (self.rto_hours + self.wrt_hours)


def recommend_site_strategy(rto_hours):
    if rto_hours <= 1:
        return "Hot Site (гарячий резерв)"
    elif rto_hours < 12:
        return "Посилений Warm Site із прискореним відновленням або Hot Site"
    elif rto_hours <= 48:
        return "Warm Site (теплий резерв)"
    else:
        return "Cold Site (холодний резерв)"


def compute_backup_window(
    total_data_gb,
    network_bandwidth_mbps,
    efficiency=0.8,
    index_time_seconds=60,
):
    total_bits = total_data_gb * 8 * 10**9
    bandwidth_bps = network_bandwidth_mbps * 10**6

    transfer_seconds = total_bits / (bandwidth_bps * efficiency)

    return transfer_seconds + index_time_seconds


def main():
    with open("variant_3.json", "r", encoding="utf-8") as file:
        variant = json.load(file)

    scenario = BIAScenario(
        name=variant["disaster_description"],
        mtd_hours=variant["mtd_hours"],
        rto_hours=variant["rto_hours"],
        wrt_hours=variant["wrt_hours"],
        rpo_hours=variant["rpo_hours"],
    )

    print("=" * 65)
    print("РОЗРАХУНОК МЕТРИК BIA — ВАРІАНТ №3")
    print("=" * 65)

    print(f"Сценарій: {scenario.name}")
    print(f"MTD: {scenario.mtd_hours} год")
    print(f"RTO: {scenario.rto_hours} год")
    print(f"WRT: {scenario.wrt_hours} год")
    print(f"RPO: {scenario.rpo_hours} год")

    total_recovery = round(scenario.rto_hours + scenario.wrt_hours, 2)

    print("\n" + "=" * 65)
    print("ПЕРЕВІРКА НЕРІВНОСТІ RTO + WRT <= MTD")
    print("=" * 65)

    print(
        f"{scenario.rto_hours} + {scenario.wrt_hours} "
        f"= {total_recovery} <= {scenario.mtd_hours}"
    )

    if scenario.is_plan_viable:
        print("[OK] Умова виконується")
    else:
        print("[ERROR] Умова порушена")

    print(f"Запас часу: {scenario.safety_margin_hours:.2f} год")

    print("\n" + "=" * 65)
    print("РЕКОМЕНДОВАНА СТРАТЕГІЯ")
    print("=" * 65)

    strategy = recommend_site_strategy(scenario.rto_hours)
    print(f"Резервний майданчик: {strategy}")

    print("\n" + "=" * 65)
    print("РОЗРАХУНОК BACKUP WINDOW")
    print("=" * 65)

    # Приклад розрахунку для 500 ГБ через канал 1 Гбіт/с.
    total_data_gb = 500
    bandwidth_mbps = 1000

    backup_window = compute_backup_window(
        total_data_gb,
        bandwidth_mbps,
        efficiency=0.8,
        index_time_seconds=60,
    )

    print(f"Обсяг даних: {total_data_gb} ГБ")
    print(f"Швидкість мережі: {bandwidth_mbps} Мбіт/с")
    print("Ефективність: 80%")
    print(f"Backup Window: {backup_window:.2f} секунд")
    print(f"Backup Window: {backup_window / 3600:.2f} год")

    print("\n[OK] Розрахунки BIA завершено!")


if __name__ == "__main__":
    main()
