from redis_cache import AvailableCurrencies, PricesCache


class APIException(Exception):
    pass

class CheckConversion:
    @staticmethod
    def final_price(base, quote, amount):

        codes = AvailableCurrencies.get_all_countries()

        if base == quote:
            raise APIException('Валюты должны отличаться.')

        try:
            codes[base]
        except KeyError:
            raise APIException(f'{base} отсутствует в списке доступных валют.')

        try:
            codes[quote]
        except KeyError:
            raise APIException(f'{quote} отсутствует в списке доступных валют.')

        if "," in amount:
            raise APIException(f'Используйте "." в качестве разделителя для дробных чисел.')

        try:
            float(amount)
        except ValueError:
            raise APIException(f"{amount} - это не число.")


        usd_price = PricesCache.get_prices()
        result = (usd_price[quote] / usd_price[base]) * float(amount)

        return result





