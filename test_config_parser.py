#!/usr/bin/env python3
"""
Тесты для парсера конфигурационного языка.
"""

import unittest
import sys
from config_to_json import convert_to_json


class TestConfigParser(unittest.TestCase):
    """Тесты парсера конфигурационного языка."""

    def test_basic_parsing(self):
        """Тест базового парсинга."""
        config = """
        server_name @"Test Server"
        port 8080
        max_connections 100
        """

        result = convert_to_json(config)
        self.assertEqual(result["server_name"], "Test Server")
        self.assertEqual(result["port"], 8080)
        self.assertEqual(result["max_connections"], 100)

    def test_arrays(self):
        """Тест массивов."""
        config = """
        allowed_ips [ @"192.168.1.1", @"10.0.0.1", @"127.0.0.1" ]
        ports [ 80, 443, 8080 ]
        mixed_array [ 1, @"two", 0x03 ]
        """

        result = convert_to_json(config)
        self.assertEqual(result["allowed_ips"], ["192.168.1.1", "10.0.0.1", "127.0.0.1"])
        self.assertEqual(result["ports"], [80, 443, 8080])
        self.assertEqual(result["mixed_array"], [1, "two", 3])  # 0x03 = 3

    def test_comments(self):
        """Тест комментариев."""
        config = """
        % Это однострочный комментарий
        key1 @"value1"  % Комментарий после значения
        <#
        Это многострочный
        комментарий
        #>
        key2 @"value2"
        """

        result = convert_to_json(config)
        self.assertEqual(result["key1"], "value1")
        self.assertEqual(result["key2"], "value2")

    def test_define_constants(self):
        """Тест определения констант."""
        config = """
        (define max_users 100)
        (define app_name @"My Application")

        current_users 50
        application app_name
        """

        result = convert_to_json(config)
        self.assertEqual(result["current_users"], 50)
        self.assertEqual(result["application"], "My Application")

    def test_const_expressions(self):
        """Тест константных выражений."""
        config = """
        (define base_port 8000)

        port .{base_port 80 +}.
        offset_port .{base_port 100 +}.
        negative_value .{5 10 - abs}.
        hex_calc .{0x0A 0x10 +}.
        """

        result = convert_to_json(config)
        self.assertEqual(result["port"], 8080)  # 8000 + 80
        self.assertEqual(result["offset_port"], 8100)  # 8000 + 100
        self.assertEqual(result["negative_value"], 5)  # abs(5 - 10)
        self.assertEqual(result["hex_calc"], 26)  # 0x0A + 0x10 = 10 + 16

    def test_nested_const_expressions(self):
        """Тест вложенных константных выражений с define."""
        config = """
        (define base 10)
        (define offset .{base 5 +}.)

        result .{offset base *}.
        """

        result = convert_to_json(config)
        self.assertEqual(result["result"], 150)  # (10 + 5) * 10

    def test_hex_numbers(self):
        """Тест шестнадцатеричных чисел."""
        config = """
        hex_small 0x0A
        hex_big 0xFF
        hex_upper 0XABCD
        """

        result = convert_to_json(config)
        self.assertEqual(result["hex_small"], 10)
        self.assertEqual(result["hex_big"], 255)
        self.assertEqual(result["hex_upper"], 43981)

    def test_complex_array(self):
        """Тест сложного массива."""
        config = """
        (define increment 5)

        complex_array [
            .{increment 1 +}.
            @"string"
            [ 1, 2, 3 ]
            0x10
        ]
        """

        result = convert_to_json(config)
        self.assertEqual(result["complex_array"], [6, "string", [1, 2, 3], 16])

    def test_string_escaping(self):
        """Тест строк с кавычками."""
        config = """
        quoted @"He said \"Hello, World!\""
        double_quotes @"This is a \"test\" string"
        """

        result = convert_to_json(config)
        self.assertEqual(result["quoted"], 'He said "Hello, World!"')
        self.assertEqual(result["double_quotes"], 'This is a "test" string')

    def test_error_handling(self):
        """Тест обработки ошибок."""
        config = """
        key @"value"
        invalid [ 1, 2  % Пропущена запятая
        """

        with self.assertRaises(SyntaxError):
            convert_to_json(config)


