import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

try:
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "Di 'Hola, mundo'"}]
    )
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error en la conexión con OpenAI: {e}")
    


# try:
#     models = openai.models.list()
#     for model in models:
#         print(model.id)
# except Exception as e:
#     print(f"Error al obtener la lista de modelos: {e}")