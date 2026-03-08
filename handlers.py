import re

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from config import ADMIN_ID
from database import (
    get_gifts,
    get_gift_remaining,
    user_exists_by_telegram,
    user_exists_by_id_number,
    decrease_gift,
    save_user,
    get_remaining_slots,
    get_user_by_order_number,
    get_gifts_status_text,
)
from keyboards import (
    start_keyboard,
    phone_keyboard,
    confirm_keyboard,
    countries_keyboard,
    regions_keyboard,
    get_all_regions,
    get_all_countries,
)


router = Router()


class GiftOrderForm(StatesGroup):
    user_id_number = State()
    fullname = State()
    gift = State()
    phone = State()
    country = State()
    region = State()
    address = State()
    confirm = State()
    admin_reply = State()


async def build_gifts_keyboard():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

    gifts = await get_gifts()
    rows = []

    for gift_name, remaining in gifts:
        rows.append([KeyboardButton(text=f"🎁 {gift_name} — {remaining} та қолди")])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        one_time_keyboard=True
    )


def extract_gift_name(button_text: str):
    cleaned = button_text.replace("🎁 ", "").strip()

    if " — " in cleaned:
        return cleaned.split(" — ")[0].strip()

    return cleaned.strip()


def is_valid_phone(phone: str) -> bool:
    pattern = r"^\+?\d{9,15}$"
    return bool(re.match(pattern, phone))


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    await state.clear()

    text = (
        "💐 Байрам акциясига хуш келибсиз!\n\n"
        "🎁 XJ компанияси томонидан 8-март муносабати билан\n"
        "100 нафар иштирокчига бепул совғалар тақдим этилади.\n\n"
        "🎁 Ҳар бир иштирокчи 5 та маҳсулотдан 1 тасини танлаб олиши мумкин.\n\n"
        "📌 Қоидалар:\n\n"
        "• Ҳар бир иштирокчи фақат 1 марта қатнашиши мумкин\n"
        "• Совғалар сони чекланган\n\n"
        "📝 Давом этиш учун қуйидаги тугмани босинг."
    )

    await message.answer(text, reply_markup=start_keyboard())


