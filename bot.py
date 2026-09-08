import os
import threading
from flask import Flask
from twitchio.ext import commands
from google import genai
from google.genai import types

# === МИНИ-СЕРВЕР ДЛЯ RENDER WEB SERVICE ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# === ЛОГИКА GEMINI И TWITCH ===
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_INSTRUCTION = """Ты — интерактивный и дружелюбный чат-бот для Twitch-канала.
Отвечай зрителям трансляции исключительно на грамотном, естественном белорусском языке.
Адказы мусяць быць кароткімі (1-3 сказы, да 250 сімвалаў).
Трымай у памяці папярэднія паведамленні ад гледачоў.
"""

chat_session = gemini_client.chats.create(
    model="gemini-3.8-flash",
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.7,
        max_output_tokens=150,
    )
)

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=os.getenv("TWITCH_OAUTH_TOKEN"),
            prefix="!",
            initial_channels=[os.getenv("TWITCH_CHANNEL")]
        )

    async def event_ready(self):
        print(f'Бот запущен под именем | {self.nick}')

    async def event_message(self, message):
        if message.echo:
            return

        if message.content.startswith('!bot ') or self.nick.lower() in message.content.lower():
            user_prompt = f"[{message.author.name}]: {message.content.replace('!bot', '').strip()}"
            try:
                response = chat_session.send_message(user_prompt)
                await message.channel.send(response.text)
            except Exception as e:
                print(f"Ошибка Gemini API: {e}")

        await self.handle_commands(message)

if __name__ == "__main__":
    # Запуск Flask сервера в отдельном потоке
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Запуск Twitch бота
    bot = Bot()
    bot.run()
