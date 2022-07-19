import logging
import asyncpg

logging.basicConfig(level=logging.DEBUG, filename='myapp.log',
                    format="%(asctime)s: %(funcName)s: %(levelname)s: %(message)s")

logger = logging.getLogger(__name__)


# TODO: подключение к базе данных через переменные среды
async def connect():
    conn = await asyncpg.connect(user='postgres', password='12345',
                                 database='postgres', host='127.0.0.1')

    return conn


# Выполнение миграций для запуска из коробки
async def make_migrations():
    connection = await connect()

    try:
        # TODO: шифрование пароля
        await connection.execute("CREATE TABLE auth_users (id uuid primary key, email text, password text);")
        await connection.execute("CREATE TABLE photos_test (id uuid primary key, image_bin bytea);")
        logger.info("Миграции выполнены")
    except asyncpg.exceptions.DuplicateTableError:
        pass

    await connection.close()
