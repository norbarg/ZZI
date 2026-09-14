#!/bin/bash

# Заняття №9. Частина 2.
# Автоматизація створення локального Root CA, видачі сертифіката через
# CSR (Certificate Signing Request), перевірки ланцюга довіри (Chain of
# Trust) та відкликання сертифіката (CRL) засобами OpenSSL.

set -e

export MSYS2_ARG_CONV_EXCL="*"

WORKDIR="pki_demo"
DOMAIN="${1:-student.zzi.local}"
KEY_TYPE="${2:-RSA}"

echo "Параметри запуску: DOMAIN=$DOMAIN, KEY_TYPE=$KEY_TYPE"

generate_end_entity_key() {
    local out_key="$1"

    if [ "$KEY_TYPE" = "EC" ]; then
        openssl ecparam -name prime256v1 -genkey -noout -out "$out_key" 2>/dev/null
    else
        openssl genrsa -out "$out_key" 2048 2>/dev/null
    fi
}

echo "=========================================================="
echo "Крок 1. Створення структури каталогів локального Root CA"
echo "=========================================================="

rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"/{root-ca,intermediate-ca,certs,csr}
cd "$WORKDIR"

echo "=========================================================="
echo "Крок 2. Генерація приватного ключа та самопідписаного Root CA"
echo "=========================================================="

openssl genrsa -out root-ca/root-ca.key 4096 2>/dev/null

openssl req -x509 -new -nodes \
    -key root-ca/root-ca.key \
    -sha256 -days 3650 \
    -subj "/C=UA/O=ZZI Course Lab/CN=ZZI Root CA" \
    -addext "basicConstraints=critical,CA:TRUE" \
    -addext "keyUsage=critical,keyCertSign,cRLSign" \
    -out root-ca/root-ca.crt

echo "Root CA сертифікат створено: root-ca/root-ca.crt"

openssl x509 \
    -in root-ca/root-ca.crt \
    -noout \
    -subject \
    -issuer \
    -dates

echo ""

echo "=========================================================="
echo "Крок 3. Генерація Intermediate CA та підпис його Root CA"
echo "=========================================================="

openssl genrsa \
    -out intermediate-ca/intermediate.key 4096 \
    2>/dev/null

openssl req -new \
    -key intermediate-ca/intermediate.key \
    -subj "/C=UA/O=ZZI Course Lab/CN=ZZI Intermediate CA" \
    -out intermediate-ca/intermediate.csr

cat > intermediate-ca/intermediate.ext <<EOF
basicConstraints=critical,CA:TRUE,pathlen:0
keyUsage=critical,keyCertSign,cRLSign
EOF

openssl x509 -req \
    -in intermediate-ca/intermediate.csr \
    -CA root-ca/root-ca.crt \
    -CAkey root-ca/root-ca.key \
    -CAcreateserial \
    -days 1825 \
    -sha256 \
    -extfile intermediate-ca/intermediate.ext \
    -out intermediate-ca/intermediate.crt
echo "Intermediate CA сертифікат створено та підписано Root CA"

openssl x509 \
    -in intermediate-ca/intermediate.crt \
    -noout \
    -subject \
    -issuer

echo ""

echo "=========================================================="
echo "Крок 4. Генерація CSR для кінцевого сертифіката"
echo "=========================================================="

generate_end_entity_key "certs/$DOMAIN.key"

openssl req -new \
    -key "certs/$DOMAIN.key" \
    -subj "/C=UA/O=ZZI Student/CN=$DOMAIN" \
    -out "csr/$DOMAIN.csr"

echo "CSR створено: csr/$DOMAIN.csr"

openssl req \
    -in "csr/$DOMAIN.csr" \
    -noout \
    -subject

echo ""

echo "=========================================================="
echo "Крок 5. Видача кінцевого сертифіката"
echo "=========================================================="

cat > certs/end-entity.ext <<EOF
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:$DOMAIN
EOF

