import json
import re
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix


# Список легітимних брендів, під які найчастіше маскується фішинг
KNOWN_BRANDS = [
    "paypal",
    "google",
    "microsoft",
    "apple",
    "privatbank",
    "monobank",
]


# ---------------------------------------------------------------------
# 1. Вилучення ознак (Feature Extraction)
# ---------------------------------------------------------------------

def levenshtein(a: str, b: str) -> int:
    """Відстань Левенштейна — кількість правок для перетворення a в b."""
    if len(a) < len(b):
        return levenshtein(b, a)

    if len(b) == 0:
        return len(a)

    previous_row = range(len(b) + 1)

    for i, ca in enumerate(a):
        current_row = [i + 1]

        for j, cb in enumerate(b):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (ca != cb)

            current_row.append(
                min(insertions, deletions, substitutions)
            )

        previous_row = current_row

    return previous_row[-1]


def min_brand_distance(domain: str) -> int:
    """
    Мінімальна відстань Левенштейна від домену до відомих брендів.
    Низьке значення (1-2) при відмінному домені є ознакою тайпсквотингу.
    """
    return min(
        levenshtein(domain, brand)
        for brand in KNOWN_BRANDS
    )


def extract_features(url: str) -> dict:
    """Обчислює числові ознаки URL для класифікатора."""

    domain_match = re.search(r"://([^/]+)", url)
    domain = domain_match.group(1) if domain_match else url

    has_ip = bool(
        re.match(
            r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
            domain,
        )
    )

    subdomain_count = (
        domain.count(".") - 1
        if not has_ip
        else 0
    )

    brand_dist = min_brand_distance(domain.lower())
    suspicious_words = [
        "verify",
        "secure",
        "update",
        "account",
        "login",
    ]

    suspicious_words_in_domain = int(
        any(word in domain.lower() for word in suspicious_words)
    )

    digits_in_domain = sum(
        c.isdigit() for c in domain
    )

    return {
        "url_length": len(url),
        "has_ip_instead_of_domain": int(has_ip),
        "subdomain_count": max(subdomain_count, 0),
        "has_at_symbol": int("@" in url),
        "has_hyphen_in_domain": int("-" in domain),
        "brand_levenshtein_distance": brand_dist,
        "uses_https": int(url.startswith("https://")),
        "count_digits": sum(c.isdigit() for c in url),
        "suspicious_words_in_domain": suspicious_words_in_domain,
        "digits_in_domain": digits_in_domain,
    }


FEATURE_NAMES = [
    "url_length",
    "has_ip_instead_of_domain",
    "subdomain_count",
    "has_at_symbol",
    "has_hyphen_in_domain",
    "brand_levenshtein_distance",
    "uses_https",
    "count_digits",
    "suspicious_words_in_domain",
    "digits_in_domain",
]


# ---------------------------------------------------------------------
# 2. Завантаження розміченого датасету
# ---------------------------------------------------------------------

def load_dataset(
    path: str,
) -> tuple[np.ndarray, np.ndarray, list[str]]:

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    urls = [item["url"] for item in data]
    labels = np.array([item["label"] for item in data])

    feature_rows = [
        extract_features(u)
        for u in urls
    ]

    X = np.array(
        [
            [row[name] for name in FEATURE_NAMES]
            for row in feature_rows
        ]
    )

    return X, labels, urls


# ---------------------------------------------------------------------
# 3. Навчання та оцінка моделі
# ---------------------------------------------------------------------

def train_and_evaluate(
    X: np.ndarray,
    y: np.ndarray,
):
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=42,
        stratify=y,
    )

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print("=" * 60)
    print("Звіт про якість класифікації (тестова вибірка):")
    print("=" * 60)

    print(
        classification_report(
            y_test,
            y_pred,
            target_names=[
                "Легітимний",
                "Фішинг",
            ],
        )
    )

    print("Матриця плутанини (Confusion Matrix):")

    cm = confusion_matrix(y_test, y_pred)

    print(
        f"{'':20}"
        f"{'Прогноз: Легіт.':^18}"
        f"{'Прогноз: Фішинг':^18}"
    )

    print(
        f"{'Факт: Легітимний':20}"
        f"{cm[0][0]:^18}"
        f"{cm[0][1]:^18}"
    )

    print(
        f"{'Факт: Фішинг':20}"
        f"{cm[1][0]:^18}"
        f"{cm[1][1]:^18}"
    )

    print(
        "\nВага кожної ознаки в рішенні моделі "
        "(коефіцієнти логістичної регресії):"
    )

    for name, coef in sorted(
        zip(FEATURE_NAMES, model.coef_[0]),
        key=lambda x: -abs(x[1]),
    ):
        direction = (
            "→ ФІШИНГ"
            if coef > 0
            else "→ легітимний"
        )

        print(
            f"{name:30} "
            f"{coef:+.3f} "
            f"{direction}"
        )

    return model


# ---------------------------------------------------------------------
# 4. Класифікація нового URL
# ---------------------------------------------------------------------

def classify_url(
    model: LogisticRegression,
    url: str,
) -> None:

    features = extract_features(url)

    X_new = np.array(
        [
            [
                features[name]
                for name in FEATURE_NAMES
            ]
        ]
    )

    proba = model.predict_proba(X_new)[0]
    prediction = model.predict(X_new)[0]

    label = (
        "ФІШИНГ"
        if prediction == 1
        else "легітимний"
    )

    print(f"\nURL: {url}")

    print(
        f"Класифікація: {label} "
        f"(імовірність фішингу: {proba[1]:.1%})"
    )

    print(f"Ознаки: {features}")


# ---------------------------------------------------------------------
# 5. Точка входу
# ---------------------------------------------------------------------

def main():
    path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "dataset.json"
    )

    X, y, urls = load_dataset(path)

    print(
        f"Завантажено {len(urls)} прикладів "
        f"({sum(y)} фішингових, "
        f"{len(y) - sum(y)} легітимних)\n"
    )

    model = train_and_evaluate(X, y)

    # Демонстрація класифікації нових, раніше не бачених URL
    test_urls = [
        "https://www.privatbank.ua/login",
        "http://privatbank-secure-login.tk/verify?user=1",
        "http://192.168.45.12/paypal.signin.com/webapps/",
    ]

    print("\n" + "=" * 60)
    print("Класифікація нових прикладів:")
    print("=" * 60)

    for url in test_urls:
        classify_url(model, url)


if __name__ == "__main__":
    main()