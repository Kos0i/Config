#!/usr/bin/env python3
"""
Примеры конфигураций для разных предметных областей.
"""

# Пример 1: Конфигурация веб-сервера
WEB_SERVER_CONFIG = """
% Конфигурация веб-сервера Nginx-like
(define default_port 80)
(define ssl_port 443)
(define max_body_size 10485760)  % 10MB

server {
    server_name @"example.com"
    listen [ default_port, ssl_port ]

    ssl {
        enabled true
        certificate @"@"/etc/ssl/certs/example.crt""
        key @"@"/etc/ssl/private/example.key""
        protocols [ @"TLSv1.2", @"TLSv1.3" ]
    }

    location @"/" {
        root @"@"/var/www/html""
        index [ @"index.html", @"index.php" ]
        try_files @"$uri $uri/ /index.php?$args"
    }

    location @"/api/" {
        proxy_pass @"http://backend:3000"
        proxy_set_header Host @"$host"
        proxy_set_header X-Real-IP @"$remote_addr"
    }

    logging {
        access_log @"@"/var/log/nginx/access.log""
        error_log @"@"/var/log/nginx/error.log""
        log_level @"warn"
    }

    security {
        x_frame_options @"DENY"
        x_content_type_options @"nosniff"
        strict_transport_security @"max-age=31536000; includeSubDomains"
    }
}
"""

# Пример 2: Конфигурация CI/CD пайплайна
CI_CD_CONFIG = """
% Конфигурация пайплайна CI/CD
(define node_version @"16")
(define python_version @"3.9")

pipeline {
    name @"Deployment Pipeline"
    trigger [ @"push", @"pull_request" ]
    concurrency @"production-deploy"

    variables {
        DOCKER_REGISTRY @"registry.gitlab.com"
        PROJECT_PATH @"mygroup/myproject"
        DEPLOY_ENV @"staging"
    }

    stages [ @"test", @"build", @"deploy" ]

    test_stage {
        image .{@"node:" node_version +}.

        services [
            {
                name @"postgres"
                image @"postgres:13"
                variables {
                    POSTGRES_DB @"test_db"
                    POSTGRES_USER @"test_user"
                    POSTGRES_PASSWORD @"test_password"
                }
            }
            {
                name @"redis"
                image @"redis:6"
            }
        ]

        scripts [
            @"npm ci"
            @"npm run lint"
            @"npm test"
            @"npm run e2e"
        ]

        artifacts {
            paths [ @"coverage/", @"test-results.xml" ]
            expire_in @"30 days"
        }
    }

    build_stage {
        image @"docker:latest"

        scripts [
            @"docker build -t $DOCKER_REGISTRY/$PROJECT_PATH:$CI_COMMIT_SHA ."
            @"docker push $DOCKER_REGISTRY/$PROJECT_PATH:$CI_COMMIT_SHA"
        ]

        rules [
            {
                if @"$CI_COMMIT_BRANCH == 'main'"
                when @"on_success"
            }
        ]
    }

    deploy_stage {
        image @"alpine/helm:3.7"

        environment DEPLOY_ENV

        scripts [
            @"echo 'Deploying to $DEPLOY_ENV'"
            @"helm upgrade --install myapp ./charts/myapp --values ./envs/$DEPLOY_ENV.yaml"
        ]

        needs [ @"build_stage" ]
    }
}
"""

