import asyncio
import asyncpg


async def connect():
    conn = await asyncpg.connect(user='postgres', password='12345',
                                 database='postgres', host='127.0.0.1')

    return conn
