import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler
from typing import Dict, Optional, Union

import requests
import telegram
from dotenv import load_dotenv
from telegram.ext import Filters, CommandHandler, MessageHandler, Updater
from telegram import ReplyKeyboardMarkup

load_dotenv()

TELEGRAM_TOKEN: Optional[str] = os.getenv('TELEGRAM_TOKEN')
ADMIN_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')

TRACKED_IDS = {
    'Blood and Thunder': 49377146,
    'King Magenta': 420475855,
    'Cergx': 125253635
}

RETRY_TIME: int = 600
MATCH_ENDPOINT: str = 'https://api.opendota.com/api/matches/'
PLAYER_ENDPOINT: str = 'https://api.opendota.com/api/players/'
PERIODS_DICT: Dict[str, int] = {
    'последний день': 1,
    'последние три дня': 3,
    'последнюю неделю': 7,
    'последний месяц': 28,
    'последние полгода': 183,
    'всё время': 5110,
}
WCLOUD_MIN_WORD_LEN: str = 4
WCLOUD_OUTPUT_WORDS_AMOUNT: str = 7

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


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


def parse_player_info(response: Dict) -> Dict:
    """Принимает объект юзера, возвращает словарь с текстом и URL аватара."""
    if response.get('profile') is None:
        raise KeyError('Отсутствует профиль с данным ID!')

    username = response.get('profile').get('personaname')
    if username is None:
        raise KeyError('В профиле нет personaname!')

    mmr_estimate = response.get('mmr_estimate')
    if mmr_estimate is None:
        raise KeyError('В профиле нет mmr_estimate.')

    estimate = mmr_estimate.get('estimate')
    if estimate is None:
        raise KeyError('В профиле нет estimate.')

    return {
        'text': f'Игрок {username}: оценочный MMR - {estimate}.',
        'avatar_url': response.get('profile').get('avatarfull')
    }


def get_win_loss_count(accout_id: int) -> Dict[str, Dict[str, int]]:
    """Принимает account_id, возвращает словарь с объектами винрейта."""
    winrates_periods: Dict[str, Dict[str, int]] = {}

    for period, days in PERIODS_DICT.items():
        request_params: Dict[str, Union[str, Dict]] = {
            'url': PLAYER_ENDPOINT + str(accout_id) + '/wl',
            'params': {'date': days}
        }
        response = requests.get(**request_params)
        if check_response(response):
            winrates_periods[period] = response.json()

    return winrates_periods


def parse_win_loss_count(winrates_periods: Dict[str, Dict[str, int]]) -> str:
    """Принимает словарь объектов винрейта, возвращает сообщение."""
    message: str = ''

    for period, winloss_dict in winrates_periods.items():
        win: int = winloss_dict['win']
        lose: int = winloss_dict['lose']
        try:
            winrate: str = f'{win / (win + lose):.2%}'
            message += (f'За {period}:\nВинрейт: {winrate}.\n'
                        f'Побед - {win}, поражений - {lose}.\n'
                        f'Всего игр: {win + lose}.\n\n')
        except ZeroDivisionError:
            message += (f'За {period} сыграно 0 игр.\n\n')

    return message


def get_last_game_object(account_id: int):
    """Получает id игрока, возвращает объект последней игры."""
    response = requests.get(
        url=PLAYER_ENDPOINT + str(account_id) + '/recentMatches')
    check_response(response)
    match_object = get_match_info(response.json()[0]['match_id'])
    print(match_object)


def parse_wordcloud_object(player_words_raw: Dict) -> str:
    """Получает объект вордклауда, возвращает список слов.

    Из всех слов удаляет слова с длиной меньше
    WCLOUD_MIN_WORD_LEN, сортирует по убыванию по частоте использования,
    возвращает строку из WCLOUD_OUTPUT_WORDS_AMOUNT слов.
    """
    w_filtered = dict(filter(
        lambda item: len(item[0]) > WCLOUD_MIN_WORD_LEN,
        player_words_raw.items()
    ))

    w_sorted = dict(sorted(
        w_filtered.items(), key=lambda item: item[1], reverse=True
    ))
    logger.debug(list(w_sorted.items())[:10])

    return (', ').join(list(w_sorted.keys())[:WCLOUD_OUTPUT_WORDS_AMOUNT])


