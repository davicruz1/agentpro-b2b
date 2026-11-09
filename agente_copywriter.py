import os
import re
import time
import logging
from dotenv import load_dotenv
from google import genai
from typing import TypedDict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Lead(TypedDict):
    nome: str
    telefone: str
    nicho: str
    link_investigacao: str

class Pitch(TypedDict):
    nome_lead: str
    mensagem: str
    link_whatsapp: str

def inicializar_ia() -> genai.Client:
    load_dotenv()
    chave_api = os.getenv("GEMINI_API_KEY")
    if not chave_api:
        raise ValueError("Chave GEMINI_API_KEY não encontrada no arquivo .env.")
    return genai.Client(api_key=chave_api)

def formatar_numero_whatsapp(telefone: str) -> str:
    numero_limpo = re.sub(r'\D', '', telefone)
    return f"https://wa.me/{numero_limpo}" if numero_limpo else "Sem número válido"

def gerar_pitch_vendas(lead: Lead, cliente_ia: genai.Client, modelo: str = 'gemini-3.5-flash') -> Pitch:
    prompt = f"""
    Você é um executivo de vendas B2B de uma agência de tecnologia.
    
    DADOS DO CLIENTE ALVO:
    - Empresa: {lead.get('nome', 'Empresa')}
    - Nicho: {lead.get('nicho', 'Negócio local')}
    - Localização: Zurique, Suíça
    
    ESTRUTURA DE SAÍDA OBRIGATÓRIA:
    
    Escreva a mensagem em Alemão formal suíço (usando 'Sie'). Diga que notou no Google Maps que não têm site profissional e ofereça mostrar um rascunho de design (Entwurf) sem compromisso. Call to Action: "Darf ich Ihnen den Link dazu kurz hier schicken?"
    
    🇧🇷 TRADUÇÃO PARA SEU CONTROLE:
    (Coloque aqui a tradução exata em Português Brasileiro)
    """
    
    texto_mensagem = ""
    
    for tentativa in range(3):
        try:
            resposta = cliente_ia.models.generate_content(
                model=modelo,
                contents=prompt
            )
            if resposta.text:
                texto_mensagem = resposta.text.strip()
                break 
        except Exception as e:
            logger.warning(f"Falha na IA para '{lead.get('nome')}' (Tentativa {tentativa+1}/3): {e}")
            texto_mensagem = f"Erro da API do Google: {str(e)}\n\nO servidor do Google bloqueou a requisição (geralmente por Rate Limit). Aguarde um minuto e tente novamente."
            time.sleep(5) 

    return {
        "nome_lead": lead.get('nome', 'Desconhecido'),
        "mensagem": texto_mensagem,
        "link_whatsapp": formatar_numero_whatsapp(lead.get('telefone', ''))
    }