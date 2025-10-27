import telebot
import requests
from datetime import datetime, timedelta
import pytz
from typing import Dict, List

# Configuración inicial
TOKEN = '8460409787:AAHN6uK7UBqJ3PJC6LMs3vEk2L5JNoeeCeg'
API_URL = "https://tasas.eltoque.com/v1/trmi"
API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc2MTE0NzQzMSwianRpIjoiMTc4ZGIyZWYtNWIzNy00MzJhLTkwYTktNTczZDBiOGE2N2ViIiwidHlwZCI6ImFjY2VzcyIsInN1YiI6IjY4ZjgyZjM1ZTkyYmU3N2VhMzAzODJhZiIsIm5iZiI6MTc2MTE0NzQzMSwiZXhwIjoxNzkyNjgzNDMxfQ.gTIXoSudOyo99vLLBap74_5UfdSRdOLluXekb0F1cPg"

# Lista de grupos autorizados
GRUPOS_AUTORIZADOS = [-1003226018534]

# Tu user ID como administrador
ADMIN_ID = 1853800972  # Cambia esto por tu user ID real

# Variable para almacenar la URL de la imagen
imagen_url = None

bot = telebot.TeleBot(TOKEN)

def obtener_tasas_eltoque() -> Dict:
    """
    Obtiene las tasas actuales desde la API de ElToque (últimas 24 horas)
    """
    try:
        # Obtener hora actual en Cuba
        cuba_tz = pytz.timezone('America/Havana')
        ahora_cuba = datetime.now(cuba_tz)
        
        # Calcular rango de 24 horas
        fecha_hasta = ahora_cuba
        fecha_desde = ahora_cuba - timedelta(hours=24)
        
        # Formatear fechas para la API
        date_from = fecha_desde.strftime("%Y-%m-%d %H:%M:%S").replace(" ", "%20")
        date_to = fecha_hasta.strftime("%Y-%m-%d %H:%M:%S").replace(" ", "%20")
        
        url = f"https://tasas.eltoque.com/v1/trmi?date_from={date_from}&date_to={date_to}"
        
        headers = {
            'accept': '*/*',
            'Authorization': f'Bearer {API_TOKEN}'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        print(f"❌ Error al obtener tasas: {e}")
        return None

def formatear_mensaje_tasas(datos_api: Dict) -> str:
    """
    Formatea un mensaje atractivo con las tasas
    """
    if not datos_api or 'tasas' not in datos_api:
        return "❌ No se pudieron obtener las tasas en este momento."
    
    tasas = datos_api['tasas']
    fecha = datos_api.get('date', 'N/A')
    hora_utc = datos_api.get('hour', 0)
    minutos_utc = datos_api.get('minutes', 0)
    segundos_utc = datos_api.get('seconds', 0)
    
    mensaje = "💹 *TASAS DEL DÍA*\n\n"
    mensaje += "📊 *Tasas disponibles:*\n"
    mensaje += "┌───────────────────────┐\n"
    
    tasas_ordenadas = [
        ("ECU", "💶 EUR"),
        ("USD", "💵 USD"),
        ("MLC", "💳 MLC"),
        ("USDT_TRC20", "🔷 USDT"),
        ("TRX", "⚡ TRX")
    ]
    
    for codigo, nombre in tasas_ordenadas:
        if codigo in tasas:
            valor = tasas[codigo]
            mensaje += f"│ *{nombre}:* `{valor}` CUP\n"
    
    mensaje += "└───────────────────────┘\n\n"
    mensaje += f"📅 *Fecha:* `{fecha}`\n"
    mensaje += f"🕒 *Hora de Actualización:* `{hora_utc:02d}:{minutos_utc:02d}:{segundos_utc:02d}`\n\n"
    mensaje += "📢 *Actualizado diariamente a las 7:00 AM*\n"
    mensaje += "💡 _Datos proporcionados por eltoque.com_"
    
    return mensaje

def es_grupo_autorizado(chat_id: int) -> bool:
    return chat_id in GRUPOS_AUTORIZADOS

def es_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# Comando start
@bot.message_handler(commands=['start'])
def comando_start(message):
    if message.chat.type in ['group', 'supergroup']:
        if not es_grupo_autorizado(message.chat.id):
            bot.reply_to(message, "❌ Grupo no autorizado.")
            return
    
    if es_admin(message.from_user.id):
        mensaje = """
🤖 *Bot de Tasas - MODO ADMIN* 💹

*Comandos disponibles:*
/tasas - Ver tasas del día
/link [url] - Configurar URL de imagen
/imagen - Enviar imagen configurada

⚠️ *Primero configura la imagen con /link*
        """
    else:
        mensaje = """
🤖 *Bot de Tasas* 💹

*Comandos disponibles:*
/tasas - Ver tasas del día
/imagen - Ver imagen de tasas
        """
    
    bot.reply_to(message, mensaje, parse_mode='Markdown')

# Comando tasas
@bot.message_handler(commands=['tasas'])
def comando_tasas(message):
    if message.chat.type in ['group', 'supergroup']:
        if not es_grupo_autorizado(message.chat.id):
            bot.reply_to(message, "❌ Grupo no autorizado.")
            return
    
    bot.send_chat_action(message.chat.id, 'typing')
    datos = obtener_tasas_eltoque()
    mensaje = formatear_mensaje_tasas(datos)
    bot.reply_to(message, mensaje, parse_mode='Markdown')

# Comando link - SOLO ADMIN
@bot.message_handler(commands=['link'])
def comando_link(message):
    global imagen_url
    
    if not es_admin(message.from_user.id):
        bot.reply_to(message, "❌ Comando solo para administrador.")
        return
    
    texto = message.text.strip()
    
    if texto == '/link':
        if imagen_url:
            bot.reply_to(message, f"🔗 *URL actual:*\n`{imagen_url}`", parse_mode='Markdown')
        else:
            bot.reply_to(message, "⚠️ *No hay URL configurada.*\nUsa: `/link https://tu-imagen.com/trmi.png`", parse_mode='Markdown')
        return
    
    partes = texto.split(' ', 1)
    if len(partes) < 2:
        bot.reply_to(message, "❌ Formato: `/link https://tu-imagen.com/trmi.png`", parse_mode='Markdown')
        return
    
    nueva_url = partes[1].strip()
    
    if not (nueva_url.startswith('http://') or nueva_url.startswith('https://')):
        bot.reply_to(message, "❌ URL debe empezar con http:// o https://")
        return
    
    imagen_url = nueva_url
    bot.reply_to(message, f"✅ *URL configurada!*\n`{imagen_url}`", parse_mode='Markdown')
    print(f"🔗 URL de imagen actualizada: {imagen_url}")

# Comando imagen
@bot.message_handler(commands=['imagen'])
def comando_imagen(message):
    global imagen_url
    
    if message.chat.type in ['group', 'supergroup']:
        if not es_grupo_autorizado(message.chat.id):
            bot.reply_to(message, "❌ Grupo no autorizado.")
            return
    
    if not imagen_url:
        bot.reply_to(message, "⚠️ *No hay imagen configurada.*\nEl administrador debe usar /link primero.")
        return
    
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    try:
        bot.send_photo(message.chat.id, imagen_url, caption="📊 TRMI - Tasas de Cambio")
        print(f"✅ Imagen enviada: {imagen_url}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error al enviar imagen: {e}")

# Comando help
@bot.message_handler(commands=['help'])
def comando_help(message):
    help_text = """
🆘 *Ayuda Rápida*

*Comandos:*
/tasas - Ver tasas del día
/imagen - Ver imagen de tasas
/help - Esta ayuda

*Para administrador:*
/link [url] - Configurar imagen
    """
    bot.reply_to(message, help_text, parse_mode='Markdown')

# Inicialización - Mensaje al admin
def notificar_admin():
    try:
        bot.send_message(
            ADMIN_ID, 
            "🤖 *Bot iniciado*\n\n⚠️ *Configura la imagen con:*\n`/link https://tu-imagen.com/trmi.png`\n\n*Luego usa /imagen para probar.*",
            parse_mode='Markdown'
        )
        print(f"✅ Notificación enviada al admin: {ADMIN_ID}")
    except Exception as e:
        print(f"❌ Error al notificar admin: {e}")

# Ejecutar bot
if __name__ == '__main__':
    print("🤖 Bot de Tasas iniciado...")
    print("📍 Esperando configuración de imagen...")
    
    # Notificar al admin que configure la imagen
    notificar_admin()
    
    try:
        bot.polling(none_stop=True, interval=1, timeout=60)
    except Exception as e:
        print(f"Error: {e}")
