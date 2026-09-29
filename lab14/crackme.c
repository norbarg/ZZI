#include <stdio.h>
#include <string.h>

int check_license(const char *user_input) {
    if (strcmp(user_input, "ITNV-WCA4-JI9Q") == 0) {
        return 1;
    } else {
        return 0;
    }
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <license_key>\n", argv[0]);
        return 1;
    }

    printf("Checking key: %s\n", argv[1]);

    if (check_license(argv[1])) {
        printf("[OK] License valid. Access granted.\n");
        return 0;
    } else {
        printf("[FAIL] Invalid key. Access denied.\n");
        return 1;
    }
}