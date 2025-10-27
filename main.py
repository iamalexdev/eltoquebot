import telebot
import requests
from datetime import datetime, timedelta
import pytz
from typing import Dict, List

# Configuración inicial
TOKEN = '8460409787:AAHN6uK7UBqJ3PJC6LMs3vEk2L5JNoeeCeg'
API_URL = "https://tasas.eltoque.com/v1/trmi"
API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc2MTE0NzQzMSwianRpIjoiMTc4ZGIyZWYtNWIzNy00MzJhLTkwYTktNTczZDBiOGE2N2ViIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjY4ZjgyZjM1ZTkyYmU3N2VhMzAzODJhZiIsIm5iZiI6MTc2MTE0NzQzMSwiZXhwIjoxNzkyNjgzNDMxfQ.gTIXoSudOyo99vLLBap74_5UfdSRdOLluXekb0F1cPg"

# Lista de grupos autorizados
GRUPOS_AUTORIZADOS = [
    -4958319706,
]

bot = telebot.TeleBot(TOKEN)

def obtener_tasas_eltoque() -> Dict:
    """
    Obtiene las tasas actuales desde la API de ElToque (últimos 3 minutos)
    """
    try:
        # Preparar fechas (últimos 3 minutos)
        fecha_actual = datetime.now()
        fecha_desde = fecha_actual - timedelta(minutes=3)
        
        # Formatear fechas para la API
        date_from = fecha_desde.strftime("%Y-%m-%d %H:%M:%S").replace(" ", "%20")
        date_to = fecha_actual.strftime("%Y-%m-%d %H:%M:%S").replace(" ", "%20")
        
        url = f"https://tasas.eltoque.com/v1/trmi?date_from={date_from}&date_to={date_to}"
        
        headers = {
            'accept': '*/*',
            'Authorization': f'Bearer {API_TOKEN}'
        }
        
        print(f"🔍 Solicitando tasas desde: {fecha_desde} hasta: {fecha_actual}")
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        datos = response.json()
        print(f"✅ Datos obtenidos: {datos}")
        return datos
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener tasas: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

def convertir_a_hora_cuba(utc_hour: int, utc_minutes: int, utc_seconds: int) -> str:
    """
    Convierte hora UTC a hora de Cuba (Cuba Standard Time - UTC-5)
    """
    try:
        # Crear objeto datetime en UTC
        utc_time = datetime.utcnow().replace(
            hour=utc_hour, 
            minute=utc_minutes, 
            second=utc_seconds
        )
        
        # Definir timezone de Cuba
        cuba_tz = pytz.timezone('America/Havana')
        
        # Asumir que la hora de la API es UTC y convertir a Cuba
        utc_time = pytz.utc.localize(utc_time)
        cuba_time = utc_time.astimezone(cuba_tz)
        
        return cuba_time.strftime("%H:%M:%S")
    except Exception as e:
        print(f"⚠️ Error en conversión horaria: {e}")
        return f"{utc_hour:02d}:{utc_minutes:02d}:{utc_seconds:02d} (UTC)"

def formatear_mensaje_tasas(datos_api: Dict) -> str:
    """
    Formatea un mensaje atractivo con las tasas
    """
    if not datos_api or 'tasas' not in datos_api:
        return "❌ No se pudieron obtener las tasas en este momento. Intenta nuevamente en unos segundos."
    
    tasas = datos_api['tasas']
    fecha = datos_api.get('date', 'N/A')
    hora_utc = datos_api.get('hour', 0)
    minutos_utc = datos_api.get('minutes', 0)
    segundos_utc = datos_api.get('seconds', 0)
    
    # Convertir a hora de Cuba
    hora_cuba = convertir_a_hora_cuba(hora_utc, minutos_utc, segundos_utc)
    
    # Crear mensaje formateado
    mensaje = "💹 *TASAS ACTUALIZADAS*\n\n"
    mensaje += "📊 *Tasas disponibles:*\n"
    mensaje += "┌───────────────────────┐\n"
    
    # Lista de tasas en orden específico
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
    mensaje += f"⏰ *Hora Cuba:* `{hora_cuba}`\n"
    mensaje += f"🕒 *Hora UTC:* `{hora_utc:02d}:{minutos_utc:02d}:{segundos_utc:02d}`\n\n"
    mensaje += "💡 _Datos proporcionados por eltoque.com_"
    
    return mensaje

