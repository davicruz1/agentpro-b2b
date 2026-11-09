import os
import csv
import time
import logging
import requests
import urllib.parse
from datetime import datetime
from typing import TypedDict, List, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from langgraph.graph import StateGraph, END
from duckduckgo_search import DDGS

class Config:
    USER_AGENT = "AgenteProspeccaoB2B/5.0"
    TIMEOUT_QUERY_DB = 60
    TIMEOUT_HTTP_LOCAL = 75
    MAX_RETRIES = 3
    PASTA_LEADS = "leads_extraidos"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NICHOS_LUCRATIVOS = {
    "restaurantes": '"amenity"="restaurant"',
    "padarias_e_cafes": '"shop"="bakery"',
    "clinicas_medicas": '"amenity"="clinic"',
    "dentistas": '"amenity"="dentist"',
    "escritorios_advocacia": '"office"="lawyer"',
    "arquitetos": '"office"="architect"',
    "estudios_tatuagem": '"shop"="tattoo"'
}

class Lead(TypedDict):
    nome: str
    telefone: str
    nicho: str
    link_investigacao: str

class AgentState(TypedDict):
    cidade: str
    nicho_alvo: str  
    leads_encontrados: List[Lead]
    arquivo_salvo: str
    erro: str

def criar_sessao_resiliente() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=Config.MAX_RETRIES, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["POST"])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def salvar_leads_csv(leads: List[Lead], cidade: str, nicho: str) -> str:
    if not os.path.exists(Config.PASTA_LEADS):
        os.makedirs(Config.PASTA_LEADS)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"{Config.PASTA_LEADS}/{nicho}_{cidade.replace(' ', '_')}_{timestamp}.csv"
    with open(nome_arquivo, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["nome", "telefone", "nicho", "link_investigacao"])
        writer.writeheader()
        writer.writerows(leads)
    return nome_arquivo

def checar_falso_positivo_duckduckgo(nome_empresa: str, cidade: str) -> bool:
    """Retorna True se ACHAR um site, ou se o buscador FALHAR (para descartar o lead por segurança)"""
    try:
        resultados = DDGS().text(f"{nome_empresa} {cidade} official website", max_results=3)
        if not resultados:
            return False # Realmente não achou nada, lead limpo.

        diretorios_comuns = ['tripadvisor', 'yelp', 'facebook', 'instagram', 'local.ch', 'search.ch', 'thefork', 'zueri.ch', 'map.geo.admin.ch', 'guide.michelin']
        
        for res in resultados:
            url = res.get('href', '').lower()
            # Se a URL não for um diretório de terceiros, é o site oficial
            if not any(diretorio in url for diretorio in diretorios_comuns):
                logger.info(f"Falso Positivo Descartado (Site Encontrado): {nome_empresa} -> {url}")
                return True
        return False
    except Exception as e:
        logger.warning(f"Buscador falhou para {nome_empresa} (Rate Limit). Descartando lead por segurança: {e}")
        return True # Retornamos True para fingir que tem site e DESCARTAR o lead. Garantia de 100% de qualidade.

def buscar_empresas_sem_site(state: AgentState) -> Dict[str, Any]:
    cidade = state["cidade"]
    nicho_escolhido = state["nicho_alvo"]
    tag_osm = NICHOS_LUCRATIVOS.get(nicho_escolhido, '"amenity"="restaurant"')
    
    logger.info(f"Iniciando prospecção B2B de '{nicho_escolhido}' em '{cidade}'...")
    
    query = f"""
    [out:json][timeout:{Config.TIMEOUT_QUERY_DB}];
    area[name="{cidade}"]->.searchArea;
    (
      node[{tag_osm}](area.searchArea);
      way[{tag_osm}](area.searchArea);
      relation[{tag_osm}](area.searchArea);
    );
    out tags;
    """
    
    url = "https://overpass.osm.ch/api/interpreter"
    headers = {'User-Agent': Config.USER_AGENT}
    
    try:
        with criar_sessao_resiliente() as sessao:
            response = sessao.post(url, data={'data': query}, headers=headers, timeout=Config.TIMEOUT_HTTP_LOCAL)
            response.raise_for_status() 
            dados = response.json()
    except Exception as e:
        logger.critical(f"Falha crítica na extração de rede: {e}")
        return {"leads_encontrados": [], "erro": "falha_extracao"}

    leads: List[Lead] = []
    elementos = dados.get("elements", [])
    logger.info(f"{len(elementos)} estabelecimentos mapeados. Aplicando Filtro Implacável...")
    
    for elemento in elementos:
        tags = elemento.get("tags", {})
        nome = str(tags.get("name", "")).strip()
        telefone = str(tags.get("phone", "") or tags.get("contact:phone", "")).strip()
        site_osm = str(tags.get("website", "") or tags.get("contact:website", "")).strip()
        
        if nome and telefone and not site_osm and len(telefone) >= 8:
            
            tem_site_na_web = checar_falso_positivo_duckduckgo(nome, cidade)
            time.sleep(2.5) # Intervalo obrigatório para não ser bloqueado pelo DuckDuckGo
            
            if not tem_site_na_web:
                busca_url = urllib.parse.quote(f"{nome} {cidade} Switzerland")
                leads.append({
                    "nome": nome,
                    "telefone": telefone,
                    "nicho": nicho_escolhido,
                    "link_investigacao": f"https://www.google.com/maps/search/?api=1&query={busca_url}"
                })
                
                if len(leads) >= 5:
                    break
            
    arquivo_salvo = salvar_leads_csv(leads, cidade, nicho_escolhido) if leads else ""
    return {"leads_encontrados": leads, "arquivo_salvo": arquivo_salvo, "erro": ""}

workflow = StateGraph(AgentState)
workflow.add_node("extrator_de_leads", buscar_empresas_sem_site)
workflow.set_entry_point("extrator_de_leads")
workflow.add_edge("extrator_de_leads", END)
agente_prospeccao = workflow.compile()