# Пример 3: Конфигурация IoT системы умного дома
SMART_HOME_CONFIG = """
% Конфигурация системы умного дома
(define home_id @"smart_home_001")
(define api_version @"v1")
(define max_devices 50)

smart_home {
    home_id home_id
    api_version api_version
    timezone @"Europe/Moscow"

    mqtt_broker {
        host @"192.168.1.100"
        port 1883
        username @"homeassistant"
        password @"secure_password_123"
        keepalive 60
        qos 1
    }

    devices [
        {
            id @"living_room_thermostat_01"
            type @"thermostat"
            name @"Living Room Thermostat"
            manufacturer @"Xiaomi"
            model @"LYWSD03MMC"

            config {
                temperature_range [ 10, 30 ]
                target_temperature 22
                hysteresis 0x01
                update_interval 300
                battery_saver true
            }

            automation {
                schedules [
                    {
                        days [ @"mon", @"tue", @"wed", @"thu", @"fri" ]
                        times [
                            { time @"06:00", temp 21 },
                            { time @"08:00", temp 19 },
                            { time @"17:00", temp 22 },
                            { time @"22:00", temp 18 }
                        ]
                    }
                    {
                        days [ @"sat", @"sun" ]
                        times [
                            { time @"08:00", temp 20 },
                            { time @"22:00", temp 19 }
                        ]
                    }
                ]

                away_mode {
                    enabled true
                    temp 16
                    activate_after 3600
                }
            }
        }

        {
            id @"front_door_camera_01"
            type @"camera"
            name @"Front Door Camera"
            manufacturer @"Reolink"
            model @"RLC-510A"

            config {
                resolution [ 2560, 1920 ]
                fps 15
                bitrate 4096
                night_vision true
                motion_detection {
                    enabled true
                    sensitivity 80
                    zones [ @"driveway", @"front_door" ]
                }
            }

            storage {
                type @"network"
                path @"@"/mnt/nas/cameras/front_door""
                retention_days 30
                motion_only true
            }
        }

        {
            id @"kitchen_lights_01"
            type @"light"
            name @"Kitchen Main Lights"
            manufacturer @"Philips"
            model @"Hue White"

            config {
                brightness_range [ 1, 100 ]
                color_temp_range [ 2200, 6500 ]
                transition_time 400

                groups [
                    { name @"morning", brightness 70, temp 4000 },
                    { name @"evening", brightness 50, temp 2700 },
                    { name @"night", brightness 10, temp 2200 }
                ]
            }

            automation {
                motion_trigger {
                    sensor @"kitchen_motion_01"
                    delay 300
                    activate_group @"morning"
                }

                time_based [
                    { time @"sunset - 30m", action @"turn_on", group @"evening" },
                    { time @"23:00", action @"turn_off" }
                ]
            }
        }
    ]

    scenes [
        {
            name @"Good Morning"
            trigger @"06:30"
            actions [
                { device @"living_room_thermostat_01", action @"set_temp", value 21 },
                { device @"kitchen_lights_01", action @"turn_on", group @"morning" }
            ]
        }

        {
            name @"Good Night"
            trigger @"22:30"
            actions [
                { device @"all_lights", action @"turn_off" },
                { device @"living_room_thermostat_01", action @"set_temp", value 18 },
                { device @"security_system", action @"arm", mode @"night" }
            ]
        }
    ]

    security {
        alarm {
            enabled true
            code @"1234"
            entry_delay 30
            exit_delay 60

            modes [
                {
                    name @"away"
                    devices [ @"all_doors", @"all_windows", @"all_motion" ]
                }
                {
                    name @"home"
                    devices [ @"all_doors", @"all_windows" ]
                }
                {
                    name @"night"
                    devices [ @"all_doors", @"all_windows", @"first_floor_motion" ]
                }
            ]
        }

        notifications {
            enabled true
            methods [ @"push", @"email", @"sms" ]

            events [
                { type @"alarm_triggered", priority @"high", methods [ @"push", @"sms" ] },
                { type @"door_open", priority @"medium", methods [ @"push" ] },
                { type @"motion_detected", priority @"low", methods [ @"push" ] }
            ]
        }
    }

    energy {
        monitoring true
        cost_per_kwh .{0x0F 100 /}.  % 0.15 в десятичном
        devices [
            { name @"HVAC", max_power 3500 },
            { name @"Water Heater", max_power 4500 },
            { name @"Lighting", max_power 1000 }
        ]

        optimization {
            peak_hours [ @"07:00-10:00", @"17:00-20:00" ]
            shift_load true
            solar_integration true
        }
    }
}
"""