def es_grupo_autorizado(chat_id: int) -> bool:
    """
    Verifica si el chat está en la lista de grupos autorizados
    """
    return chat_id in GRUPOS_AUTORIZADOS

# Manejo de comandos
@bot.message_handler(commands=['start'])
def comando_start(message):
    if message.chat.type in ['group', 'supergroup']:
        if not es_grupo_autorizado(message.chat.id):
            bot.reply_to(message, "❌ Este grupo no está autorizado para usar este bot.")
            return
    
    welcome_text = """
💹 *BOT DE TASAS DE CAMBIO* 🤖

*✨ FUNCIONALIDADES:*

✅ Tasas via eltoque.com
✅ Actualizaciones frecuentes
✅ Acceso controlado por grupos

🚀 *¡Usa /tasas para ver las tasas ahora!*

_By Alex Gonzalez_
    """
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['tasas'])
def comando_tasas(message):
    # Verificar autorización para grupos
    if message.chat.type in ['group', 'supergroup']:
        if not es_grupo_autorizado(message.chat.id):
            bot.reply_to(message, "❌ Este grupo no está autorizado para usar este bot.")
            return
    
    # Enviar mensaje de "escribiendo..."
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Obtener y mostrar tasas
    datos = obtener_tasas_eltoque()
    mensaje = formatear_mensaje_tasas(datos)
    
    bot.reply_to(message, mensaje, parse_mode='Markdown')

@bot.message_handler(commands=['agregar'])
def comando_grupos(message):
    if message.chat.type == 'private':
        info_grupos = """
*Para agregar el bot a tu grupo:*

1. Añade @elToqueP_bot como administrador
2. Asegúrate de que tenga permisos para enviar mensajes
3. El bot debe estar en la lista de grupos autorizados

*Contacta al administrador para solicitar acceso. @Alex_GlezRM*
        """
        bot.reply_to(message, info_grupos, parse_mode='Markdown')
    else:
        bot.reply_to(message, "Este comando solo está disponible en chats privados.")

@bot.message_handler(commands=['help'])
def comando_help(message):
    help_text = """
🆘 *Ayuda del Bot de Tasas*

*Comandos disponibles:*
/start - Iniciar el bot
/tasas - Obtener tasas de cambio actuales
/agregar - Agregalo a tu grupo
/help - Mostrar esta ayuda

*Características:*
• Tasas en tiempo real
• Actualizaciones frecuentes
• Formato claro y organizado
• Compatible con grupos autorizados

*Soporte:* Contacta al administrador para problemas o sugerencias.
    """
    bot.reply_to(message, help_text, parse_mode='Markdown')

# Manejo cuando el bot es agregado a un grupo
@bot.message_handler(content_types=['new_chat_members'])
def nuevo_miembro(message):
    for new_member in message.new_chat_members:
        if new_member.id == bot.get_me().id:
            if es_grupo_autorizado(message.chat.id):
                welcome_msg = """
¡Hola! 🤖 Gracias por agregarme al grupo.

Puedes usar el comando /tasas para obtener las tasas de cambio actualizadas.

Usa /help para ver todos los comandos disponibles.
                """
                bot.reply_to(message, welcome_msg)
            else:
                bot.reply_to(message, "❌ Este grupo no está autorizado. Seré removido.")
                # Opcional: el bot puede salirse automáticamente
                # bot.leave_chat(message.chat.id)

# Función principal
if __name__ == '__main__':
    print("🤖 Bot de Tasas iniciado...")
    print(f"📍 Grupos autorizados: {len(GRUPOS_AUTORIZADOS)}")
    print("📊 Comando /tasas disponible")
    print("⏰ Obteniendo tasas de los últimos 3 minutos...")
    
    try:
        bot.polling(none_stop=True, interval=1, timeout=60)
    except Exception as e:
        print(f"Error: {e}")
