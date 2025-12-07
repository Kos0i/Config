#!/bin/bash
# Скрипт запуска примеров

echo "=== Тест 1: Базовая конфигурация ==="
echo 'server_name @"Test" port 8080' | python3 config_to_json.py -o test1.json
cat test1.json
echo

echo "=== Тест 2: Конфигурация с массивами ==="
cat > test2.config << 'EOF'
allowed_ips [ @"192.168.1.1", @"10.0.0.1" ]
ports [ 80, 443, 8080 ]
EOF
python3 config_to_json.py -o test2.json < test2.config
cat test2.json
echo

echo "=== Тест 3: Конфигурация с веб-сервером ==="
cat > input.config << 'EOF'
% Пример конфигурации веб-сервера
(define default_port 8080)

server_name @"MyServer"
port .{default_port 80 +}.
max_connections 100
allowed_ips [ @"192.168.1.1", @"127.0.0.1" ]
EOF

python3 config_to_json.py -o webserver.json < webserver.config