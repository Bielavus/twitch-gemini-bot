import os
from twitchio.ext import commands
from google import genai
from google.genai import types

# Инициализация Gemini API
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Системные инструкции для модели
SYSTEM_INSTRUCTION = """Ты — чат-бот для белорусскоязычного Twitch-канала... (вставьте промпт выше)"""

# Настройка диалога с памятью (хранение контекста)
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

        # Вызываем бота командой !bot или упоминанием
        if message.content.startswith('!bot ') or self.nick.lower() in message.content.lower():
            user_prompt = f"[{message.author.name}]: {message.content.replace('!bot', '').strip()}"
            
            try:
                # Отправка сообщения в сессию чата (Gemini помнит контекст)
                response = chat_session.send_message(user_prompt)
                await message.channel.send(response.text)
            except Exception as e:
                print(f"Ошибка Gemini API: {e}")

        await self.handle_commands(message)

if __name__ == "__main__":
    bot = Bot()
    bot.run()