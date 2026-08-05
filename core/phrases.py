"""
Tez-tez ishlatiladigan logistika iboralari. Bot foydalanuvchisi bu
gaplarni yozish yoki gapirish o'rniga tugma bosib, darhol tarjima
holda yubora oladi.

Har bir yozuv: (o'zbekcha ibora, qisqa tugma matni)
"""

READY_PHRASES = [
    ("Yukni qachon olib ketasiz?", "🚚 Qachon olib ketasiz?"),
    ("Yetkazib berish qachon bo'ladi?", "📦 Yetkazib berish qachon?"),
    ("Bu yuk uchun tarif qancha?", "💰 Tarif qancha?"),
    ("Kutish haqi qancha bo'ladi?", "⏱ Kutish haqi qancha?"),
    ("Hujjatlarni yuborishingiz mumkinmi?", "📄 Hujjat yuborasizmi?"),
    ("Haydovchi qayerda hozir?", "📍 Haydovchi qayerda?"),
    ("Yuk mashinasi bo'sh emas", "🚛 Mashina band"),
    ("Bir necha daqiqadan so'ng qayta qo'ng'iroq qilaman", "☎️ Keyinroq qo'ng'iroq qilaman"),
    ("Rate confirmation yuborilsinmi?", "✅ Tasdiqlash yuborilsinmi?"),
    ("Kechirasiz, tushunmadim, qayta ayting", "❓ Qayta ayting"),
]