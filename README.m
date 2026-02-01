TeachBot 🤖 | Your Smart English Tutor
TeachBot is an interactive Telegram chatbot designed for immersive English practice. Unlike a generic chat, TeachBot acts as a pedagogical tutor that adapts vocabulary, corrects grammatical errors in Spanish, and guides the conversation through dynamic scenarios.

✨ Key Features
Dynamic Scenarios: Practice in real-life contexts such as a job interview, an airport, or a coffee shop.

Pedagogical Correction: If you make a mistake or mix languages, the bot explains the grammatical rule in Spanish to ensure understanding.

Conversation Scaffolding: Each response includes suggested English phrases so the conversation never stops.

Vocabulary Boost: Instant keyword generation based on the selected scenario.

Adjustable Levels: Difficulty settings from A1 (Beginner) to C1 (Advanced).

🛠️ Technologies Used
Language: Python 3.10+

Framework: python-telegram-bot (Asynchronous)

AI Engine: Groq API (Llama 3.1-8b-instant model)

Variable Management: python-dotenv

🚀 Installation and Configuration
Clone the repository:

Bash
git clone https://github.com/EstickSB/teachbot-English-ChatBot-Telegram.git
cd teachbot-English-ChatBot-Telegram
Install dependencies:

Bash
pip install python-telegram-bot groq python-dotenv
Configure environment variables: Create an .env file in the project root with your credentials:

Excerpt from Code

TELEGRAM_TOKEN=your_botfather_token
GROQ_API_KEY=your_groq_api_key
Run the bot:

Bash
python bot.py


📈 Roadmap / Upcoming Improvements

[ ] Data Persistence: Implement SQLite to save progress and user profile after restarting the bot.

[ ] Voice Support: Integration with Whisper for listening and speaking practice.

[ ] Logging System: Record common grammatical errors to generate a study report.