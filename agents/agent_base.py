"""Содержит базовую реализацию агента с обработкой сообщений"""
import logging
import traceback
from abc import ABC
from typing import Optional, TYPE_CHECKING

from thespian.actors import Actor, ActorExitRequest
from agents.scene import Scene

from entities.base_entity import BaseEntity

if TYPE_CHECKING:
    from agents.agents_dispatcher import AgentsDispatcher

from .messages import MessageType


class AgentBase(ABC, Actor):
    """
    Базовая реализация агента
    """

    def __init__(self):
        self.name = 'Базовый агент'
        super().__init__()
        self.handlers = {}
        self.scene: Scene = None
        self.dispatcher: Optional[AgentsDispatcher] = None
        self.entity: BaseEntity = None
        self.subscribe(MessageType.INIT_MESSAGE, self.handle_init_message)

    def subscribe(self, msg_type: MessageType, handler):
        """
        Подписка на события определенного типа
        :param msg_type: Тип события
        :param handler: Обработчик сообщения заданного типа
        :return:
        """
        if msg_type in self.handlers:
            logging.warning('Повторная подписка на сообщение: %s', msg_type)
        self.handlers[msg_type] = handler

    def handle_deleted(self, msg, sender):
        logging.info(f'{self} получил сообщение {msg}')

    def receiveMessage(self, msg, sender):
        """Обрабатывает сообщения - запускает их обработку в зависимости от типа.
        :param msg:
        :param sender:
        :return:
        """
        logging.debug('%s получил сообщение: %s', self.name, msg)
        if isinstance(msg, ActorExitRequest):
            logging.info(f'{self} получил сообщение {msg} - ActorExitRequest')
            self.handle_deleted(msg, sender)
            return

        if isinstance(msg, tuple):

            message_type, message_data = msg
            if message_type in self.handlers:
                try:
                    self.handlers[message_type](msg, sender)
                except Exception as ex:
                    traceback.print_exc()
                    logging.error(ex)
            else:
                logging.warning('%s Отсутствует подписка на сообщение: %s', self.name, message_type)
        else:
            logging.error('%s Неверный формат сообщения: %s', self.name, msg)
            super().receiveMessage(msg, sender)

    def __str__(self):
        return self.name

    def handle_init_message(self, message, sender):
        """
        Обработка сообщения с инициализацией - сохранение присланных данных в агенте.
        :param message:
        :param sender:
        :return:
        """
        self.scene = message[1].get('scene')
        self.dispatcher = message[1].get('dispatcher')
        self.entity = message[1].get('entity')
        self.name = self.name + ' ' + self.entity.name
        logging.info(f'{self} проинициализирован')

    @staticmethod
    def get_decreasing_kpi_value(value: float, min_value: float, max_value: float):
        """
        Функция возвращает значение убывающей линейной функции
        (f(x)) с областью определения [minValue, maxValue], нормированное к единице.
        f(minValue) === 1. f(maxValue) === 0
        :param value:
        :param min_value:
        :param max_value:
        :return:
        """

        if max_value == min_value:
            return 1

        if value > max_value or value < min_value:
            return -1

        if isinstance(value, float) and abs(value - min_value) < 0.000001:
            # Работаем с минимальным значением => возвращаем 1
            return 1
        if isinstance(value, float) and abs(value - max_value) < 0.000001:
            # Работаем с максимальным значением => возвращаем 0
            return 0
        # Решаем уравнение прямой по двум точкам. f(minValue) == 1; f(maxValue) == 0
        return 1 - (value - min_value) / (max_value - min_value)

    @staticmethod
    def get_increasing_kpi_value(value: float, min_value: float, max_value: float):
        """
        Функция возвращает значение возрастающей линейной функции
        (f(x)) с областью определения [minValue, maxValue], нормированное к единице.
        f(minValue) === 0. f(maxValue) === 1
        :param value:
        :param min_value:
        :param max_value:
        :return:
        """

        if max_value == min_value:
            # Работаем с прямой, все значения - единицы
            return 1

        if value > max_value or value < min_value:
            # Некорректные данные, выходят из диапазона
            return -1
        if isinstance(value, float) and abs(value - min_value) < 0.000001:
            # Работаем с минимальным значением => возвращаем 0
            return 0
        if isinstance(value, float) and abs(value - max_value) < 0.000001:
            # Работаем с максимальным значением => возвращаем 1
            return 1

        # Решаем уравнение прямой по двум точкам. f(minValue) == 0; f(maxValue) == 1
        return (value - min_value) / (max_value - min_value)
