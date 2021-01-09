import uuid

import psycopg2
from psycopg2 import sql

import config
import logger

connection = psycopg2.connect(config.DATABASE_URL, sslmode='require')

cursor = connection.cursor()


def create_user_table():
    try:
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS USERS
            (USER_ID INT NOT NULL,
            UUID UUID UNIQUE NOT NULL,
            IS_PREMIUM_USER BOOLEAN NOT NULL DEFAULT FALSE,
            PREMIUM_EXPIRED_DATE INT,
            CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""")
    except Exception:
        logger.critical('Создание таблицы для пользователей не выполнено')

    connection.commit()


def add_user(user_id):

    unique_id = str(uuid.uuid4())

    try:
        cursor.execute(
            'INSERT INTO USERS (USER_ID, UUID) VALUES (%s, %s);',
            (user_id, unique_id),
            )
    except Exception:
        logger.warning(f'Пользователь {user_id} не добавлен в таблицу')
    else:
        logger.info('Новый пользователь добавлен в таблицу')

    connection.commit()


def create_dictionary():

    try:
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS DICTIONARY
            (USER_ID INT NOT NULL,
            RU TEXT,
            EN TEXT,
            IS_LEARNED BOOLEAN,
            LEARNED_AT TIMESTAMP,
            CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_pair_en UNIQUE (USER_ID, EN),
            CONSTRAINT unique_pair_ru UNIQUE (USER_ID, RU));""")
    except Exception:
        logger.critical('Создание таблицы для слов не выполнено')

    connection.commit()


def add_word_to_dictionary(user_id, source_language, word):

    query = sql.SQL(
        'INSERT INTO DICTIONARY (USER_ID, {language}) VALUES (%s, %s)',
        ).format(language=sql.Identifier(source_language))

    try:
        cursor.execute(query, (user_id, word.lower()))
    except Exception:
        logger.warning('Добавление слова в словарь не выполнено')
    else:
        logger.info('Новое слово успешно добавлено в таблицу')

    connection.commit()
