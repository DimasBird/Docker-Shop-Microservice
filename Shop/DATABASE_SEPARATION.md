# Database-per-service: отдельные экземпляры PostgreSQL

Проект использует два независимых контейнера PostgreSQL и два отдельных Docker volume:

- `postgres_shop` — база `shop_db`, роль приложения `shop_service`; таблицы товаров, корзины и заказов.
- `postgres_auth` — база `auth_db`, владелец `auth_service`; таблицы пользователей.

`api` и `consumer` подключаются к `postgres_shop` через `DATABASE_URL`. `auth` подключается к `postgres_auth` через `AUTH_DATABASE_URL`, передаваемый Compose как `DATABASE_URL`. URL авторизации использует hostname `postgres_auth`.

## Пароли

Существующие значения в `.env` сохранены. `auth_service` использует `SHOP_SERVICE_PASSWORD` как пароль PostgreSQL, потому что отдельной переменной пароля auth в исходной конфигурации не было. Это можно вынести в отдельную переменную позже, если разрешено менять конфигурацию секретов.

## Запуск

```powershell
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 postgres_shop postgres_auth api auth consumer
```

## Проверка независимости

```powershell
docker compose exec postgres_shop psql -U admin -d shop_db -c "SELECT current_database();"
docker compose exec postgres_auth psql -U auth_service -d auth_db -c "SELECT current_database();"
```

Это два разных экземпляра PostgreSQL, а не просто две базы в одном экземпляре. У них отдельные контейнеры и volumes. Это изолирует отказ одного экземпляра от другого на уровне контейнеров, но не гарантирует полную доступность: оба всё ещё зависят от Docker-хоста и его ресурсов.

Если у тебя уже есть старый volume `postgres_data`, он не удаляется автоматически. Новые сервисы используют новые volumes `shop_postgres_data` и `auth_postgres_data`. Старые данные остаются на месте, пока ты вручную не удалишь старый volume.
