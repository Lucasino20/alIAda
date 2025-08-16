from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from openai import OpenAI
import time

# Inicializa el cliente
client = OpenAI(api_key="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")

# Tu agente de Platform AI
assistant_id = "asst_j8TbTUFMM2B11EGmsJy9rC3T"

# Diccionario en memoria para mantener threads por usuario (ejemplo simple)
user_threads = {}

app = FastAPI()

@app.post("/start_chat/")
async def start_chat(user_id: str = Form(...)):
    """
    Crea un nuevo thread para el usuario y lo guarda en memoria.
    """
    thread = client.beta.threads.create()
    user_threads[user_id] = thread.id
    return {"message": "✅ Chat iniciado", "thread_id": thread.id}

@app.post("/send_message/")
async def send_message(user_id: str = Form(...), user_input: str = Form(...)):
    """
    Envía un mensaje al agente dentro del thread del usuario.
    """
    if user_id not in user_threads:
        return JSONResponse(content={"error": "Primero inicia un chat con /start_chat/"}, status_code=400)

    thread_id = user_threads[user_id]

    # 1. Enviar mensaje del usuario
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_input
    )

    # 2. Ejecutar el agente
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # 3. Esperar respuesta
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        if run_status.status == "completed":
            break
        elif run_status.status == "failed":
            return JSONResponse(content={"error": "❌ El run falló"}, status_code=500)
        time.sleep(1)

    # 4. Obtener último mensaje del agente
    messages = client.beta.threads.messages.list(thread_id=thread_id)

    for msg in reversed(messages.data):
        if msg.role == "assistant":
            return {"respuesta": msg.content[0].text.value}

    return {"respuesta": None}
