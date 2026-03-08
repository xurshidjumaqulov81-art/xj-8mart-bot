import aiosqlite
from config import DB_NAME


GIFT_NAMES = [
    "XJ MINI PERFUME",
    "XJ FOUNDATION",
    "XJ GLOSS LIPISTICK",
    "XJ MATTE LIPISTICK",
    "XJ MASCARA",
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
                remaining INTEGER NOT NULL DEFAULT 20
            )
        """)

        await db.commit()


async def seed_gifts():
    async with aiosqlite.connect(DB_NAME) as db:
        for gift_name in GIFT_NAMES:
            cursor = await db.execute(
                "SELECT id FROM gifts WHERE name = ?",
                (gift_name,)
            )
            row = await cursor.fetchone()

            if not row:
                await db.execute(
                    "INSERT INTO gifts (name, remaining) VALUES (?, ?)",
                    (gift_name, 20)
                )

        await db.commit()


async def user_exists_by_telegram(telegram_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        return row is not None


async def user_exists_by_id_number(user_id_number: str) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id FROM users WHERE user_id_number = ?",
            (user_id_number,)
        )
        row = await cursor.fetchone()
        return row is not None


async def get_gifts():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT name, remaining FROM gifts ORDER BY id ASC"
        )
        return await cursor.fetchall()


async def get_gift_remaining(gift_name: str) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT remaining FROM gifts WHERE name = ?",
            (gift_name,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def decrease_gift(gift_name: str) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT remaining FROM gifts WHERE name = ?",
            (gift_name,)
        )
        row = await cursor.fetchone()

        if not row:
            return False

        remaining = row[0]
        if remaining <= 0:
            return False

        await db.execute(
            "UPDATE gifts SET remaining = remaining - 1 WHERE name = ?",
            (gift_name,)
        )
        await db.commit()
        return True


async def get_total_users_count() -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_remaining_slots() -> int:
    total = await get_total_users_count()
    remaining = 100 - total
    return remaining if remaining > 0 else 0


async def generate_order_number() -> str:
    count = await get_total_users_count()
    next_number = count + 1
    return f"XJ-{next_number:04d}"


async def save_user(
    telegram_id: int,
    user_id_number: str,
    fullname: str,
    phone: str,
    country: str,
    region: str,
    address: str,
    gift: str
):
    order_number = await generate_order_number()

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

    return order_number


async def get_user_by_order_number(order_number: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT order_number, telegram_id, user_id_number, fullname,
                   phone, country, region, address, gift
            FROM users
            WHERE order_number = ?
        """, (order_number,))
        return await cursor.fetchone()


async def get_gifts_status_text() -> str:
    gifts = await get_gifts()
    total_users = await get_total_users_count()
    remaining_slots = await get_remaining_slots()

    lines = ["📊 Совғалар ҳолати", ""]

    for gift_name, remaining in gifts:
        lines.append(f"🎁 {gift_name} — {remaining} та қолди")

    lines.append("")
    lines.append(f"👥 Жами буюртмалар: {total_users} та")
    lines.append(f"📦 Қолган жой: {remaining_slots} та")

    return "\n".join(lines)
