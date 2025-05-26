import os
import io
import time
from PIL import Image, ImageFilter
from pdf2image import convert_from_path
from google.cloud import vision
from pergunta_gemini import perguntar_sobre_documento
from dotenv import load_dotenv
import json

# Load .env
load_dotenv()


def main():
    # Get paths from environment
    credentials_path = os.getenv("GOOGLE_CREDENTIALS")
    pdfs_folder = os.getenv("PDFS_FOLDER")
    extracao_folder = os.getenv("EXTRACAO_FOLDER")
    respostas_folder = os.getenv("RESPOSTAS_FOLDER")
    imagens_folder = os.getenv("IMAGENS_FOLDER")
    poppler_path = os.getenv("POPPLER_PATH")

    # Verify credentials
    if not os.path.exists(credentials_path):
        print(f"❌ Credenciais não encontradas: {credentials_path}")
        return

    # Setup
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    client = vision.ImageAnnotatorClient()

    # Create folders
    os.makedirs(extracao_folder, exist_ok=True)
    os.makedirs(respostas_folder, exist_ok=True)
    os.makedirs(imagens_folder, exist_ok=True)

    # Process PDFs
    for filename in os.listdir(pdfs_folder):
        if filename.lower().endswith(".pdf"):
            caminho_pdf = os.path.join(pdfs_folder, filename)
            print(f"📄 Processando {filename}...")

            try:
                paginas = convert_from_path(
                    caminho_pdf, dpi=300, poppler_path=poppler_path
                )
                resultado = []
                imagem_paths = []

                # Create document subfolder
                nome_documento = os.path.splitext(filename)[0]
                pasta_documento = os.path.join(imagens_folder, nome_documento)
                os.makedirs(pasta_documento, exist_ok=True)

                # Process each page
                for i, pagina in enumerate(paginas):
                    # OCR processing
                    img = pagina.convert("L").filter(ImageFilter.SHARPEN)
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG")
                    image = vision.Image(content=buffer.getvalue())
                    image_context = vision.ImageContext(language_hints=["pt"])

                    # Extract text with retry
                    for tentativa in range(3):
                        try:
                            response = client.document_text_detection(
                                image=image, image_context=image_context
                            )
                            texto = response.full_text_annotation.text
                            resultado.append(f"\n--- Página {i+1} ---\n{texto}\n")
                            break
                        except Exception as e:
                            if tentativa == 2:
                                raise RuntimeError(f"Falha ao processar página {i+1}")
                            time.sleep(2)

                    # Save page image
                    img_path = os.path.join(pasta_documento, f"pagina_{i+1:03d}.jpg")
                    pagina.save(img_path, "JPEG")
                    imagem_paths.append(img_path)

                    time.sleep(1)

                # Save OCR text
                txt_path = os.path.join(extracao_folder, f"{nome_documento}.txt")
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.writelines(resultado)
                print(f"✅ Texto extraído e salvo")

                resultado_str = "".join(resultado)
                # Generate response
                resposta_llm = perguntar_sobre_documento(resultado_str)

                # Verificar se a resposta não está vazia
                if not resposta_llm or not resposta_llm.strip():
                    print(f"⚠️ Resposta vazia do LLM para {filename}")
                    continue

                try:
                    # Limpar resposta do LLM (remover markdown)
                    resposta_limpa = resposta_llm.strip()
                    if resposta_limpa.startswith("```json"):
                        resposta_limpa = resposta_limpa[7:]  # Remove ```json
                    if resposta_limpa.endswith("```"):
                        resposta_limpa = resposta_limpa[:-3]  # Remove ```
                    resposta_limpa = resposta_limpa.strip()
                    
                    # Format text response to JSON
                    resposta_llm_json = json.loads(resposta_limpa)
                    
                    resposta_path = os.path.join(
                        respostas_folder, f"{nome_documento}_response.json"
                    )
                    with open(resposta_path, "w", encoding="utf-8") as f:
                        json.dump(resposta_llm_json, f, ensure_ascii=False, indent=2)
                    print(f"📝 Resposta do llm salva para {filename}")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Erro ao decodificar JSON para {filename}: {e}")
                    print(f"Resposta recebida: {resposta_llm[:200]}...")  # Mostrar primeiros 200 chars
                    
                    # Salvar resposta bruta para debug
                    # debug_path = os.path.join(respostas_folder, f"{nome_documento}_debug.txt")
                    # with open(debug_path, "w", encoding="utf-8") as f:
                    #     f.write(resposta_llm)
                    # print(f"💾 Resposta bruta salva em {debug_path} para análise")

                # # Interactive questions
                # while True:
                #     pergunta = input("❓ Pergunta sobre o documento (Enter para pular): ").strip()
                #     if not pergunta:
                #         break
                #     resposta = perguntar_sobre_documento(imagem_paths, pergunta)
                #     print(f"💬 {resposta}\n")

            except Exception as e:
                print(f"❌ Erro ao processar {filename}: {e}")


if __name__ == "__main__":
    main()