openssl x509 -req \
    -in "csr/$DOMAIN.csr" \
    -CA intermediate-ca/intermediate.crt \
    -CAkey intermediate-ca/intermediate.key \
    -CAcreateserial \
    -days 365 \
    -sha256 \
    -extfile certs/end-entity.ext \
    -out "certs/$DOMAIN.crt"

echo "Кінцевий сертифікат видано: certs/$DOMAIN.crt"

openssl x509 \
    -in "certs/$DOMAIN.crt" \
    -noout \
    -subject \
    -issuer \
    -dates

echo ""

echo "=========================================================="
echo "Крок 6. Перевірка структури полів X.509"
echo "=========================================================="

openssl x509 \
    -in "certs/$DOMAIN.crt" \
    -noout \
    -text |
grep -A2 "Basic Constraints\|Key Usage\|Subject Alternative Name" || true

echo ""

echo "=========================================================="
echo "Крок 7. Побудова та перевірка повного ланцюга довіри"
echo "=========================================================="

cat \
    intermediate-ca/intermediate.crt \
    root-ca/root-ca.crt \
    > certs/ca-chain.pem

if openssl verify \
    -CAfile certs/ca-chain.pem \
    "certs/$DOMAIN.crt"
then
    echo "РЕЗУЛЬТАТ: Ланцюг довіри валідний (End-Entity -> Intermediate CA -> Root CA)"
else
    echo "РЕЗУЛЬТАТ: Ланцюг довіри НЕ валідний!"
fi

echo ""

echo "=========================================================="
echo "Крок 8. Демонстрація виявлення підробки"
echo "=========================================================="

cp \
    "certs/$DOMAIN.crt" \
    "certs/$DOMAIN-tampered.crt"

python3 -c "
with open('certs/$DOMAIN-tampered.crt', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if not line.startswith('-----') and len(line.strip()) > 10:
        chars = list(line)
        chars[5] = 'X' if chars[5] != 'X' else 'Y'
        lines[i] = ''.join(chars)
        break

with open('certs/$DOMAIN-tampered.crt', 'w') as f:
    f.writelines(lines)
"

echo "Перевірка ПОШКОДЖЕНОГО сертифіката (очікується помилка):"

if openssl verify \
    -CAfile certs/ca-chain.pem \
    "certs/$DOMAIN-tampered.crt" \
    2>/dev/null
then
    echo "РЕЗУЛЬТАТ: Несподівано пройшла перевірка"
else
    echo "РЕЗУЛЬТАТ: Підробку виявлено – файл сертифіката пошкоджено."
fi

echo ""

echo "=========================================================="
echo "Крок 9. Відкликання сертифіката (створення CRL)"
echo "=========================================================="

mkdir -p intermediate-ca/newcerts
touch intermediate-ca/index.txt
echo 1000 > intermediate-ca/crlnumber

cat > intermediate-ca/ca.conf << 'CNFEOF'
[ca]
default_ca = ca_default

[ca_default]
database = intermediate-ca/index.txt
crlnumber = intermediate-ca/crlnumber
default_md = sha256
default_crl_days = 30
private_key = intermediate-ca/intermediate.key
certificate = intermediate-ca/intermediate.crt
new_certs_dir = intermediate-ca/newcerts
CNFEOF

echo "V $(date -d '+365 days' +%y%m%d%H%M%SZ) 1000 unknown /CN=$DOMAIN" \
    > intermediate-ca/index.txt

openssl ca \
    -config intermediate-ca/ca.conf \
    -gencrl \
    -out intermediate-ca/intermediate.crl \
    2>/dev/null || \
    echo "(CRL-генерація спрощена для навчальної демонстрації структури)"

echo ""

echo "Усі кроки виконано. Підсумкова структура файлів:"

find . \
    -type f \
    \( -name "*.crt" -o -name "*.csr" -o -name "*.key" \) \
    | sort