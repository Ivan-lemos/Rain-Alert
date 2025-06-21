import os
import requests
from twilio.rest import Client
from twilio.http.http_client import TwilioHttpClient

# ---------------------------- CONSTANTES ------------------------------- #
OWM_ENDPOINT = "https://api.openweathermap.org/data/2.5/forecast" # Endpoint da API OpenWeatherMap
API_KEY = os.environ.get("OWM_API_KEY") # Chave da API OpenWeatherMap (obtida de variáveis de ambiente)
ACCOUNT_SID = "YOUR ACCOUNT SID" # SID da conta Twilio
AUTH_TOKEN = os.environ.get("AUTH_TOKEN") # Token de autenticação Twilio (obtido de variáveis de ambiente)

# Coordenadas da localização para a previsão do tempo (ex: Berna, Suíça)
LATITUDE = 46.947975
LONGITUDE = 7.447447

# ---------------------------- FUNÇÕES AUXILIARES ------------------------------- #

def get_weather_forecast(lat: float, lon: float, api_key: str, cnt: int = 4) -> dict:
    """Obtém a previsão do tempo para as próximas horas de uma localização específica.

    Args:
        lat (float): Latitude da localização.
        lon (float): Longitude da localização.
        api_key (str): Chave da API OpenWeatherMap.
        cnt (int): Número de blocos de 3 horas a serem retornados (padrão: 4, para 12 horas).

    Returns:
        dict: Um dicionário contendo os dados da previsão do tempo.

    Raises:
        requests.exceptions.RequestException: Se a requisição à API falhar.
    """
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "cnt": cnt,
    }
    response = requests.get(OWM_ENDPOINT, params=params)
    response.raise_for_status()  # Levanta uma exceção para erros de status HTTP
    return response.json()


def will_it_rain(weather_data: dict) -> bool:
    """Verifica se haverá chuva nas próximas horas com base nos dados da previsão.

    Considera que choverá se o código de condição meteorológica for menor que 700
    (indicando chuva, neve, tempestade, etc., em vez de condições claras ou nubladas).

    Args:
        weather_data (dict): Dados da previsão do tempo obtidos da API OpenWeatherMap.

    Returns:
        bool: True se houver previsão de chuva, False caso contrário.
    """
    for hour_data in weather_data["list"]:
        condition_code = hour_data["weather"][0]["id"]
        if int(condition_code) < 700:
            return True
    return False


def send_sms_alert(account_sid: str, auth_token: str, from_number: str, to_number: str, message_body: str) -> None:
    """Envia uma mensagem SMS usando o serviço Twilio.

    Args:
        account_sid (str): SID da conta Twilio.
        auth_token (str): Token de autenticação Twilio.
        from_number (str): Número de telefone Twilio remetente.
        to_number (str): Número de telefone do destinatário.
        message_body (str): O corpo da mensagem SMS.
    """
    # Configura o cliente HTTP para usar proxy se estiver definido no ambiente
    proxy_client = TwilioHttpClient()
    if 'https_proxy' in os.environ:
        proxy_client.session.proxies = {'https': os.environ['https_proxy']}

    client = Client(account_sid, auth_token, http_client=proxy_client)

    message = client.messages.create(
        body=message_body,
        from_=from_number,
        to=to_number
    )
    print(f"Status da mensagem SMS: {message.status}")


# ---------------------------- LÓGICA PRINCIPAL ------------------------------- #

if __name__ == "__main__":
    # Verifica se as chaves de API e tokens estão configurados
    if not API_KEY or not AUTH_TOKEN:
        print("Erro: As variáveis de ambiente OWM_API_KEY e AUTH_TOKEN devem ser configuradas.")
        print("Por favor, defina-as antes de executar o script.")
    else:
        try:
            # 1. Obter a previsão do tempo
            weather_data = get_weather_forecast(LATITUDE, LONGITUDE, API_KEY)

            # 2. Verificar se vai chover
            if will_it_rain(weather_data):
                # 3. Enviar alerta SMS se for chover
                # Substitua 'YOUR TWILIO VIRTUAL NUMBER' e 'YOUR TWILIO VERIFIED REAL NUMBER'
                # pelos seus números reais do Twilio.
                TWILIO_VIRTUAL_NUMBER = "YOUR TWILIO VIRTUAL NUMBER"
                TWILIO_VERIFIED_REAL_NUMBER = "YOUR TWILIO VERIFIED REAL NUMBER"
                
                sms_message = "Vai chover hoje. Lembre-se de levar um ☔️"
                send_sms_alert(ACCOUNT_SID, AUTH_TOKEN, TWILIO_VIRTUAL_NUMBER, TWILIO_VERIFIED_REAL_NUMBER, sms_message)
            else:
                print("Não há previsão de chuva para as próximas horas.")

        except requests.exceptions.RequestException as e:
            print(f"Erro ao conectar com a API do tempo: {e}")
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")


