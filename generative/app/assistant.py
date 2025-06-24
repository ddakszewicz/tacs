import json
import os
import time
from typing import Optional, Dict, Any

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

# Diccionario para almacenar los response_ids de cada conversación
conversation_responses = {}

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

VECTOR_STORE="vs_JKz7Tha2MacqyIQD9WQQ9RAM"

def get_report(query: str) -> str:
    """Ejecuta una consulta SQL y devuelve los resultados"""
    try:
        output = database.query(query)
        return str(output) if output else "No se encontraron resultados para la consulta"
    except Exception as e:
        return f"Error al ejecutar la consulta: {str(e)}"


# Definición de herramientas para la Responses API
TOOLS = [
    {
        "type": "function",
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
    },
    {
        "type": "file_search",
        "vector_store_ids": [VECTOR_STORE]
    }
]


class ResponsesManager:
    def __init__(self):
        self.client = client

    def get_last_response_id(self, chat_id: int) -> Optional[str]:
        """Obtiene el último response_id para un chat"""
        return conversation_responses.get(chat_id)

    def store_response_id(self, chat_id: int, response_id: str):
        """Almacena el response_id para un chat"""
        conversation_responses[chat_id] = response_id

    def execute_function_call(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """Ejecuta una llamada a función"""
        if function_name == "get_reports_from_query":
            query = arguments.get("query", "")
            return get_report(query)
        else:
            return f"Función '{function_name}' no encontrada"

    def send_message(self, chat_id: int, message: str) -> Optional[str]:
        """Envía un mensaje usando la Responses API con response_id"""
        try:
            # Preparar el payload base
            payload = {
                "model": "gpt-4o-mini",
                "input": [{"role": "user", "content": message}],
                "instructions":SYSTEM_PROMPT,
                "tools": TOOLS,
                "store": True  # Importante: permite que OpenAI almacene la conversación
            }

            # Obtener el último response_id si existe
            last_response_id = self.get_last_response_id(chat_id)

            if last_response_id:
                # Continuar conversación existente
                payload["previous_response_id"] = last_response_id

            # Realizar la llamada a la Responses API
            response = self.client.responses.create(**payload)

            # Almacenar el nuevo response_id
            self.store_response_id(chat_id, response.id)

            # Verificar si hay llamadas a funciones que requieren procesamiento

            tool_outputs = []
            for output in response.output:
                # Procesar tool calls
                if (output.type =="function_call"):
                    tool_call=output
                    function_name = tool_call.name
                    function_args = json.loads(tool_call.arguments)
                    print(f"Ejecutando función: {function_name} con argumentos: {function_args}")

                    # Ejecutar la función
                    function_result = self.execute_function_call(function_name, function_args)

                    tool_outputs.append({
                        "tool_call_id": tool_call.call_id,
                        "output": function_result
                    })

            if tool_outputs:
                # Continuar la conversación con los resultados de las tool calls
                follow_up_payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "tool",
                            "tool_call_id": output["tool_call_id"],
                            "content": output["output"]
                        } for output in tool_outputs
                    ],
                    "previous_response_id": response.id,
                    "store": True,
                }

                # Obtener la respuesta final
                final_response = self.client.responses.create(**follow_up_payload)

                # Actualizar el response_id
                self.store_response_id(chat_id, final_response.id)

                return final_response.output_text
            else:
               return response.output_text


        except Exception as e:
            print(f"Error en ResponsesManager: {str(e)}")
            return "Ocurrió un error al procesar tu mensaje. Por favor, intenta de nuevo."

    def clear_conversation(self, chat_id: int):
        """Limpia la conversación eliminando el response_id almacenado"""
        if chat_id in conversation_responses:
            del conversation_responses[chat_id]
        return True


# Inicializar el gestor de respuestas
responses_manager = ResponsesManager()


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
    if responses_manager.clear_conversation(message.chat.id):
        bot.reply_to(message, "¡Conversación reiniciada! ¿En qué puedo ayudarte?")
    else:
        bot.reply_to(message, "Hubo un error al reiniciar la conversación. Por favor, intenta de nuevo.")


@bot.message_handler(commands=['debug'])
def debug_conversation(message):
    """Comando de debug para mostrar el response_id actual"""
    chat_id = message.chat.id
    response_id = responses_manager.get_last_response_id(chat_id)

    if response_id:
        bot.reply_to(message, f"Response ID actual: {response_id}")
    else:
        bot.reply_to(message, "No hay conversación activa.")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Maneja todos los mensajes de texto"""
    chat_id = message.chat.id
    user_message = message.text

    # Mostrar indicador de "escribiendo..."
    bot.send_chat_action(chat_id, 'typing')

    # Obtener respuesta del asistente
    response = responses_manager.send_message(chat_id, user_message)

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
    print("Bot iniciado con OpenAI Responses API...")
    print(f"DB health: {database.healthcheck()}")

    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Error en el bot: {e}")
            time.sleep(15)


if __name__ == "__main__":
    main()