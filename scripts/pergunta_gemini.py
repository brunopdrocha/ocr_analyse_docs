from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

# Configuração LLM 
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

with open("system_prompt.txt", "r",encoding="utf-8") as arquivo:
    system_prompt = arquivo.read()
    

def perguntar_sobre_documento(documento_texto: str) -> str:
    """
    Envia um arquivo .txt e um prompt ao modelo Gemini via SDK python-genai.

    Args:
        documento_texto (str): Documento bruto a ser analisado

    Returns:
        str: Resposta do modelo formato JSON.
    """ 
    # Gera o conteúdo combinando prompt e arquivo
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[types.Part.from_text(text=documento_texto)],
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3
        )
    )
    return response.text


# Exemplo de uso
if __name__ == "__main__":
    with open(rf"data\extracao\10211872_BR76036_Certidões_Matricula_Imovel.txt", "r",encoding="utf-8") as arquivo:
        documento_extraido = arquivo.read()
    
    resposta = perguntar_sobre_documento(documento_extraido)
    print(resposta)