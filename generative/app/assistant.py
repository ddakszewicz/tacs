import json
import os
import time
from typing import Optional, List, Dict, Any

import telebot
from dotenv import load_dotenv
from openai import OpenAI

import database

# Cargar variables de entorno
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Inicializar los clientes
bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

# Diccionario para almacenar las conversaciones
conversations = {}

# Configuración del sistema
SYSTEM_PROMPT = """Eres un asistente amable y servicial que ayuda a los alumnos en la cursada de TACS materia de programación de la facultad UTN de Buenos Aires.
Proporciona respuestas concisas y útiles, manteniendo un tono conversacional.

Tienes acceso a una base de datos con las siguientes tablas:

-- tabla de alumnos
CREATE TABLE alumnos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50),
    apellido VARCHAR(50),
    legajo VARCHAR(5)
);

-- tabla de cursadas
CREATE TABLE cursadas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    alumno_id INT,
    cuatrimestre INT,
    anio INT,
    nota INT,
    FOREIGN KEY (alumno_id) REFERENCES alumnos(id)
);

Cuando necesites consultar información de la base de datos, utiliza la función get_reports_from_query con una consulta SQL apropiada.
Siempre usa aliases para las tablas cuando hagas JOINs y asume información razonable si es necesario."""


def get_report(query: str) -> str:
    """Ejecuta una consulta SQL y devuelve los resultados"""
    try:
        output = database.query(query)
        return str(output) if output else "No se encontraron resultados para la consulta"
    except Exception as e:
        return f"Error al ejecutar la consulta: {str(e)}"


# Definición de herramientas para la Response API
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_reports_from_query",
            "description": "Ejecuta una consulta SQL en la base de datos de alumnos y cursadas",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La consulta SQL a ejecutar. Ej: SELECT * FROM alumnos. Usar aliases para las tablas en JOINs."
                    }
                },
                "required": ["query"]
            }
        }
    }
]


class ChatManager:
    def __init__(self):
        self.client = client
        self.max_history = 20  # Limitar el historial para evitar tokens excesivos

    def get_conversation_history(self, chat_id: int) -> List[Dict[str, Any]]:
        """Obtiene el historial de conversación para un chat"""
        if chat_id not in conversations:
            conversations[chat_id] = []
        return conversations[chat_id]

    def add_message(self, chat_id: int, role: str, content: str):
        """Agrega un mensaje al historial de conversación"""
        history = self.get_conversation_history(chat_id)
        history.append({"role": role, "content": content})

        # Mantener solo los últimos mensajes para evitar exceso de tokens
        if len(history) > self.max_history:
            # Mantener el mensaje del sistema y los últimos mensajes
            system_messages = [msg for msg in history if msg["role"] == "system"]
            recent_messages = history[-self.max_history:]
            conversations[chat_id] = system_messages + recent_messages

    def execute_function_call(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """Ejecuta una llamada a función"""
        if function_name == "get_reports_from_query":
            query = arguments.get("query", "")
            return get_report(query)
        else:
            return f"Función '{function_name}' no encontrada"

    def send_message(self, chat_id: int, message: str) -> Optional[str]:
        """Envía un mensaje y obtiene la respuesta del modelo"""
        try:
            # Obtener historial de conversación
            history = self.get_conversation_history(chat_id)

            # Si es la primera conversación, agregar el prompt del sistema
            if not history:
                self.add_message(chat_id, "system", SYSTEM_PROMPT)
                history = self.get_conversation_history(chat_id)

            # Agregar el mensaje del usuario
            self.add_message(chat_id, "user", message)
            history = self.get_conversation_history(chat_id)

            # Realizar la llamada a la API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=history,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1500
            )

            assistant_message = response.choices[0].message

            # Verificar si hay llamadas a funciones
            if assistant_message.tool_calls:
                # Agregar el mensaje del asistente con las tool calls
                self.add_message(chat_id, "assistant", assistant_message.content or "")

                # Procesar cada tool call
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    print(f"Ejecutando función: {function_name} con argumentos: {function_args}")

                    # Ejecutar la función
                    function_result = self.execute_function_call(function_name, function_args)

                    # Agregar el resultado de la función al historial
                    self.add_message(chat_id, "tool", function_result)

                # Obtener la respuesta final después de las tool calls
                updated_history = self.get_conversation_history(chat_id)
                final_response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=updated_history,
                    temperature=0.7,
                    max_tokens=1500
                )

                final_message = final_response.choices[0].message.content
                self.add_message(chat_id, "assistant", final_message)
                return final_message
            else:
                # Respuesta simple sin tool calls
                response_content = assistant_message.content
                self.add_message(chat_id, "assistant", response_content)
                return response_content

        except Exception as e:
            print(f"Error en ChatManager: {str(e)}")
            return "Ocurrió un error al procesar tu mensaje. Por favor, intenta de nuevo."

    def clear_conversation(self, chat_id: int):
        """Limpia el historial de conversación"""
        if chat_id in conversations:
            conversations[chat_id] = []
        return True


# Inicializar el gestor de chat
chat_manager = ChatManager()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_message = """
¡Hola! Soy un asistente potenciado por GPT-4 para ayudarte con TACS.

Puedo ayudarte con consultas sobre alumnos, cursadas y cualquier pregunta relacionada con la materia.

Comandos disponibles:
/start - Iniciar el bot
/clear - Comenzar una nueva conversación
/help - Mostrar esta ayuda
    """
    bot.reply_to(message, welcome_message)


@bot.message_handler(commands=['help'])
def send_help(message):
    help_message = """
🤖 **Asistente TACS**

Puedo ayudarte con:
- Consultas sobre alumnos y sus datos
- Información sobre cursadas y notas
- Preguntas generales sobre la materia TACS

Ejemplos de preguntas:
- "Muéstrame todos los alumnos"
- "¿Cuáles son las notas del alumno con legajo 12345?"
- "¿Quién tiene la nota más alta?"

Comandos:
/clear - Reiniciar conversación
/help - Mostrar esta ayuda
    """
    bot.reply_to(message, help_message)


@bot.message_handler(commands=['clear'])
def clear_conversation(message):
    """Inicia una nueva conversación"""
    if chat_manager.clear_conversation(message.chat.id):
        bot.reply_to(message, "¡Conversación reiniciada! ¿En qué puedo ayudarte?")
    else:
        bot.reply_to(message, "Hubo un error al reiniciar la conversación. Por favor, intenta de nuevo.")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Maneja todos los mensajes de texto"""
    chat_id = message.chat.id
    user_message = message.text

    # Mostrar indicador de "escribiendo..."
    bot.send_chat_action(chat_id, 'typing')

    # Obtener respuesta del asistente
    response = chat_manager.send_message(chat_id, user_message)

    if response:
        # Enviar la respuesta en fragmentos si es muy larga
        if len(response) > 4096:
            for x in range(0, len(response), 4096):
                bot.reply_to(message, response[x:x + 4096])
        else:
            bot.reply_to(message, response)

        print(f"Usuario: {user_message} | Asistente: {response}")
    else:
        bot.reply_to(message, "Lo siento, no pude procesar tu mensaje. Intenta de nuevo.")


def main():
    print("Bot iniciado con OpenAI Chat Completions API...")
    print(f"DB health: {database.healthcheck()}")

    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Error en el bot: {e}")
            time.sleep(15)


if __name__ == "__main__":
    main()