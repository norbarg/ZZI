/*
 * Заняття №14. Частина 2: Anti-debugging через RDTSC.
 *
 * Реалізація таймінгової перевірки для виявлення аномальної
 * затримки виконання критичної ділянки коду.
 */

#include <stdio.h>
#include <stdlib.h>
#include <x86intrin.h>

#define ANOMALY_THRESHOLD 0x3FFFFF

void secure_function(void) {
    // Зчитуємо кількість тактів процесора ДО виконання коду
    unsigned long long t1 = __rdtsc();

    // Критична ділянка коду
    int result = 0;

    for (int i = 0; i < 5000; i++) {
        result += i;

        volatile unsigned long long delay = 0;

        for (volatile long j = 0; j < 100000L; j++) {
            delay += j;
        }
    }

    // Зчитуємо кількість тактів процесора ПІСЛЯ виконання коду
    unsigned long long t2 = __rdtsc();

    unsigned long long delta = t2 - t1;

    printf("Виміряна різниця тактів процесора: %llu\n", delta);
    printf("Поріг аномалії: %d\n", ANOMALY_THRESHOLD);

    if (delta > ANOMALY_THRESHOLD) {
        printf("[!] Збій безпеки: Виявлено відлагоджувач "
               "(аномальна затримка)!\n");
        exit(1);
    } else {
        printf("[OK] Нормальне виконання "
               "(у межах штатного часу).\n");
    }
}

int main(void) {
    secure_function();
    return 0;
}