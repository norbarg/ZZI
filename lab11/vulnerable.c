#include <stdio.h>
#include <string.h>

void print_secret_flag(void) {
    printf("[!] СЕКРЕТНА ФУНКЦІЯ ВИКЛИКАНА: SECRET_DATA_LEAKED_92E799E7\n");
}

void vulnerable_function(const char *input) {
    char buffer[48];

    printf("Адреса буфера: %p\n", (void *)buffer);
    printf("Адреса функції print_secret_flag: %p\n", (void *)print_secret_flag);

    strcpy(buffer, input);

    printf("Скопійовано у буфер: %s\n", buffer);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Використання: %s <рядок_для_копіювання>\n", argv[0]);
        return 1;
    }

    printf("=== Демонстрація вразливості переповнення буфера ===\n");
    printf(
        "Довжина вхідного рядка: %zu байт (буфер розрахований на 48 байт)\n",
        strlen(argv[1])
    );

    vulnerable_function(argv[1]);

    printf("Функція завершилась нормально.\n");

    return 0;
}