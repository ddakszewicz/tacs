import telebot
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Crear instancia del bot
bot = telebot.TeleBot(TOKEN)

# Manejador para el comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Hola! Soy tu bot de Telegram. ¿En qué puedo ayudarte?")

# Manejador para el comando /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
    Comandos disponibles:
    /start - Iniciar el bot
    /help - Mostrar esta ayuda
    """
    bot.reply_to(message, help_text)

# Manejador para mensajes de texto
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Recibí tu mensaje: {message.text}")

# Iniciar el bot
if __name__ == "__main__":
    print("Bot iniciado...")
    bot.polling()
