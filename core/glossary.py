"""
Logistika sohasiga oid atamalar va tez-tez ishlatiladigan iboralar lug'ati.
Bu lug'at tarjima sifatini oshirish uchun AI modeliga "kontekst" sifatida beriladi
(model bu so'zlarni umumiy tarjimondan ko'ra to'g'riroq tushunishi uchun).

Yangi atama qo'shish juda oson — pastdagi ro'yxatga bitta qator qo'shsangiz bo'ldi.
"""

# Atama: (inglizcha, izoh — model uchun qo'shimcha tushuntirish)
LOGISTICS_GLOSSARY = {
    "yuk": ("load / freight", "tashiladigan tovar"),
    "haydovchi": ("driver", ""),
    "dispetcher": ("dispatcher", "yuklarni haydovchilarga taqsimlovchi xodim"),
    "broker": ("broker", "yuk va haydovchi o'rtasida vositachi"),
    "tarif / narx": ("rate", "bir reys uchun to'lanadigan pul"),
    "kutish haqi": ("detention", "yuklash/tushirish joyida uzoq kutib qolish uchun to'lov"),
    "yuk tushirish haqi": ("lumper fee", "omborda ishchilar yukni tushirgani uchun to'lov"),
    "yopiq furgon": ("dry van", "oddiy yopiq yuk mashinasi"),
    "muzlatgichli furgon": ("reefer", "sovutgichli yuk mashinasi"),
    "tekis platforma": ("flatbed", "tomsiz, tekis platformali yuk mashinasi"),
    "olib ketish": ("pickup", "yukni yuklash joyi/vaqti"),
    "yetkazib berish": ("delivery", "yukni tushirish joyi/vaqti"),
    "yo'l xati": ("BOL / bill of lading", "yuk haqidagi rasmiy hujjat"),
    "tasdiqlash xati": ("rate confirmation", "narx va shartlarni tasdiqlovchi hujjat"),
    "elektron jurnal": ("ELD / electronic logging device", "haydovchi ish soatini yozib boruvchi qurilma"),
    "ish soati limiti": ("hours of service (HOS)", "haydovchi bir kunda necha soat hayday olishi mumkinligi qoidasi"),
    "vazn nazorati punkti": ("weigh station", "yo'lda mashina vaznini tekshiradigan joy"),
    "sug'urta": ("insurance", ""),
    "yetkazib berish muddati o'tib ketdi": ("late delivery", ""),
    "bo'sh mashina": ("empty truck / deadhead", "yuk olib ketayotgan bo'sh mashina"),
    "yo'lda muammo": ("breakdown", "mashina yo'lda buzilishi"),
}


def glossary_as_prompt_text():
    """Lug'atni AI modeliga tushunarli matn ko'rinishida qaytaradi."""
    lines = []
    for uz_term, (en_term, note) in LOGISTICS_GLOSSARY.items():
        line = f"- {uz_term} -> {en_term}"
        if note:
            line += f" ({note})"
        lines.append(line)
    return "\n".join(lines)
