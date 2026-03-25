
import json
import os

original_path = r'C:\Users\User\Downloads\Flujo Customer Service 1.1.json'
target_path = r'C:\Users\User\Downloads\Maxi_IA_v3.1_PRO.json'

with open(original_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

data['name'] = 'Maxi IA v3.1 PRO'
data['id'] = 1757617547764702

for node in data['workflow']:
    # Fix Intro
    if node['id'] == 'e9d8c8':
        node['data']['payload'][0]['message']['text'] = '🤖 ¡Hola! Bienvenido a Maxi IA.\n\nSoy tu asistente inteligente y voy a procesar tu consulta de inmediato.'
    
    # Fix Legal
    if node['id'] == 'ce4326':
        node['data']['payload'][0]['message']['text'] = 'Usted se está comunicando con Maxitransfers a través de WhatsApp... [Script A1 IA v2.2]. Su seguridad es nuestra prioridad.'
    
    # Fix Hours (Always open)
    if node['id'] == '5ad4be':
        for day in node['data']['times']:
            day['startTime'] = '00:00'
            day['endTime'] = '23:59'
            day['disabled'] = False

    # Fix Orquestador Node placeholder
    if node['id'] == '699954':
        node['data']['question']['text'] = '⚙️ [CONFIGURACIÓN REQUERIDA]: Reemplaza este nodo por el AI Agent \"ORQUESTADOR v2.2\". Guarda el resultado en \"intended_path\".'

    # Fix Estatus Node placeholder
    if node['id'] == 'af9cdd':
        node['data']['question']['text'] = '⚙️ [CONFIGURACIÓN REQUERIDA]: Reemplaza este nodo por el Agente de Estatus.'

# Write output
with open(target_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print(f"File created successfully at {target_path}")