def get_wordcloud_msg(account_id: int):
    """Получает id игрока, возвращает сообщение из вордклауда."""
    response = requests.get(
        url=PLAYER_ENDPOINT + str(account_id) + '/wordcloud')
    check_response(response)

    player_words_raw = response.json()['my_word_counts']
    others_words_raw = response.json()['all_word_counts']
    return (f'Чаще всего ты писал такие слова: '
            f'{parse_wordcloud_object(player_words_raw)}.\n\n'
            f'Чаще всего ты видел такие слова: '
            f'{parse_wordcloud_object(others_words_raw)}.')


def check_tokens() -> bool:
    """Проверяет доступность обязательных переменных окружения."""
    return all([TELEGRAM_TOKEN, ADMIN_CHAT_ID])


def check_response(response) -> bool:
    """Проверяет статус ответа, если != 200, поднимает исключение."""
    if response.status_code != HTTPStatus.OK:
        raise ValueError(f'Ответ со статусом "{response.status_code}".')
    logger.debug('Бот сделал запрос к API и получил ответ со статусом '
                 f'"{response.status_code}".')
    return True


def get_check_tokens_failure_msg() -> str:
    """Возвращает сообщение об ошибке со списком ненайденных переменных."""
    missing_vars: list = []
    if not TELEGRAM_TOKEN:
        missing_vars.append('TELEGRAM_TOKEN')
    if not ADMIN_CHAT_ID:
        missing_vars.append('TELEGRAM_CHAT_ID')

    first_line = 'Не найдена обязательная переменная'
    if len(missing_vars) > 1:
        first_line = 'Не найдены обязательные переменные'

    return (f'{first_line} окружения: {missing_vars}. '
            '\nПрограмма принудительно остановлена.')


def wake_up(update, context) -> None:
    """При получении команды /start здоровается."""
    chat = update.effective_chat
    name = update.message.chat.first_name
    button = ReplyKeyboardMarkup([list(TRACKED_IDS.keys())])

    context.bot.send_message(
        chat_id=chat.id,
        text=(f'Привет, {name}! Введи свой Steam32 account ID, чтобы увидеть '
              'статистику по оценочному MMR и винрейту.'),
        reply_markup=button
    )


def mmr_winrate_info(update, context) -> None:
    """При получении сообщения пытается собрать инфу по присланному SteamID."""
    chat = update.effective_chat

    try:
        full_name = (f'{update.message.chat.first_name} '
                     f'{update.message.chat.last_name}')
        incoming_message = update.message.text
        account_id = TRACKED_IDS[incoming_message] if incoming_message in TRACKED_IDS.keys() else int(incoming_message)

        message_to_send = f'Нам пишет {full_name}!'
        logger.info(message_to_send)
        context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=message_to_send
        )

        player_info = get_player_info(account_id)
        message_object = parse_player_info(player_info)

        avatar_url = message_object.get('avatar_url')

        if avatar_url:
            context.bot.send_photo(
                chat_id=chat.id,
                photo=avatar_url,
                caption=message_object.get('text')
            )

        else:
            context.bot.send_message(
                chat_id=chat.id,
                text=message_object.get('text')
            )

        logger.info(message_object.get('text'))

        context.bot.send_message(
            chat_id=chat.id,
            text=get_wordcloud_msg(account_id)
        )

        wl_count = get_win_loss_count(account_id)
        wl_message = parse_win_loss_count(wl_count)
        context.bot.send_message(
            chat_id=chat.id,
            text=wl_message
        )
        logger.info(wl_message)

    except Exception as error:
        context.bot.send_message(
            chat_id=chat.id,
            text=f'Возникла проблема: {error}.'
        )
        logger.info(error)


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical(get_check_tokens_failure_msg())
        sys.exit()
    logger.info('Переменные среды найдены. Инициализация...')

    updater = Updater(token=TELEGRAM_TOKEN)
    updater.dispatcher.add_handler(CommandHandler('start', wake_up))
    updater.dispatcher.add_handler(
        MessageHandler(
            Filters.text,
            mmr_winrate_info
        )
    )

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
