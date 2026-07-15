import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
import aiohttp
from google import genai  # Yangi rasmiy Google GenAI paketi

# ⚠️ API Kalitlaringizni joylashtiring:
DEEPGRAM_API_KEY = "DEEPGRAM_API_KEY"
GEMINI_API_KEY = "GEMINI_API_KEY"


class AudioStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("🔴 MVP: Brauzer ulandi!")

        # Yangi mijozni va eng so'nggi barqaror modelni ishga tushiramiz
        self.ai_client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = "gemini-1.5-flash"

        # Deepgram ulanishi (Inglizcha model)
        deepgram_url = "wss://api.deepgram.com/v1/listen?model=nova-2&language=en&smart_format=true"
        headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}

        self.session = aiohttp.ClientSession()
        try:
            self.dg_socket = await self.session.ws_connect(deepgram_url, headers=headers)
            print("⚡ MVP: Deepgram STT aloqa liniyasi tayyor!")
            self.listen_task = asyncio.create_task(self.receive_from_deepgram())
        except Exception as e:
            print(f"❌ Deepgramga ulanishda xato: {e}")
            await self.session.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'listen_task'):
            self.listen_task.cancel()
        if hasattr(self, 'dg_socket'):
            await self.dg_socket.close()
        if hasattr(self, 'session'):
            await self.session.close()
        print("❌ MVP: Audio ulanish yopildi.")

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data and hasattr(self, 'dg_socket'):
            await self.dg_socket.send_bytes(bytes_data)

    async def receive_from_deepgram(self):
        try:
            async for msg in self.dg_socket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    sentence = data.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")

                    if sentence:
                        print(f"🎙 Eshitildi: {sentence}")
                        # Matnni tahlil qilish uchun Gemini'ga yuboramiz
                        asyncio.create_task(self.analyze_with_gemini(sentence))

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"❌ Deepgram xatosi: {e}")

    async def analyze_with_gemini(self, text):
        """Matndan logistika ma'lumotlarini bepul suzib oluvchi AI funksiya"""
        prompt = (
            f"Siz AQSh logistika (trucking) tizimi uchun yordamchisiz. Quyidagi dispetcherning gapidan "
            f"logistika ma'lumotlarini aniqlang va faqat qat'iy va toza JSON formatida javob bering. "
            f"Hech qanday markdown (```json kabi yozuvlar) qo'shmang, faqat toza tekst ko'rinishida JSON chiqaring.\n\n"
            f"Gap: '{text}'\n\n"
            f"Format:\n"
            f"{{\n"
            f"  \"origin\": \"Yuk ortiladigan shahar/shtat\",\n"
            f"  \"destination\": \"Yuk tushadigan shahar/shtat\",\n"
            f"  \"payout\": \"Taklif qilingan narx ($)\",\n"
            f"  \"broker\": \"Broker yoki kompaniya nomi\",\n"
            f"  \"key_details\": \"Boshqa muhim detallar\"\n"
            f"}}\n"
            f"Agar biror ma'lumot topilmasa, qiymatiga \"Nomalum\" deb yozing."
        )

        try:
            # Yangi asinxron model chaqiruvi
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.ai_client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
            )

            ai_analysis = response.text.strip()
            print(f"🤖 Gemini AI Tahlili:\n{ai_analysis}")

            # Tahlil natijasini brauzerga otamiz
            await self.send(text_data=json.dumps({
                "type": "ai_analysis",
                "text": text,
                "analysis": ai_analysis
            }))

        except Exception as e:
            print(f"❌ Gemini API xatosi: {e}")