class TestExamples(unittest.TestCase):
    """Тесты примеров из разных предметных областей."""

    def test_web_server_config(self):
        """Пример 1: Конфигурация веб-сервера."""
        config = """
        % Конфигурация веб-сервера
        (define default_port 8080)
        (define max_file_size 10485760)  % 10 MB в байтах

        server_config [
            {
                server_name @"MyWebServer"
                port .{default_port 80 +}.  % 8160
                ssl_enabled true
                max_upload_size max_file_size
                allowed_methods [ @"GET", @"POST", @"PUT" ]
                <#
                Настройки кэширования
                #>
                cache_ttl 3600
                static_paths [ @"/var/www", @"/home/user/public_html" ]
            }
        ]
        """

        result = convert_to_json(config)
        self.assertEqual(result["server_config"][0]["server_name"], "MyWebServer")
        self.assertEqual(result["server_config"][0]["port"], 8160)
        self.assertEqual(result["server_config"][0]["allowed_methods"], ["GET", "POST", "PUT"])

    def test_game_settings(self):
        """Пример 2: Настройки игры."""
        config = """
        % Настройки компьютерной игры
        (define base_speed 100)
        (define max_level 50)

        game_settings {
            title @"Epic Adventure"
            version @"1.5.2"

            % Настройки графики
            graphics {
                resolution [ 1920, 1080 ]
                texture_quality @"high"
                shadow_quality @"medium"
                anti_aliasing 4
            }

            % Настройки геймплея
            gameplay {
                difficulty @"normal"
                player_speed .{base_speed 20 *}.
                enemy_count .{max_level 2 *}.
                auto_save true
                checkpoints [ @"level1", @"level3", @"boss_fight" ]
            }

            % Сетевые настройки
            network {
                max_players 8
                timeout_ms 5000
                ports [ 7777, 7778, 7779 ]
            }
        }
        """

        result = convert_to_json(config)
        self.assertEqual(result["game_settings"]["title"], "Epic Adventure")
        self.assertEqual(result["game_settings"]["graphics"]["resolution"], [1920, 1080])
        self.assertEqual(result["game_settings"]["gameplay"]["player_speed"], 2000)  # 100 * 20
        self.assertEqual(result["game_settings"]["network"]["max_players"], 8)

    def test_iot_device_config(self):
        """Пример 3: Конфигурация IoT устройства."""
        config = """
        % Конфигурация умного термостата
        (define min_temp 10)
        (define max_temp 30)
        (define default_temp 22)

        device_config {
            device_id @"thermostat_living_room_001"
            device_type @"smart_thermostat"
            firmware_version @"2.1.4"

            % Настройки температуры
            temperature {
                current .{default_temp}.
                target default_temp
                min min_temp
                max max_temp
                hysteresis 0x01  % 1 градус
                unit @"celsius"
            }

            % Расписание
            schedule [
                {
                    time @"06:00"
                    temp 21
                    days [ @"mon", @"tue", @"wed", @"thu", @"fri" ]
                }
                {
                    time @"22:00"
                    temp 18
                    days [ @"mon", @"tue", @"wed", @"thu", @"fri", @"sat", @"sun" ]
                }
            ]

            % Сетевые настройки
            network {
                wifi_ssid @"HomeNetwork"
                wifi_password @"secure_password"
                mqtt_broker @"192.168.1.100"
                mqtt_port 1883
                update_interval 300  % 5 минут в секундах
            }

            % Мониторинг
            monitoring {
                enabled true
                metrics [ @"temperature", @"humidity", @"power_usage" ]
                report_interval 3600  % 1 час
                alert_thresholds {
                    high_temp .{max_temp 2 +}.
                    low_temp .{min_temp 2 -}.
                }
            }
        }
        """

        result = convert_to_json(config)
        self.assertEqual(result["device_config"]["device_id"], "thermostat_living_room_001")
        self.assertEqual(result["device_config"]["temperature"]["current"], 22)
        self.assertEqual(result["device_config"]["temperature"]["hysteresis"], 1)  # 0x01
        self.assertEqual(result["device_config"]["monitoring"]["alert_thresholds"]["high_temp"], 32)  # 30 + 2
        self.assertEqual(result["device_config"]["schedule"][0]["days"], ["mon", "tue", "wed", "thu", "fri"])


def run_tests():
    """Запуск всех тестов."""
    # Создаем тестовый набор
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestConfigParser))
    suite.addTests(loader.loadTestsFromTestCase(TestExamples))

    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == "__main__":
    # Если скрипт запущен с ключом --test, запускаем тесты
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Запуск тестов...")
        result = run_tests()
        sys.exit(0 if result.wasSuccessful() else 1)
    else:
        print("Для запуска тестов используйте: python test_config_parser.py --test")