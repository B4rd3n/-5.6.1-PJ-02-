import redis
import json
import requests
import lxml.html


class RedisData:
    db = redis.Redis(host = 'redis-14814.c265.us-east-1-2.ec2.cloud.redislabs.com',
                         port = 14814,
                         password = 'LIyEPuYG3lfOOeoIw5XQHeDTNmWy4WXp',
                         decode_responses = True)


class PricesCache:
    _db = RedisData.db

    @classmethod
    def get_prices(cls):
        cache = cls._db.get("prices")

        if not cache:
            price_usd = requests.get(f'https://v6.exchangerate-api.com/v6/4e21cf827a909a1f3d9038d5/latest/USD').content
            convert = json.loads(price_usd)['conversion_rates']

            cls._db.setex("prices", 3600, json.dumps(convert))

            return convert
        return json.loads(cache)


class AvailableCurrencies:
    _db = RedisData.db

    @classmethod
    def _load_data(cls):

        html = requests.get('https://www.exchangerate-api.com/docs/supported-currencies').content
        tree = lxml.html.fromstring(html)
        rows = tree.xpath('//table[3]/tr')

        codes = dict()

        for element in rows[1:]:
            code = element.find('td[1]')
            full_name = element.find('td[2]')
            codes[code.text_content()] = full_name.text_content()

        cls._db.setex("available_countries", 86400, json.dumps(codes))
        return codes

    @classmethod
    def get_all_countries(cls):
        data = cls._db.get("available_countries")

        if data:
            return json.loads(data)

        return cls._load_data()

    @classmethod
    def get_curr_txt(cls):

        all_currencies = ""
        curr_dict = cls.get_all_countries()

        for element in curr_dict:
            full_name = curr_dict[element]
            all_currencies += f"{element} - {full_name}\n"

        return all_currencies

    @classmethod
    def curr_amount(cls):
        return len(cls.get_all_countries())



class FavoriteManager:
    _db = RedisData.db
    max_limit = 3

    def __init__(self, user_id):
        self.user_id = user_id
        self.favorite_key = f"favorite:{self.user_id}"

    def favorites(self, favorite):
        amount = self._db.scard(self.favorite_key)
        converted = PricesCache.get_prices()


        if favorite not in converted:
            return "Валюта не найдена..."

        if amount >= FavoriteManager.max_limit:
            return f"Лимит превышен! ({FavoriteManager.max_limit} шт.)"

        is_inside = self._db.sadd(self.favorite_key, favorite)

        if is_inside:
            return "Успешно добавлено!"

        else:
            return "Эта валюта уже есть в списке."

    def remove_favorite(self, favorite):
        remove = self._db.srem(self.favorite_key, favorite)

        if remove:
            return f"Валюта {favorite} успешно удалена!"
        else:
            return "Этой валюты и не было в вашем списке..."

    def show_favorite(self):
        data_countries = self._db.smembers(self.favorite_key)
        if not data_countries:
            return "Ваш список пуст!"

        all_countries = AvailableCurrencies.get_all_countries()
        show = ''
        counter = 1

        for element in data_countries:
            if element in all_countries:
                show += f'{counter}. <code>{element}</code> - {all_countries[element]}\n'
                counter += 1

        return show
