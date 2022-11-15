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
ENDPOINT: str = 'https://api.opendota.com/api/matches/'

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
    print(message)


def get_api_answer(match_id: int) -> Dict:
    """Принимает match_id, делает запрос к API, возвращает словарь."""
    request_params: Dict = {
        'url': ENDPOINT + str(match_id),
    }
    response = requests.get(**request_params)

    if response.status_code != HTTPStatus.OK:
        raise Exception(f'Ответ со статусом "{response.status_code}"')

    logger.debug('Бот сделал запрос к API и получил ответ со статусом '
                 f'"{response.status_code}".')
    return response.json()


def check_tokens() -> bool:
    """Проверяет доступность обязательных переменных окружения."""
    return all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


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
    match_info = get_api_answer(6860559663)
    send_message(bot, match_info)

if __name__ == '__main__':
    main()
