import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler
from typing import Dict, List, Optional

from pprint import pprint
import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN: Optional[str] = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME: int = 600
MATCH_ENDPOINT: str = 'https://api.opendota.com/api/matches/'
PLAYER_ENDPOINT: str = 'https://api.opendota.com/api/players/'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot: telegram.bot.Bot, message: Dict) -> None:
    """Получает бота и сообщение на вход. Отправляет сообщение пользователю."""
    #try:
    #    logger.info('Бот пытается отправить сообщение.')
    #    bot.send_message(TELEGRAM_CHAT_ID, message)
    #    logger.info('Сообщение успешно отправлено.')
    #except telegram.error.TelegramError as error:
    #    logger.error(f'Не удалась отправка сообщения. Ошибка: "{error}".')
    #print(message)


def get_match_info(match_id: int) -> Dict:
    """Принимает match_id, возвращает объект матча."""
    response = requests.get(url=MATCH_ENDPOINT + str(match_id))
    check_response(response)
    return response.json()


def get_player_info(account_id: int) -> Dict:
    """Принимает account_id, возвращает объект профиля."""
    response = requests.get(url=PLAYER_ENDPOINT + str(account_id))
    check_response(response)
    return response.json()


def parse_player_info(response: Dict) -> str:
    """Принимает объект юзера, парсит, возвращает сообщение о профиле."""
    username = response.get('profile').get('personaname')
    if username is None:
        raise KeyError('В объекте профиля нет personaname!')
    estimated_mmr = response.get('mmr_estimate').get('estimate')
    if estimated_mmr is None:
        raise KeyError('В ответе нет estimated_mmr!')
    return (f'Игрок {username}: оценочный MMR - {estimated_mmr}.')

def check_tokens() -> bool:
    """Проверяет доступность обязательных переменных окружения."""
    return all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def check_response(response) -> None:
    """Проверяет статус ответа, если != 200, поднимает исключение."""
    if response.status_code != HTTPStatus.OK:
        raise ValueError(f'Ответ со статусом "{response.status_code}".')
    logger.debug('Бот сделал запрос к API и получил ответ со статусом '
                 f'"{response.status_code}".')    


def get_check_tokens_failure_msg() -> str:
    """Возвращает сообщение об ошибке со списком ненайденных переменных."""
    missing_vars = []
    if not TELEGRAM_TOKEN:
        missing_vars.append('TELEGRAM_TOKEN')
    if not TELEGRAM_CHAT_ID:
        missing_vars.append('TELEGRAM_CHAT_ID')

    first_line = 'Не найдена обязательная переменная'
    if len(missing_vars) > 1:
        first_line = 'Не найдены обязательные переменные'

    return (f'{first_line} окружения: {missing_vars}. '
            '\nПрограмма принудительно остановлена.')


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical(get_check_tokens_failure_msg())
        sys.exit()
    logger.info('Переменные среды найдены. Инициализация...')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    player_info = get_player_info(125253635)
    print(parse_player_info(player_info))


if __name__ == '__main__':
    main()
