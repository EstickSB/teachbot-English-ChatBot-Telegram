import os
import asyncio
import sys
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler, CallbackQueryHandler
from groq import Groq

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
            "history": []
        }


async def show_main_menu(update: Update, uid):
    text = (f"🤖 *TeachBot* | Profile: {user_data[uid]['name']}\n\n"
            f"📊 Level: {user_data[uid]['level']}\n"
            f"🌍 Scenario: {user_data[uid]['scenario']}\n\n"
            "What would you like to do?")
    
    botones = [
        [InlineKeyboardButton("⚙️ Change Level", callback_data='config_level')],
        [InlineKeyboardButton("🌍 Change Scenario", callback_data='config_scene')],
        [InlineKeyboardButton("📚 Vocabulary Booster", callback_data='get_vocab')],
        [InlineKeyboardButton("🚀 Start Chatting", callback_data='start_chat')]
    ]
    markup = InlineKeyboardMarkup(botones)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode='Markdown')

async def show_level_menu(update: Update):
    botones = [
        [InlineKeyboardButton("A1 - Beginner", callback_data='set_lvl_Beginner')],
        [InlineKeyboardButton("B2 - Intermediate", callback_data='set_lvl_Intermediate')],
        [InlineKeyboardButton("C1 - Advanced", callback_data='set_lvl_Advanced')],
        [InlineKeyboardButton("⬅️ Back", callback_data='back_main')]
    ]
    await update.callback_query.edit_message_text("Select your English level:", reply_markup=InlineKeyboardMarkup(botones))

async def show_scenario_menu(update: Update):
    botones = [
        [InlineKeyboardButton("☕ Coffee Shop", callback_data='set_sce_Coffee Shop')],
        [InlineKeyboardButton("💼 Job Interview", callback_data='set_sce_Job Interview')],
        [InlineKeyboardButton("✈️ Airport", callback_data='set_sce_Airport')],
        [InlineKeyboardButton("⬅️ Back", callback_data='back_main')]
    ]
    await update.callback_query.edit_message_text("Choose a scenario:", reply_markup=InlineKeyboardMarkup(botones))

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
        await query.edit_message_text(f"Perfect! We are at the {user_data[uid]['scenario']}. Type 'Hello' to start! 🚀")
    
    elif query.data == 'get_vocab':
        scene = user_data[uid]['scenario']
        prompt = f"Give me 5 essential words for a {scene} scenario with Spanish translations. Format: Word - Translation - Example."
        response = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.1-8b-instant")
        await query.message.reply_text(f"📚 *Vocab for {scene}:*\n\n{response.choices[0].message.content}\n\nWrite one sentence using these words!", parse_mode='Markdown')

    elif query.data.startswith('set_lvl_'):
        user_data[uid]['level'] = query.data.replace('set_lvl_', '')
        await show_main_menu(update, uid)

    elif query.data.startswith('set_sce_'):
        user_data[uid]['scenario'] = query.data.replace('set_sce_', '')
        user_data[uid]['history'] = []
        await show_main_menu(update, uid)

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user(uid, update.effective_user.first_name)
    
    user_text = update.message.text
    data = user_data[uid]

    system_prompt = f"""
    Eres 'TeachBot', un tutor de inglés PRO. Usuario: {data['name']}, Nivel: {data['level']}.
    Escenario: {data['scenario']}.

    INSTRUCCIONES DE RESPUESTA:
    1. Actúa según el escenario pero NO olvides que eres un tutor.
    2. Si el usuario comete errores o usa español:
       - Responde en inglés primero.
       - Luego añade una sección: "📝 RECOMENDACIÓN:". Explica en ESPAÑOL el error gramatical y da la opción correcta en inglés.
    3. Si el usuario no entiende algo: Explica de forma sencilla en ESPAÑOL.
    4. SIEMPRE termina tu mensaje con una sección: "🗣️ SIGUE LA CHARLA:". Da una frase exacta en INGLÉS que el usuario podría usar para responderte, seguida de su traducción.
    5. Usa un tono motivador.
    """

    messages = [{"role": "system", "content": system_prompt}]
    for h in data['history'][-4:]:
        messages.append(h)
    messages.append({"role": "user", "content": user_text})

    try:
        response = client.chat.completions.create(messages=messages, model="llama-3.1-8b-instant")
        answer = response.choices[0].message.content
        data['history'].append({"role": "user", "content": user_text})
        data['history'].append({"role": "assistant", "content": answer})
        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text("⚠️ API Error.")

if __name__ == "__main__":
    app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))
    print("🤖 TeachBot Pro is Running...")
    app.run_polling()