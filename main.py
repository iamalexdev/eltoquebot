
import telebot
import requests
from datetime import datetime, timedelta
import pytz
from typing import Dict, List

# Configuración inicial
TOKEN = '8460409787:AAHN6uK7UBqJ3PJC6LMs3vEk2L5JNoeeCeg'  # Reemplaza con tu token de BotFather
API_URL = "https://tasas.eltoque.com/v1/trmi"
API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc2MTE0NzQzMSwianRpIjoiMTc4ZGIyZWYtNWIzNy00MzJhLTkwYTktNTczZDBiOGE2N2ViIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjY4ZjgyZjM1ZTkyYmU3N2VhMzAzODJhZiIsIm5iZiI6MTc2MTE0NzQzMSwiZXhwIjoxNzkyNjgzNDMxfQ.gTIXoSudOyo99vLLBap74_5UfdSRdOLluXekb0F1cPg"

# Lista de grupos autorizados (reemplaza con los IDs de tus grupos)
GRUPOS_AUTORIZADOS = [
    -4958319706,  # Ejemplo: ID de grupo 1
]

bot = telebot.TeleBot(TOKEN)

def obtener_tasas_eltoque() -> Dict:
    """
    Obtiene las tasas actuales desde la API de ElToque
    """
    try:
        # Preparar fechas (últimas 24 horas)
        fecha_actual = datetime.now()
        fecha_desde = fecha_actual - timedelta(hours=24)
        
        # Formatear fechas para la API
        date_from = fecha_desde.strftime("%Y-%m-%d %H:%M:%S").replace(" ", "%20")
        date_to = fecha_actual.strftime("%Y-%m-%d %H:%M:%S").replace(" ", "%20")
        
        url = f"https://tasas.eltoque.com/v1/trmi?date_from={date_from}&date_to={date_to}"
        
        headers = {
            'accept': '*/*',
            'Authorization': f'Bearer {API_TOKEN}'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener tasas: {e}")
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
        
        # Definir timezone de Cuba (normalmente UTC-5, puede variar con horario de verano)
        cuba_tz = pytz.timezone('America/Havana')
        
        # Asumir que la hora de la API es UTC y convertir a Cuba
        utc_time = pytz.utc.localize(utc_time)
        cuba_time = utc_time.astimezone(cuba_tz)
        
        return cuba_time.strftime("%H:%M:%S")
    except Exception as e:
        print(f"Error en conversión horaria: {e}")
        return f"{utc_hour}:{utc_minutes}:{utc_seconds} (UTC)"

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
    
    # Convertir a hora de Cuba
    hora_cuba = convertir_a_hora_cuba(hora_utc, minutos_utc, segundos_utc)
    
    # Crear mensaje formateado
    mensaje = "💹 *TASAS DE CAMBIO ACTUALIZADAS* 💹\n\n"
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
            mensaje += f"│ *{nombre}:* {valor} CUP │\n"
    
    mensaje += "└───────────────────────┘\n\n"
    mensaje += f"📅 *Fecha:* {fecha}\n"
    mensaje += f"⏰ *Hora UTC:* {hora_utc:02d}:{minutos_utc:02d}:{segundos_utc:02d}\n\n"
    mensaje += "💡 _Datos proporcionados por eltoque.com"
    
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
            bot.reply_to(message, "❌ Este grupo no está autorizado para usar este bot. Por Favor contacte con @Alex_GlezRM")
            return
    
    welcome_text = """
🤖 *Bot de Tasas de Cambio*
*Funcionalidades:*
• Tasas en tiempo real desde ElToque
• Integración a grupos por petición
    """
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['tasas'])
def comando_tasas(message):
    # Verificar autorización para grupos
    if message.chat.type in ['group', 'supergroup']:
        if not es_grupo_autorizado(message.chat.id):
            bot.reply_to(message, "❌ Este grupo no está autorizado para usar este bot. Por Favor contacte con @Alex_GlezRM")
            return
    
    # Enviar mensaje de "escribiendo..."
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Obtener y mostrar tasas
    datos = obtener_tasas_eltoque()
    mensaje = formatear_mensaje_tasas(datos)
    
    bot.reply_to(message, mensaje, parse_mode='Markdown')

@bot.message_handler(commands=['grupos'])
def comando_grupos(message):
    if message.chat.type == 'private':
        info_grupos = """
👥 *Grupos Autorizados:*
        
*Para agregar el bot a tu grupo:*
1. Añade @elToqueP_bot como administrador
2. Asegúrate de que tenga permisos para enviar mensajes
3. Contactar a @Alex_GlezRM para añadir tu grupo

*Contacta al administrador para solicitar acceso.*
        """.format(
            "\n".join([f"• Grupo {i+1}" for i in range(len(GRUPOS_AUTORIZADOS))]),
            bot.get_me().username
        )
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
/grupos - Información sobre grupos autorizados
/help - Mostrar esta ayuda

*Características:*
• Tasas en tiempo real
• Actualizaciones frecuentes

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
    
    try:
        bot.polling(none_stop=True, interval=1, timeout=60)
    except Exception as e:
        print(f"Error: {e}")
