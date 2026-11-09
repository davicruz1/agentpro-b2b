import time
from flask import Flask, render_template, request, jsonify
from agente_leads import buscar_empresas_sem_site
from agente_copywriter import inicializar_ia, gerar_pitch_vendas

app = Flask(__name__)

ia_client = inicializar_ia()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/prospectar', methods=['POST'])
def prospectar():
    dados = request.json
    cidade = dados.get('cidade')
    nicho = dados.get('nicho')

    estado_inicial = {
        "cidade": cidade, 
        "nicho_alvo": nicho, 
        "leads_encontrados": [], 
        "erro": "", 
        "arquivo_salvo": ""
    }
    
    resultado_extracao = buscar_empresas_sem_site(estado_inicial)

    if resultado_extracao.get("erro"):
        return jsonify({"erro": resultado_extracao["erro"]}), 500

    leads = resultado_extracao['leads_encontrados'][:5]
    resultados_finais = []

    for lead in leads:
        pitch = gerar_pitch_vendas(lead, ia_client)
        resultados_finais.append({
            "nome": lead['nome'],
            "telefone": lead['telefone'],
            "link_maps": lead.get('link_investigacao', '#'),
            "mensagem": pitch['mensagem'],
            "link_whatsapp": pitch['link_whatsapp']
        })
        # INTERVALO DE SEGURANÇA: 4 segundos entre cada chamada para não tomar block do Google
        time.sleep(4) 

    return jsonify(resultados_finais)

if __name__ == '__main__':
    app.run(debug=True, port=5000)