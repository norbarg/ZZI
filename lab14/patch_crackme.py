import shutil

binary_path = "crackme.exe"
patched_path = "crackme_patched.exe"

# Всегда создаём свежую копию оригинального файла
shutil.copy(binary_path, patched_path)

with open(patched_path, "rb") as f:
    data = bytearray(f.read())

# Фрагмент именно нашей функции check_license:
#
# call strcmp
# test eax,eax
# jne ...
# mov eax,1
#
signature = bytes(
    [0xE8, 0x4B, 0x16, 0x00, 0x00, 0x85, 0xC0, 0x75, 0x07, 0xB8, 0x01, 0x00, 0x00, 0x00]
)

offset = data.find(signature)

if offset == -1:
    raise ValueError("Нужная сигнатура check_license не найдена")

# В сигнатуре JNE (0x75) находится через 7 байт от начала
opcode_offset = offset + 7

print(f"Сигнатура check_license найдена: 0x{offset:X}")
print(f"Опкод JNE находится по смещению: 0x{opcode_offset:X}")
print(f"До патча: 0x{data[opcode_offset]:02X}")

if data[opcode_offset] != 0x75:
    raise ValueError("Ожидался опкод JNE = 0x75")

# JNE -> JE
data[opcode_offset] = 0x74

with open(patched_path, "wb") as f:
    f.write(data)

print(f"После патча: 0x{data[opcode_offset]:02X}")
print(f"Создан файл: {patched_path}")
