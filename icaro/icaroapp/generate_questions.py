import re
import openai
import os
from icaroapp import db
from icaroapp.models import Quiz
import json
import csv

openai.api_key = os.getenv("OPENAI_API_KEY")

def clean_json_response(response_text):
    """
    Limpia la respuesta de OpenAI eliminando caracteres no válidos y formato Markdown.
    """
    # 📌 Eliminar etiquetas de código Markdown como ```json ... ```
    response_text = re.sub(r"```json\n?|```", "", response_text).strip()

    # 📌 Eliminar contenido adicional que pueda haber antes o después del JSON
    match = re.search(r"$begin:math:display$.*$end:math:display$", response_text, re.DOTALL)
    if match:
        response_text = match.group(0)

    return response_text


def generate_complex_question(text, ask_title_group, group_id=1, field_id=1, resource_id=1, nivel_id=1):
    """
    Genera preguntas de examen tipo test sin repetir preguntas ya existentes en la base de datos.
    """

    existing_questions = {q.ask_name for q in Quiz.query.with_entities(Quiz.ask_name).all()}
  

    prompt = f"""
    Genera DOS preguntas de examen tipo test basadas en el siguiente contenido:
    
    {text}

    Requisitos:
    - La pregunta debe ser completamente nueva y no debe haber sido generada antes.
    - NO repitas preguntas ya almacenadas en la base de datos.
    - Genera preguntas que exploren aspectos diferentes del texto para maximizar la diversidad.
    - Debe incluir 4 opciones de respuesta, de las cuales solo una es correcta.
    - Proporciona una explicación detallada de por qué la respuesta correcta es la correcta y por qué las otras son incorrectas.
    - **Evita repetir términos o estructuras de preguntas anteriores.**
    - **Usa temas menos comunes dentro del contexto del documento.**
    - **NO agregues texto adicional fuera del JSON.**
    - **Asegúrate de que la respuesta sea un JSON válido.**
    
    Responde **EXCLUSIVAMENTE** en el siguiente formato JSON:

    ```json
    [
        {{
            "ask_title_group": "{ask_title_group}",
            "ask_name": "Pregunta completamente diferente a las anteriores",
            "answer1": "Opción A",
            "answer2": "Opción B",
            "answer3": "Opción C",
            "answer4": "Opción D",
            "correct_answer": "La opción correcta",
            "ask_description": "Explicación detallada asegurando que es un tema nuevo.",
            "group_id": {group_id},
            "field_id": {field_id},
            "resource_id": {resource_id},
            "nivel_id": {nivel_id}
        }},
        {{
            "ask_title_group": "{ask_title_group}",
            "ask_name": "Otra pregunta completamente diferente",
            "answer1": "Opción A",
            "answer2": "Opción B",
            "answer3": "Opción C",
            "answer4": "Opción D",
            "correct_answer": "La opción correcta",
            "ask_description": "Explicación detallada asegurando que es un tema nuevo.",
            "group_id": {group_id},
            "field_id": {field_id},
            "resource_id": {resource_id},
            "nivel_id": {nivel_id}
        }}
    ]
    ```
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un generador de preguntas expertas de nivel avanzado."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9  # 🔥 Aumentamos la temperatura para obtener más variabilidad
        )

        result = response.choices[0].message.content.strip()
        print("🔍 Respuesta de OpenAI ANTES de limpiar:")
        print(result)

        try:
            questions_data = json.loads(result)
            if not isinstance(questions_data, list):
                print("❌ Error: OpenAI no devolvió una lista de preguntas.")
                return []

            # 📌 Filtrar preguntas ya existentes en la base de datos
            questions_data = [q for q in questions_data if q["ask_name"] not in existing_questions]

            if not questions_data:
                print("❌ No se generaron preguntas nuevas (todas eran repetidas).")
                return []

        except json.JSONDecodeError:
            print("❌ Error: La respuesta de OpenAI no es un JSON válido")
            return []

        # Guardar preguntas en la base de datos
        for question_data in questions_data:
            new_quiz = Quiz(
                ask_title_group=ask_title_group,
                ask_name=question_data["ask_name"],
                answer1=question_data["answer1"],
                answer2=question_data["answer2"],
                answer3=question_data.get("answer3"),
                answer4=question_data.get("answer4"),
                correct_answer=question_data["correct_answer"],
                ask_description=question_data["ask_description"],
                group_id=group_id,
                field_id=field_id,
                resource_id=resource_id,
                nivel_id=nivel_id
            )

            db.session.add(new_quiz)
        
        db.session.commit()

        return questions_data

    except Exception as e:
        print(f"❌ Error en la generación de la pregunta: {e}")
        db.session.rollback()
        return []


def save_questions_to_csv(questions, pdf_filename):
    """
    Guarda las preguntas generadas en un archivo CSV (o TSV) con el mismo nombre que el PDF, 
    usando tabulaciones como delimitador.
    """

    # 📌 Obtener el nombre del CSV basado en el nombre del PDF
    csv_filename = os.path.splitext(pdf_filename)[0] + ".csv"
    tsv_filename = os.path.splitext(pdf_filename)[0] + ".tsv" #nombre para el archivo de tabulaciones

    # 📌 Verificar que `DATA_FOLDER` está configurado, si no, usar un directorio por defecto
    data_folder = os.getenv("DATA_FOLDER", "./data")  # Usa "./data" si no está definida la variable
    os.makedirs(data_folder, exist_ok=True)  # Crear la carpeta si no existe

    csv_path = os.path.join(data_folder, csv_filename)
    tsv_path = os.path.join(data_folder, tsv_filename)

    fieldnames = [
        "ask_title_group", "ask_name", "answer1", "answer2", "answer3", "answer4", "correct_answer", "ask_description", "group_id", "field_id", "resource_id", "nivel_id"
    ]

    # 📌 Verificar que hay preguntas antes de escribir el archivo
    if not questions:
        print("❌ No se generaron preguntas, no se creará el CSV.")
        return None

    with open(csv_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for question in questions:
            writer.writerow(question)
    
    # Save as TSV (tab-delimited)
    with open(tsv_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter='\t')  # Changed here
        writer.writeheader()
        for question in questions:
            writer.writerow(question)

    # 📌 Verificar si el archivo CSV se ha creado correctamente
    if not os.path.exists(csv_path):
        print(f"❌ Error: No se pudo crear el archivo CSV en {csv_path}")
        return None
    if not os.path.exists(tsv_path):
        print(f"❌ Error: No se pudo crear el archivo TSV en {tsv_path}")
        return None

    print(f"✅ TSV guardado correctamente en {tsv_path}")
    return csv_path, tsv_path

