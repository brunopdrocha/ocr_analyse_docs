import os
from dotenv import load_dotenv

def carregar_variaveis():
    load_dotenv()
    config = {
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "GOOGLE_CREDENTIALS": os.getenv("GOOGLE_CREDENTIALS"),
        "POPPLER_PATH": os.getenv("POPPLER_PATH"),
        "PDFS_FOLDER": os.getenv("PDFS_FOLDER"),
        "TEXTOS_FOLDER": os.getenv("TEXTOS_FOLDER"),
        "RESPOSTAS_FOLDER": os.getenv("RESPOSTAS_FOLDER"),
    }

    for chave, valor in config.items():
        if not valor:
            raise ValueError(f"Variável de ambiente {chave} não encontrada.")
    return config

print(carregar_variaveis())