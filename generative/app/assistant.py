import json
import os
import time
from typing import Optional, reveal_type

import telebot
from dotenv import load_dotenv
from openai import OpenAI

import database

# Cargar variables de entorno
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('ASSISTANT_ID')  # ID del asistente que crearemos

# Inicializar los clientes
bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

# Diccionario para almacenar los hilos de conversación
threads = {}
headers = {
    "OpenAI-Beta": "assistants=v2",
}


def get_report(arguments: dict):
    try:
        output=database.query(arguments["query"])
        return str(output) if output   else "Error al ejecutar la consulta"
    except Exception as e:
        return "Error al ejecutar la consulta: " + str(e)



functions = {
    "get_reports_from_query": {
        "instructions": """When you call get_reports_from_query consider the following schema to create proper queries:
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
""",
        "declaration": {
            "name": "get_reports_from_query",
            "description": "Gets a report from an sql query",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The expected query to execute. e.g. SELECT * FROM alumnos. Please join the tables if is necessary adding aliases to tables. Made assumptions that you need and always try to run the query",
                    }
                },
                "required": ["query"],
            },
        },
        "execute": get_report
    }
}


class AssistantManager:
    def __init__(self):
        self.client = client
        self.assistant_id = ASSISTANT_ID or self.create_assistant()

    def create_assistant(self) -> str:
        """Crea un nuevo asistente si no existe"""
        assistant = self.client.beta.assistants.create(
            name="TACS Assistant",
            instructions="""Eres un asistente amable y servicial que ayuda a los alumnos en la cursada de TACS materia de programación de la facultad UTN de Buenos Aires.
            Proporciona respuestas concisas y útiles, manteniendo un tono conversacional.""",
            model="gpt-4o-mini",
            extra_headers=headers
        )
        print(f"Asistente creado: {assistant.id}")
        return assistant.id

    def get_or_create_thread(self, chat_id: int) -> str:
        """Obtiene o crea un nuevo hilo para el chat"""
        if chat_id not in threads:
            thread = self.client.beta.threads.create(extra_headers=headers)
            threads[chat_id] = thread.id
        return threads[chat_id]

    def send_message(self, chat_id: int, message: str) -> Optional[str]:
        """Envía un mensaje al asistente y espera su respuesta"""
        try:
            thread_id = self.get_or_create_thread(chat_id)

            # Agregar el mensaje del usuario al hilo
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message,
                extra_headers=headers
            )

            # Ejecutar el asistente
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id,
                extra_headers=headers,
                additional_instructions="\n".join(func["instructions"] for func in functions.values()),
                tools=[{"type":"file_search"}]+[{"type": "function", "function": func["declaration"]} for func in functions.values()]
            )

            # Esperar la respuesta
            while True:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id,
                    extra_headers=headers
                )
                if run_status.status == 'completed':
                    break
                elif run_status.status == 'failed':
                    return "Lo siento, hubo un error al procesar tu mensaje."
                elif run_status.status == 'requires_action':
                    # Define the list to store tool outputs
                    tool_outputs = []
                    # Loop through each tool in the required action section
                    for tool in run_status.required_action.submit_tool_outputs.tool_calls:
                        print(f"Function: {tool.function.name} | Arguments: {tool.function.arguments}")
                        function = functions[tool.function.name]
                        if function:
                            output = function["execute"](json.loads(tool.function.arguments))
                            tool_outputs.append({
                                "tool_call_id": tool.id,
                                "output": output
                            })
                        else:
                            tool_outputs.append({
                                "tool_call_id": tool.id,
                                "output": "Function not found"
                            })
                    try:
                        run = client.beta.threads.runs.submit_tool_outputs(
                            thread_id=thread_id,
                            run_id=run_status.id,
                            tool_outputs=tool_outputs
                        )
                        print("Tool outputs submitted successfully.")
                    except Exception as e:
                        print("Failed to submit tool outputs:", e)

                time.sleep(1)

            # Obtener los mensajes
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                extra_headers=headers
            )

            # Retornar el último mensaje del asistente
            for msg in messages.data:
                if msg.role == "assistant":
                    result= "\n".join(content.text["value"] if isinstance(content.text,dict) else content.text.value  for content in msg.content if content.type == "text" and content.text)
                    return result

            return "No se pudo obtener una respuesta."

        except Exception as e:
            print(f"Error en AssistantManager: {str(e)}")
            return "Ocurrió un error al procesar tu mensaje. Por favor, intenta de nuevo."

    def clear_thread(self, chat_id: int):
        """Elimina el hilo actual y crea uno nuevo"""
        if chat_id in threads:
            try:
                # Crear un nuevo hilo
                thread = self.client.beta.threads.create(extra_headers=headers)
                threads[chat_id] = thread.id
                return True
            except Exception as e:
                print(f"Error al limpiar el hilo: {str(e)}")
                return False
        return True


# Inicializar el gestor del asistente
assistant_manager = AssistantManager()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_message = """
    ¡Hola! Soy un asistente potenciado por GPT-4. 
    
    Puedes preguntarme lo que quieras y mantendré el contexto de nuestra conversación.
    
    Comandos disponibles:
    /start - Iniciar el bot
    /clear - Comenzar una nueva conversación
    """
    bot.reply_to(message, welcome_message)


@bot.message_handler(commands=['clear'])
def clear_conversation(message):
    """Inicia una nueva conversación"""
    if assistant_manager.clear_thread(message.chat.id):
        bot.reply_to(message, "¡Conversación reiniciada! ¿En qué puedo ayudarte?")
    else:
        bot.reply_to(message, "Hubo un error al reiniciar la conversación. Por favor, intenta de nuevo.")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Maneja todos los mensajes de texto"""
    chat_id = message.chat.id

    # Mostrar indicador de "escribiendo..."
    bot.send_chat_action(chat_id, 'typing')

    # Obtener respuesta del asistente
    response = assistant_manager.send_message(chat_id, message.text)

    # Enviar la respuesta en fragmentos si es muy larga
    if len(response) > 4096:
        for x in range(0, len(response), 4096):
            bot.reply_to(message, response[x:x + 4096])
    else:
        bot.reply_to(message, response)
    print(f"Usuario: {message.text} | Asistente: {response}")


def main():
    print("Bot iniciado con OpenAI Assistants API...")
    print(f"DB health {database.healthcheck()}")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Error en el bot: {e}")
            time.sleep(15)


if __name__ == "__main__":
    main()
