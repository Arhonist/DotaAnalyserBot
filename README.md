# DotaAnalyserBot 
 

## Описание 
 

Telegram-бот, при получении Steam32 ID сообщающий информацию об оценочном MMR игрока в Dota 2, информацию о винрейте и количестве сыгранных игр за разные периоды времени, а также вордклауд - наиболее часто используемые/виденные игроком слова в текстовом чате. 
 

## Стек технологий 
 

Проект использует библиотеки python-telegram-bot 13.7, python-dotenv 0.19.0, requests 2.26.0. Бот осуществляет запросы к Open Dota API для получения информации о профиле игрока.  
 

## Как запустить проект: 
 

Клонировать репозиторий и перейти в него в командной строке: 
 

``` 

git clone git@github.com:Arhonist/DotaAnalyserBot.git

``` 

 

``` 

cd DotaAnalyserBot

``` 

 

Cоздать и активировать виртуальное окружение: 

 

``` 

python -m venv env 

``` 

Для Windows:

``` 

source venv/Scripts/activate 

``` 

Для Linux:

``` 

source env/bin/activate

``` 

Установить зависимости из файла requirements.txt: 

 

``` 

python -m pip install --upgrade pip 

``` 

 

``` 

pip install -r requirements.txt 

``` 

Поместить в папку проекта файл .env с переменными TELEGRAM_TOKEN и TELEGRAM_CHAT_ID, где:
``` 
TELEGRAM_TOKEN - токен телеграм-бота
``` 
``` 
TELEGRAM_CHAT_ID - ID чата с администратором бота.
``` 


Запустить проект: 

 

``` 

python danalyserbot.py 

``` 