@router.message(Command("holat"))
async def admin_status(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    text = await get_gifts_status_text()
    await message.answer(text)


@router.message(Command("reply"))
async def admin_reply_command(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.strip().split(maxsplit=1)

    if len(parts) < 2:
        await message.answer("❌ Намуна: /reply XJ-0001")
        return

    order_number = parts[1].strip().upper()
    user = await get_user_by_order_number(order_number)

    if not user:
        await message.answer("❌ Бундай буюртма топилмади.")
        return

    await state.update_data(reply_order_number=order_number)
    await state.set_state(GiftOrderForm.admin_reply)

    await message.answer(f"✉️ {order_number} учун юбориладиган хабарни ёзинг.")


@router.message(GiftOrderForm.admin_reply)
async def send_admin_reply(message: Message, state: FSMContext, bot):
    if message.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()
    order_number = data.get("reply_order_number")

    user = await get_user_by_order_number(order_number)
    if not user:
        await message.answer("❌ Фойдаланувчи топилмади.")
        await state.clear()
        return

    _, telegram_id, _, fullname, _, _, _, _, _ = user

    text = (
        f"📩 Админдан хабар\n\n"
        f"🔢 Буюртма: {order_number}\n"
        f"👤 {fullname}\n\n"
        f"{message.text}"
    )

    try:
        await bot.send_message(chat_id=telegram_id, text=text)
        await message.answer("✅ Хабар юборилди.")
    except Exception:
        await message.answer("❌ Хабарни юбориб бўлмади.")

    await state.clear()


@router.message(F.text == "📝 Рўйхатдан ўтиш")
async def register_start(message: Message, state: FSMContext):
    telegram_exists = await user_exists_by_telegram(message.from_user.id)
    if telegram_exists:
        await message.answer(
            "⚠️ Сиз аввал рўйхатдан ўтгансиз.\n\n"
            "🎁 Бир иштирокчи фақат 1 марта совға олиши мумкин."
        )
        return

    remaining_slots = await get_remaining_slots()
    if remaining_slots <= 0:
        await message.answer("❌ Рўйхат ёпилган. Бепул совғалар тугаган.")
        return

    await state.clear()
    await state.set_state(GiftOrderForm.user_id_number)

    await message.answer(
        "🆔 Илтимос, ID рақамингизни киритинг.\n\n"
        "📌 Намуна: 0012345\n"
        "❗️ID рақам 7 хонали бўлиши керак.",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(GiftOrderForm.user_id_number)
async def get_id_number(message: Message, state: FSMContext):
    user_id_number = message.text.strip()

    if not user_id_number.isdigit() or len(user_id_number) != 7:
        await message.answer(
            "❌ ID рақам нотўғри киритилди.\n\n"
            "📌 Илтимос, 7 хонали рақам киритинг.\n"
            "Намуна: 0012345"
        )
        return

    exists = await user_exists_by_id_number(user_id_number)
    if exists:
        await message.answer(
            "⚠️ Ушбу ID рақам билан аввал рўйхатдан ўтилган.\n\n"
            "🎁 Бир иштирокчи фақат 1 марта совға олиши мумкин."
        )
        return

    await state.update_data(user_id_number=user_id_number)
    await state.set_state(GiftOrderForm.fullname)

    await message.answer(
        "👤 Илтимос, исм ва фамилиянгизни киритинг.\n\n"
        "📌 Намуна: Мадина Каримова"
    )


@router.message(GiftOrderForm.fullname)
async def get_fullname(message: Message, state: FSMContext):
    fullname = " ".join(message.text.strip().split())

    if len(fullname.split()) < 2:
        await message.answer(
            "❌ Илтимос, исм ва фамилияни тўлиқ киритинг.\n\n"
            "📌 Намуна: Мадина Каримова"
        )
        return

    await state.update_data(fullname=fullname)
    await state.set_state(GiftOrderForm.gift)

    gifts_kb = await build_gifts_keyboard()

    await message.answer(
        "🎁 Илтимос, қуйидаги маҳсулотлардан биттасини танланг.",
        reply_markup=gifts_kb
    )


@router.message(GiftOrderForm.gift)
async def get_gift(message: Message, state: FSMContext):
    gift_name = extract_gift_name(message.text)

    gifts = await get_gifts()
    gift_names = [name for name, _ in gifts]

    if gift_name not in gift_names:
        gifts_kb = await build_gifts_keyboard()
        await message.answer(
            "❌ Илтимос, совғани тугмалар орқали танланг.",
            reply_markup=gifts_kb
        )
        return

    remaining = await get_gift_remaining(gift_name)
    if remaining <= 0:
        gifts_kb = await build_gifts_keyboard()
        await message.answer(
            "❌ Бу совға тугаган.\n\n"
            "🎁 Илтимос, бошқа совғани танланг.",
            reply_markup=gifts_kb
        )
        return

    await state.update_data(gift=gift_name)
    await state.set_state(GiftOrderForm.phone)

    await message.answer(
        "📞 Илтимос, телефон рақамингизни юборинг.\n\n"
        "📌 Намуна: +998901234567",
        reply_markup=phone_keyboard()
    )


@router.message(GiftOrderForm.phone, F.contact)
async def get_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number

    if not phone.startswith("+"):
        phone = "+" + phone

    await state.update_data(phone=phone)
    await state.set_state(GiftOrderForm.country)

    await message.answer(
        "🌍 Совғани етказиб бериш учун давлатингизни танланг.",
        reply_markup=countries_keyboard()
    )


@router.message(GiftOrderForm.phone)
async def get_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()

    if not is_valid_phone(phone):
        await message.answer(
            "❌ Телефон рақам нотўғри киритилди.\n\n"
            "📌 Намуна: +998901234567",
            reply_markup=phone_keyboard()
        )
        return

    await state.update_data(phone=phone)
    await state.set_state(GiftOrderForm.country)

    await message.answer(
        "🌍 Совғани етказиб бериш учун давлатингизни танланг.",
        reply_markup=countries_keyboard()
    )


@router.message(GiftOrderForm.country)
async def get_country(message: Message, state: FSMContext):
    country = message.text.strip()

    if country not in get_all_countries():
        await message.answer(
            "❌ Илтимос, давлатни тугмалар орқали танланг.",
            reply_markup=countries_keyboard()
        )
        return

    await state.update_data(country=country)
    await state.set_state(GiftOrderForm.region)

    await message.answer(
        "📍 Совғани етказиб бериш учун вилоят ёки шаҳарни танланг.",
        reply_markup=regions_keyboard(country)
    )


@router.message(GiftOrderForm.region)
async def get_region(message: Message, state: FSMContext):
    data = await state.get_data()
    country = data.get("country")
    region = message.text.strip()

    if region not in get_all_regions(country):
        await message.answer(
            "❌ Илтимос, вилоят ёки шаҳарни тугмалар орқали танланг.",
            reply_markup=regions_keyboard(country)
        )
        return

    await state.update_data(region=region)
    await state.set_state(GiftOrderForm.address)

    await message.answer(
        "🏠 Совғани етказиб бериш учун аниқ уй манзилингизни ёзинг.\n\n"
        "📌 Намуна: Юнусобод тумани, 12-мавзе, 45-уй, 18-хонадон",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(GiftOrderForm.address)
async def get_address(message: Message, state: FSMContext):
    address = " ".join(message.text.strip().split())

    if len(address) < 8:
        await message.answer(
            "❌ Манзил тўлиқ киритилмади.\n\n"
            "🏠 Илтимос, уй манзилингизни аниқроқ ёзинг."
        )
        return

    await state.update_data(address=address)

    data = await state.get_data()

    text = (
        "✅ Илтимос, маълумотларни текширинг\n\n"
        f"🆔 ID рақам: {data['user_id_number']}\n"
        f"👤 Ф.И.Ш: {data['fullname']}\n"
        f"🎁 Совға: {data['gift']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"🌍 Давлат: {data['country']}\n"
        f"📍 Вилоят: {data['region']}\n"
        f"🏠 Манзил: {data['address']}"
    )

    await state.set_state(GiftOrderForm.confirm)
    await message.answer(text, reply_markup=confirm_keyboard())


@router.message(GiftOrderForm.confirm, F.text == "✏️ Қайта тўлдириш")
async def refill_form(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(GiftOrderForm.user_id_number)

    await message.answer(
        "🆔 Илтимос, ID рақамингизни қайта киритинг.\n\n"
        "📌 Намуна: 0012345",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(GiftOrderForm.confirm, F.text == "✅ Тасдиқлаш")
async def confirm_order(message: Message, state: FSMContext, bot):
    data = await state.get_data()

    telegram_exists = await user_exists_by_telegram(message.from_user.id)
    if telegram_exists:
        await message.answer(
            "⚠️ Сиз аввал рўйхатдан ўтгансиз."
        )
        await state.clear()
        return

    id_exists = await user_exists_by_id_number(data["user_id_number"])
    if id_exists:
        await message.answer(
            "⚠️ Ушбу ID рақам билан аввал рўйхатдан ўтилган."
        )
        await state.clear()
        return

    remaining_slots = await get_remaining_slots()
    if remaining_slots <= 0:
        await message.answer("❌ Рўйхат ёпилган. Бепул совғалар тугаган.")
        await state.clear()
        return

    success = await decrease_gift(data["gift"])
    if not success:
        gifts_kb = await build_gifts_keyboard()
        await state.set_state(GiftOrderForm.gift)
        await message.answer(
            "❌ Танланган совға ҳозир тугаб қолди.\n\n"
            "🎁 Илтимос, бошқа совғани танланг.",
            reply_markup=gifts_kb
        )
        return

    order_number = await save_user(
        telegram_id=message.from_user.id,
        user_id_number=data["user_id_number"],
        fullname=data["fullname"],
        phone=data["phone"],
        country=data["country"],
        region=data["region"],
        address=data["address"],
        gift=data["gift"]
    )

    user_text = (
        "🎉 Табриклаймиз!\n\n"
        "🎁 Сизнинг совғангиз муваффақиятли ажратилди.\n\n"
        f"📦 Буюртма рақамингиз: {order_number}\n\n"
        "🚚 Совға етказиб бериш учун тайёрланмоқда.\n"
        "📞 Зарур ҳолатда сиз билан боғланилади.\n\n"
        "🌷 Байрамингиз муборак бўлсин!"
    )

    admin_text = (
        "📥 Янги буюртма\n\n"
        f"🔢 Буюртма: {order_number}\n"
        f"🆔 ID: {data['user_id_number']}\n"
        f"👤 Ф.И.Ш: {data['fullname']}\n"
        f"🎁 Совға: {data['gift']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"🌍 Давлат: {data['country']}\n"
        f"📍 Вилоят: {data['region']}\n"
        f"🏠 Манзил: {data['address']}"
    )

    await message.answer(user_text, reply_markup=ReplyKeyboardRemove())

    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text)
    except Exception:
        pass

    await state.clear()


@router.message(GiftOrderForm.confirm)
async def confirm_only_buttons(message: Message):
    await message.answer("❌ Илтимос, тугмалардан бирини танланг.")
