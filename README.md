Запуск приложения:
     
     1) Настроить окружение в settings.toml:  app_settings.mode = "dev"
     2) Запуск контейнера docker: pg_db
     3) Применение миграции: poetry run alembic upgrade head
     4) Запуск приложения: poetry run uvicorn app.main:app --reload
     
Запуск автотестов:
     
     1) Настроить окружение в settings.toml:  app_settings.mode = "test"
     2) Запуск контейнера docker: pg_db_test
     3) Подготовить БД для автотестов, выполнить команды:
         * DROP SCHEMA public CASCADE;
         * CREATE SCHEMA public;
     4) Применение миграции: poetry run alembic upgrade head
     5) Запуск приложения: poetry run uvicorn app.main:app --reload
     6) Запуск автотестов: poetry run pytest .
     
