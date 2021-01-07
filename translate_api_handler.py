import json

import config
import errors
import logger
import utils

GOOGLE_BASIC_URL = 'https://translation.googleapis.com/language/translate/v2'
YANDEX_BASIC_URL = 'https://translate.api.cloud.yandex.net/translate/v2'
ABBYY_BASIC_URL = 'https://developers.lingvolive.com/api/v1'


class Translate:
    def google(self, language_pair, text):

        url = GOOGLE_BASIC_URL + '?key=' + config.GOOGLE_API_KEY
        payload = ({
            'q': [text],
            'target': language_pair[0],
            'source': language_pair[1],
            'format': 'text',
            })
        headers = {
            'Content-Type': 'application/json',
            }

        response = utils.send_post_request(url, payload, headers)

        if utils.is_response_failed(response):
            return response

        return ParseTranslation.google(self, response.text)

    def yandex(self, language_pair, text):
        url = YANDEX_BASIC_URL + '/translate'
        payload = ({
            'folder_id': config.YANDEX_FOLDER_ID,
            'texts': [text],
            'targetLanguageCode': language_pair[0],
            'sourceLanguageCode': language_pair[1],
            })
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Api-Key {config.YANDEX_API_TOKEN}',
            }

        response = utils.send_post_request(url, payload, headers)

        if utils.is_response_failed(response):
            return response

        return ParseTranslation.yandex(self, response.text)

    def abbyy(self, language_pair, text):

        if utils.is_single_word(text):
            logger.info('Перевод слова - используем Abbyy')

            target_language = get_abbyy_language_code(language_pair[0])
            source_language = get_abbyy_language_code(language_pair[1])

            url = ABBYY_BASIC_URL + '/Minicard'
            query_parameters = {
                'text': text,
                'srcLang': source_language,
                'dstLang': target_language,
            }
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + config.ABBYY_API_TOKEN,
                }

            response = utils.send_get_request(url, query_parameters, headers)

            if utils.is_response_failed(response):
                logger.warning((
                    'Перевод с помощью ABBYY Lingvo не выполнен. ' +
                    'Для перевода будет использован Google.'
                ))

                return Translate.google(self, language_pair, text)

            return ParseTranslation.abbyy(self, response.text)
        else:
            logger.info('Перевод фразы/текста - используем Google')

            return Translate.google(self, language_pair, text)


class ParseTranslation:
    def google(self, text):
        try:
            parsing_result = json.loads(text)['data']['translations'][0]['translatedText']
        except Exception:
            logger.critical('Парсинг ответа не выполнен')

            parsing_result = errors.unspecified_error

        return parsing_result

    def yandex(self, text):
        try:
            parsing_result = json.loads(text)['translations'][0]['text']
        except Exception:
            logger.critical('Парсинг ответа не выполнен')

            parsing_result = errors.unspecified_error

        return parsing_result

    def abbyy(self, text):
        try:
            parsing_result = json.loads(text)['Translation']['Translation']
        except Exception:
            logger.critical('Парсинг ответа не выполнен')

            parsing_result = errors.unspecified_error

        return parsing_result


class Detect:
    def google(self, text):
        url = GOOGLE_BASIC_URL + '/detect' + '?key=' + config.GOOGLE_API_KEY
        payload = ({
            'q': [text],
            })
        headers = {
            'Content-Type': 'application/json',
            }

        response = utils.send_post_request(url, payload, headers)

        if utils.is_response_failed(response):
            return response

        return ParseLanguage.google(self, response.text)

    def yandex(self, text):
        url = YANDEX_BASIC_URL + '/detect'
        payload = ({
            'folder_id': config.YANDEX_FOLDER_ID,
            'languageCodeHints': ['ru', 'en'],
            'text': text,
            })
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Api-Key {config.YANDEX_API_TOKEN}',
            }

        response = utils.send_post_request(url, payload, headers)

        if utils.is_response_failed(response):
            return response

        return ParseLanguage.yandex(self, response.text)


class ParseLanguage:
    def google(self, text):
        try:
            parsing_result = json.loads(text)['data']['detections'][0][0]['language']
        except Exception:
            logger.critical('Парсинг ответа не выполнен')

            parsing_result = errors.unspecified_error

        return parsing_result

    def yandex(self, text):
        try:
            parsing_result = json.loads(text)['languageCode']
        except Exception:
            logger.critical('Парсинг ответа не выполнен')

            parsing_result = errors.unspecified_error

        return parsing_result


def get_translation(language_pair, text):
    return getattr(Translate(), config.TRANSLATION_SERVICE)(language_pair, text)


def get_language(text):
    splited_text = text.split(' ')

    short_text = ' '.join(splited_text[:2])

    return getattr(Detect(), config.DETECTION_SERVICE)(short_text)


def get_abbyy_language_code(language):
    dictionaries = {
        'en': 1033,
        'ru': 1049,
    }

    return dictionaries.get(language)


def refresh_abbyy_api_token():

    new_token = get_abbyy_api_token()

    if utils.is_response_failed(new_token):
        print(new_token['error'])
    else:
        config.ABBYY_API_TOKEN = new_token

        print('Токен успешно обновлен')


def get_abbyy_api_token():
    url = ABBYY_BASIC_URL + '/authenticate'
    payload = ''
    headers = {
        'Authorization': f'Basic {config.ABBYY_API_KEY}',
        }

    response = utils.send_post_request(url, payload, headers)

    if utils.is_response_not_ok(response):
        return errors.refresh_token_error

    return response.text.replace('"', '')
