import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from groq import Groq
import asyncio
import sys

# Parche para Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()
GROQ_TOKEN = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

client = Groq(api_key=GROQ_TOKEN)

async def chat_tutor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    try:
        # Aquí eliminamos la 'h' que causaba el SyntaxError
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """Eres un tutor de idiomas experto y cercano. 
                    Tu tarea es:
                    1. Si el usuario comete un error gramatical, corrígelo brevemente entre paréntesis.
                    2. Responde siempre en el idioma que el usuario te hable para mantener la práctica.
                    3. Haz una pregunta abierta al final para que la conversación no muera."""
                },
                {"role": "user", "content": user_message}
            ],
            model="llama-3.1-8b-instant",
        )

        respuesta_ia = chat_completion.choices[0].message.content
        await update.message.reply_text(respuesta_ia)
        
    except Exception as e:
        print(f"Error detectado: {e}")
        await update.message.reply_text("Lo siento, tuve un pequeño corto circuito. ¿Puedes repetir eso?")

if __name__ == "__main__":
    print("🤖 Bot encendido y listo para enseñar...")
    # Verificación de seguridad
    if not TELEGRAM_TOKEN:
        print("❌ Error: No se encontró el TELEGRAM_TOKEN en el archivo .env")
    else:
        print(f"✅ Token detectado: {TELEGRAM_TOKEN[:5]}...")
        
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_tutor))
        app.run_polling()