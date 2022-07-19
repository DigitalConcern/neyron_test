import asyncpg


async def connect():
    conn = await asyncpg.connect(user='postgres', password='12345',
                                 database='postgres', host='127.0.0.1')

    return conn


async def make_migrations():
    connection = await connect()

    try:
        await connection.execute("CREATE TABLE photos_test (id uuid primary key, image_bin bytea);")
    except asyncpg.exceptions.DuplicateTableError:
        pass

    await connection.close()
