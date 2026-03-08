import aiosqlite

DB_NAME = "gifts.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT,
            telegram_id INTEGER,
            user_id_number TEXT,
            fullname TEXT,
            phone TEXT,
            country TEXT,
            region TEXT,
            address TEXT,
            gift TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS gifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            remaining INTEGER
        )
        """)

        await db.commit()


async def seed_gifts():

    gifts = [
        ("XJ MINI PERFUME", 20),
        ("XJ FOUNDATION", 20),
        ("XJ GLOSS LIPSTICK", 20),
        ("XJ MATTE LIPSTICK", 20),
        ("XJ MASCARA", 20),
    ]

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("SELECT COUNT(*) FROM gifts")
        count = await cursor.fetchone()

        if count[0] == 0:

            for name, amount in gifts:

                await db.execute(
                    "INSERT INTO gifts (name, remaining) VALUES (?, ?)",
                    (name, amount)
                )

        await db.commit()


async def get_gifts():

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("SELECT name, remaining FROM gifts")

        return await cursor.fetchall()


async def decrease_gift(name):

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute(
            "UPDATE gifts SET remaining = remaining - 1 WHERE name=?",
            (name,)
        )

        await db.commit()


async def save_user(data):

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        INSERT INTO users (
            order_number,
            telegram_id,
            user_id_number,
            fullname,
            phone,
            country,
            region,
            address,
            gift
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)

        await db.commit()


async def user_exists(telegram_id):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            "SELECT id FROM users WHERE telegram_id=?",
            (telegram_id,)
        )

        return await cursor.fetchone()


async def id_exists(user_id):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            "SELECT id FROM users WHERE user_id_number=?",
            (user_id,)
        )

        return await cursor.fetchone()
