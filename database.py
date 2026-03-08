import aiosqlite

DB_NAME = "gifts.db"

DEFAULT_GIFTS = [
    ("XJ MINI PERFUME", 20),
    ("XJ FOUNDATION", 20),
    ("XJ GLOSS LIPISTICK", 20),
    ("XJ MATTE LIPISTICK", 20),
    ("XJ MASCARA", 20),
]


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE,
            telegram_id INTEGER UNIQUE,
            user_id_number TEXT UNIQUE,
            fullname TEXT NOT NULL,
            phone TEXT NOT NULL,
            country TEXT NOT NULL,
            region TEXT NOT NULL,
            address TEXT NOT NULL,
            gift TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS gifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            remaining INTEGER NOT NULL DEFAULT 0
        )
        """)

        await db.commit()


async def seed_gifts():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM gifts")
        row = await cursor.fetchone()
        count = row[0] if row else 0

        if count == 0:
            for name, amount in DEFAULT_GIFTS:
                await db.execute(
                    "INSERT INTO gifts (name, remaining) VALUES (?, ?)",
                    (name, amount)
                )
            await db.commit()


async def user_exists_by_telegram(telegram_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT 1 FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        return row is not None


async def user_exists_by_id_number(user_id_number: str) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT 1 FROM users WHERE user_id_number = ?",
            (user_id_number,)
        )
        row = await cursor.fetchone()
        return row is not None


async def get_gifts():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT name, remaining FROM gifts ORDER BY id ASC"
        )
        rows = await cursor.fetchall()
        return rows


async def get_gift_remaining(name: str) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT remaining FROM gifts WHERE name = ?",
            (name,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def decrease_gift(name: str) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT remaining FROM gifts WHERE name = ?",
            (name,)
        )
        row = await cursor.fetchone()

        if not row:
            return False

        remaining = row[0]
        if remaining <= 0:
            return False

        await db.execute(
            "UPDATE gifts SET remaining = remaining - 1 WHERE name = ?",
            (name,)
        )
        await db.commit()
        return True


async def get_users_count() -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def generate_order_number() -> str:
    count = await get_users_count()
    next_number = count + 1
    return f"XJ-{next_number:04d}"


async def save_user(
    order_number: str,
    telegram_id: int,
    user_id_number: str,
    fullname: str,
    phone: str,
    country: str,
    region: str,
    address: str,
    gift: str
):
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
        """, (
            order_number,
            telegram_id,
            user_id_number,
            fullname,
            phone,
            country,
            region,
            address,
            gift
        ))
        await db.commit()


async def get_stats_text() -> str:
    gifts = await get_gifts()
    total_users = await get_users_count()
    remaining_places = max(0, 100 - total_users)

    lines = ["📊 Совғалар ҳолати\n"]
    for name, remaining in gifts:
        lines.append(f"🎁 {name} — {remaining} та қолди")

    lines.append("")
    lines.append(f"👥 Жами буюртма: {total_users}")
    lines.append(f"📦 Қолган жой: {remaining_places}")

    return "\n".join(lines)


async def get_order_by_number(order_number: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT
            order_number,
            telegram_id,
            user_id_number,
            fullname,
            phone,
            country,
            region,
            address,
            gift
        FROM users
        WHERE order_number = ?
        """, (order_number,))
        return await cursor.fetchone()


async def get_user_by_telegram_id(telegram_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT
            order_number,
            telegram_id,
            user_id_number,
            fullname,
            phone,
            country,
            region,
            address,
            gift
        FROM users
        WHERE telegram_id = ?
        """, (telegram_id,))
        return await cursor.fetchone()
