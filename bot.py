import os
import asyncio
import sys
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler, CallbackQueryHandler
from groq import Groq

# Parche para estabilidad en Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

user_data = {}

def ensure_user(uid, first_name):
    if uid not in user_data:
        user_data[uid] = {
            "name": first_name,
            "level": "Beginner",
            "scenario": "General Conversation",
            "history": [],
            "is_practicing": False  # Nueva bandera para controlar el idioma
        }

# --- MENÚS ---

async def show_main_menu(update: Update, uid):
    user_data[uid]["is_practicing"] = False  # Si está en el menú, no está practicando
    text = (f"🤖 *TeachBot* | Perfil: {user_data[uid]['name']}\n\n"
            f"📊 Nivel actual: {user_data[uid]['level']}\n"
            f"🌍 Escenario: {user_data[uid]['scenario']}\n\n"
            "¿Qué te gustaría hacer ahora?")
    
    botones = [
        [InlineKeyboardButton("⚙️ Cambiar Nivel", callback_data='config_level')],
        [InlineKeyboardButton("🌍 Cambiar Escenario", callback_data='config_scene')],
        [InlineKeyboardButton("📚 Vocabulario Útil", callback_data='get_vocab')],
        [InlineKeyboardButton("🚀 Comenzar a Practicar", callback_data='start_chat')]
    ]
    markup = InlineKeyboardMarkup(botones)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode='Markdown')

# (Funciones show_level_menu y show_scenario_menu se mantienen similares pero con textos en español)

async def show_level_menu(update: Update):
    botones = [
        [InlineKeyboardButton("A1 - Principiante", callback_data='set_lvl_Beginner')],
        [InlineKeyboardButton("B2 - Intermedio", callback_data='set_lvl_Intermediate')],
        [InlineKeyboardButton("C1 - Avanzado", callback_data='set_lvl_Advanced')],
        [InlineKeyboardButton("⬅️ Volver", callback_data='back_main')]
    ]
    await update.callback_query.edit_message_text("Selecciona tu nivel de inglés:", reply_markup=InlineKeyboardMarkup(botones))

async def show_scenario_menu(update: Update):
    botones = [
        [InlineKeyboardButton("☕ Cafetería", callback_data='set_sce_Coffee Shop')],
        [InlineKeyboardButton("💼 Entrevista de Trabajo", callback_data='set_sce_Job Interview')],
        [InlineKeyboardButton("✈️ Aeropuerto", callback_data='set_sce_Airport')],
        [InlineKeyboardButton("⬅️ Volver", callback_data='back_main')]
    ]
    await update.callback_query.edit_message_text("Elige un escenario para practicar:", reply_markup=InlineKeyboardMarkup(botones))

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user(uid, update.effective_user.first_name)
    await show_main_menu(update, uid)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    ensure_user(uid, query.from_user.first_name)
    await query.answer()

    if query.data == 'back_main':
        await show_main_menu(update, uid)
    elif query.data == 'config_level':
        await show_level_menu(update)
    elif query.data == 'config_scene':
        await show_scenario_menu(update)
    elif query.data == 'start_chat':
        user_data[uid]["is_practicing"] = True
        await query.edit_message_text(f"¡Excelente! Estamos en: *{user_data[uid]['scenario']}*. \n\nEscríbeme 'Hello' o cualquier frase en inglés para empezar. Si quieres parar, escribe /menu.", parse_mode='Markdown')
    
    elif query.data == 'get_vocab':
        scene = user_data[uid]['scenario']
        prompt = f"Dame 5 palabras esenciales para el escenario '{scene}' con traducción y un ejemplo. Formato claro en español."
        response = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.1-8b-instant")
        await query.message.reply_text(f"📚 *Vocabulario para {scene}:*\n\n{response.choices[0].message.content}\n\n¡Intenta usar una de estas palabras ahora!", parse_mode='Markdown')

    elif query.data.startswith('set_lvl_') or query.data.startswith('set_sce_'):
        if 'set_lvl_' in query.data:
            user_data[uid]['level'] = query.data.replace('set_lvl_', '')
        else:
            user_data[uid]['scenario'] = query.data.replace('set_sce_', '')
            user_data[uid]['history'] = []
        await show_main_menu(update, uid)

# --- CHAT ENGINE DUAL ---

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user(uid, update.effective_user.first_name)
    
    user_text = update.message.text
    data = user_data[uid]

    # Si el usuario NO ha pulsado "Empezar a practicar", el bot responde 100% en español.
    if not data["is_practicing"]:
        prompt = "Eres TeachBot, un tutor de inglés. El usuario aún no ha iniciado la práctica. Responde amablemente en ESPAÑOL indicando que debe usar el menú o presionar 'Comenzar a practicar' para hablar en inglés."
    else:
        # Modo PRÁCTICA (El que ya teníamos pero reforzado)
        prompt = f"""
        Eres 'TeachBot'. Usuario: {data['name']}, Nivel: {data['level']}, Escenario: {data['scenario']}.
        
        REGLAS:
        1. Responde en inglés como parte del escenario.
        2. Después, añade '📝 RECOMENDACIÓN:' en ESPAÑOL explicando errores o mejoras.
        3. Añade '🗣️ SIGUE LA CHARLA:' en INGLÉS y su traducción.
        """

    messages = [{"role": "system", "content": prompt}]
    for h in data['history'][-4:]:
        messages.append(h)
    messages.append({"role": "user", "content": user_text})

    try:
        response = client.chat.completions.create(messages=messages, model="llama-3.1-8b-instant")
        answer = response.choices[0].message.content
        if data["is_practicing"]:
            data['history'].append({"role": "user", "content": user_text})
            data['history'].append({"role": "assistant", "content": answer})
        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text("⚠️ Error de conexión.")

if __name__ == "__main__":
    app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start)) # Comando extra para volver al menú
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))
    print("🤖 TeachBot Pro (Bilingüe) funcionando...")
    app.run_polling()   