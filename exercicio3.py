# coding: utf-8
from datetime import datetime as dt


def logger(func):
    def wrapper(*args, **kwargs):
        name = func.__name__

        with open('log.txt', 'a') as log:
            time_before = dt.now().strftime('%H:%M %d/%m/%Y')
            hour_before, date_before = time_before.split()
            msg_before = 'A função "{}" foi executada em {} do dia {}'
            msg_before = msg_before.format(name, hour_before, date_before)
            log.write(msg_before + '\n')

        result = func(*args, **kwargs)

        with open('log.txt', 'a') as log:
            hour_after = dt.now().strftime('%H:%M')
            msg_after = 'Em {}, a função "{}" foi finalizada e retornou {}'
            msg_after = msg_after.format(hour_after, name, result)
            log.write(msg_after + '\n')

        return result
    return wrapper


@logger
def even(number):
    return number % 2 == 0


even(12)
