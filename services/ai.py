import google.generativeai as genai
import os


def consultar_ia(prompt):

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    model = genai.GenerativeModel("gemini-1.5-pro")

    response = model.generate_content(prompt)

    return response.text
