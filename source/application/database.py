import logging
import os

import asyncpg

logging.basicConfig(level=logging.DEBUG, filename='myapp.log',
                    format="%(asctime)s: %(funcName)s: %(levelname)s: %(message)s")

logger = logging.getLogger(__name__)


# TODO: подключение к базе данных через переменные среды
async def connect():
    conn = await asyncpg.connect(user=os.environ.get('POSTGRES_USER'), password=os.environ.get('POSTGRES_PASSWORD'),
                                 database=os.environ.get('POSTGRES_NAME'), host='db')

    return conn


# Выполнение миграций для запуска из коробки
async def make_migrations():
    connection = await connect()

    # TODO: шифрование пароля
    await connection.execute("CREATE TABLE IF NOT EXISTS users (id uuid primary key, email text, password text);")
    await connection.execute("CREATE TABLE IF NOT EXISTS auth ("
                             "user_id uuid,"
                             "access_token uuid,"
                             "time_create timestamp without time zone,"
                             "foreign key (user_id) REFERENCES users(id)"
                             ");")
    await connection.execute("CREATE TABLE IF NOT EXISTS photos_test (id uuid primary key, image_bin bytea);")
    logger.info("Миграции выполнены")

    await connection.close()
