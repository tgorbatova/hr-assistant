# Использование Ansible для разворачивания контейнеров

1. Убедитесь, что в `vars.local.json` в объекте `"services"` описаны все переменные для сервиса:
   1. `name` - название сервиса;
   2. `location` - название базового ресурса сервиса (должен быть идентичен с base_url в fast_api);
   3. `port` - порт, который будет проброшен из докер-контейнера;
   4. `python_version` - python-версия;
   5. `db` - `bool`, используется ли БД в сервисе;
   6. `redis` - `false | str` - используется ли redis. 
2. Команда ``` make up``` запускает сборку `docker-compose.yml` и `nginx.conf` по шаблонам и поднимает контейнеры в фоновом режиме;
3. Команда ``` make down``` останавливает контейнеры.

**Обратите внимание, что в каждом сервисе должен существовать `.env.docker` файл с переменными окружения для подключения к контейнерам.**
Пример файла есть в `.env.example`.

## Я выполнил все команды, но контейнеры упали с ошибкой `Schema <schema_name> not found`?
Обычно такая ошибка появляется при первом запуске контейнеров и связана с тем, что схемы по умолчанию не создаются в новой БД. Их необходимо создать вручную и перезапустить контейнеры:
```
make down
make up
```