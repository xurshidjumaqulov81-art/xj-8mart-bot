from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


COUNTRIES = [
    "🇺🇿 Ўзбекистон",
    "🇰🇿 Қозоғистон",
    "🇰🇬 Қирғизистон",
    "🇹🇯 Тожикистон",
    "🇹🇲 Туркманистон",
]

UZBEKISTAN_REGIONS = [
    "Тошкент шаҳри",
    "Тошкент вилояти",
    "Андижон вилояти",
    "Бухоро вилояти",
    "Жиззах вилояти",
    "Қашқадарё вилояти",
    "Навоий вилояти",
    "Наманган вилояти",
    "Самарқанд вилояти",
    "Сирдарё вилояти",
    "Сурхондарё вилояти",
    "Фарғона вилояти",
    "Хоразм вилояти",
    "Қорақалпоғистон Республикаси",
]

KAZAKHSTAN_REGIONS = [
    "Олмота",
    "Астана",
    "Шимкент",
    "Қарағанда",
    "Атирау",
]

KYRGYZSTAN_REGIONS = [
    "Бишкек",
    "Ўш",
    "Жалолобод",
    "Қоракўл",
    "Норин",
]

TAJIKISTAN_REGIONS = [
    "Душанбе",
    "Хўжанд",
    "Бохтар",
    "Кўлоб",
    "Турсунзода",
]

TURKMENISTAN_REGIONS = [
    "Ашхобод",
    "Туркманобод",
    "Дашоғуз",
    "Марв",
    "Балканобод",
]


def start_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Рўйхатдан ўтиш")]
        ],
        resize_keyboard=True
    )


def phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📲 Рақамни юбориш", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def confirm_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Тасдиқлаш")],
            [KeyboardButton(text="✏️ Қайта тўлдириш")],
        ],
        resize_keyboard=True
    )


def countries_keyboard():
    rows = []
    for country in COUNTRIES:
        rows.append([KeyboardButton(text=country)])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        one_time_keyboard=True
    )


def regions_keyboard(country: str):
    mapping = {
        "🇺🇿 Ўзбекистон": UZBEKISTAN_REGIONS,
        "🇰🇿 Қозоғистон": KAZAKHSTAN_REGIONS,
        "🇰🇬 Қирғизистон": KYRGYZSTAN_REGIONS,
        "🇹🇯 Тожикистон": TAJIKISTAN_REGIONS,
        "🇹🇲 Туркманистон": TURKMENISTAN_REGIONS,
    }

    regions = mapping.get(country, [])
    rows = [[KeyboardButton(text=region)] for region in regions]

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_all_regions(country: str):
    mapping = {
        "🇺🇿 Ўзбекистон": UZBEKISTAN_REGIONS,
        "🇰🇿 Қозоғистон": KAZAKHSTAN_REGIONS,
        "🇰🇬 Қирғизистон": KYRGYZSTAN_REGIONS,
        "🇹🇯 Тожикистон": TAJIKISTAN_REGIONS,
        "🇹🇲 Туркманистон": TURKMENISTAN_REGIONS,
    }
    return mapping.get(country, [])


def get_all_countries():
    return COUNTRIES
