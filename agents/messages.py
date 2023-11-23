""" Перечень сообщений, которыми обмениваются агенты"""
from enum import Enum


class MessageType(Enum):
    """
    Перечень сообщений протокола планирования
    """
    INIT_MESSAGE = 'Инициализация'
    PRICE_REQUEST = 'Запрос цены'
    PRICE_RESPONSE = 'Ответ цены'
    PLANNING_REQUEST = 'Запрос на размещение'
    PLANNING_RESPONSE = 'Ответ на размещение'
    NEW_COURIER_EVENT = 'Добавлен новый курьер'
    UNPLANNING_REQUEST = 'Запрос на удаление из расписания'
    NEW_PLACEMENT_EVENT = 'Размещение было изменено'
    COURIER_REMOVED_EVENT = 'Курьер был удален'
    SHIFT_EVENT_REQUEST = 0
    SHIFT_EVENT_RESPONSE = 1
    SHIFT_IS_DONE = 2
