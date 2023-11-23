""" Реализация класса агента заказа"""
import logging
import typing

from .agent_base import AgentBase
from .messages import MessageType
from entities.courier_entity import CourierEntity
from entities.order_entity import OrderEntity


class OrderAgent(AgentBase):
    """
    Класс агента заказа
    """

    def __init__(self):
        super().__init__()
        self.entity: OrderEntity
        self.name = 'Агент заказа'
        self.subscribe(MessageType.PRICE_RESPONSE, self.handle_price_response)
        self.subscribe(MessageType.PLANNING_RESPONSE, self.handle_planning_response)
        self.subscribe(MessageType.NEW_COURIER_EVENT, self.handle_new_courier_event)
        self.subscribe(MessageType.NEW_PLACEMENT_EVENT, self.handle_new_placement_event)
        self.subscribe(MessageType.COURIER_REMOVED_EVENT, self.handle_courier_removed_event)
        self.subscribe(MessageType.SHIFT_EVENT_REQUEST, self.handle_shift_event_request)
        self.subscribe(MessageType.SHIFT_IS_DONE, self.handle_shift_is_done)

        self.unchecked_couriers = []
        self.possible_variants: list[dict[str, typing.Any]] = []
        
    def handle_shift_event_request(self, message, sender):
        variant = message[1]
        self.possible_variants = [variant]
        self.__evaluate_variants()
        self.send(sender, (MessageType.SHIFT_EVENT_RESPONSE, self.possible_variants))
    
    def handle_shift_is_done(self, message, sender):
        result = message[1]
        logging.info(f'{self} - получил {message}, результат - {result}')
        if result.get('success'):
            self.entity.delivery_data = result
            logging.info(f'{self} доволен, ничего делать не надо')
            return

    def handle_planning_response(self, message, sender):
        """
        Обработка сообщения с результатами планирования.
        :param message:
        :param sender:
        :return:
        """
        result = message[1]
        logging.info(f'{self} - получил {message}, результат - {result}')

        if result.get('success'):
            self.entity.delivery_data = result
            logging.info(f'{self} доволен, ничего делать не надо')
            return
        # Ищем другой вариант для размещения
        # Возможно, правильнее было бы снова инициализировать варианты путем переговоров
        # Но мы попробуем другие варианты, которые у нас уже есть
        sorted_vars = sorted(self.possible_variants,
                             key=lambda x: x.get('price'))
        # Прошлый лучший вариант, который мы проверяли
        checked_variant = sorted_vars[0]
        self.possible_variants.remove(checked_variant)
        if not self.possible_variants:
            self.__send_params_request()
            return
        self.__run_planning()

    def handle_init_message(self, message, sender):
        super().handle_init_message(message, sender)
        # Ищем в системе ресурсы и отправляем им запросы
        self.__send_params_request()

    def handle_new_courier_event(self, message, sender):
        logging.info(f'{self} - получил сообщение {message}')
        if not self.entity.is_planned():
            self.__send_params_request()

    def handle_courier_removed_event(self, message, sender):
        logging.info(f'{self} - получил сообщение {message}')
        self.entity.delivery_data = {
            'courier': None,
            'price': None,
            'time_from': None,
            'time_to': None,
        }
        self.__send_params_request()

    def handle_new_placement_event(self, message, sender):
        logging.info(f'{self} - получил сообщение {message}')
        new_delivery_data = message[1]
        self.entity.delivery_data = new_delivery_data

    def __send_params_request(self):
        self.unchecked_couriers = []
        self.possible_variants = []
        all_couriers: typing.List[CourierEntity] = self.scene.get_entities_by_type('COURIER')
        logging.info(f'{self} - список ресурсов: {all_couriers}')
        for courier in all_couriers:
            if self.entity.weight > courier.max_mass:
                logging.info(f'{self} - грузоподъемность {courier} - {courier.max_mass} '
                             f'меньше {self.entity.weight}')
                continue
            if self.entity.volume > courier.max_volume:
                logging.info(f'{self} - макс. объем {courier} - {courier.max_volume} '
                             f'меньше {self.entity.volume}')
                continue
            if self.entity.order_type not in courier.types:
                logging.info(f'{self} - типы грузов {courier} - {courier.types} '
                             f'не включают {self.entity.order_type}')
                continue
            courier_address = self.dispatcher.reference_book.get_address(courier)
            logging.info(f'{self} - адрес {courier}: {courier_address}')
            request_message = (MessageType.PRICE_REQUEST, self.entity)
            self.send(courier_address, request_message)
            self.unchecked_couriers.append(courier_address)

    def handle_price_response(self, message: tuple[MessageType.PRICE_RESPONSE, dict[str, typing.Any]], sender):
        logging.info(f'{self} - получил сообщение {message}')
        courier_variants = message[1]

        self.possible_variants.extend(courier_variants)
        self.unchecked_couriers.remove(sender)
        if not self.unchecked_couriers:
            self.__run_planning()

    def __evaluate_variants(self):
        """
        Оцениваем варианты по критериям и расширяем информацию о них
        :return:
        """
        if not self.possible_variants:
            return
        all_start_times = [var.get('time_from') for var in self.possible_variants]
        min_start_time = min(all_start_times)
        max_start_time = max(all_start_times)
        all_finish_times = [var.get('time_to') for var in self.possible_variants]
        min_finish_time = min(all_finish_times)
        max_finish_time = max(all_finish_times)
        all_prices = [var.get('price') for var in self.possible_variants]
        min_price = min(all_prices)
        max_price = max(all_prices)
        logging.info(f'{self} минимальный старт: {min_start_time}, минимальное завершение - {min_finish_time}, '
                     f'минимальная цена - {min_price}')
        for variant in self.possible_variants:
            start_efficiency = self.get_decreasing_kpi_value(variant.get('time_from'), min_start_time, max_start_time)
            finish_efficiency = self.get_increasing_kpi_value(variant.get('time_to'), min_finish_time, max_finish_time)
            price_efficiency = self.get_increasing_kpi_value(variant.get('price'), min_price, max_price)
            variant['start_efficiency'] = start_efficiency  # [0; 1]
            variant['finish_efficiency'] = finish_efficiency  # [0; 1]
            variant['price_efficiency'] = price_efficiency  # [0; 1]

            # Итоговая оценка варианта должна учитывать все критерии
            # (в какой-то пропорции)
            variant['total_efficiency'] = self.entity.price - variant.get('price') #0.5 * finish_efficiency + 0.5 * start_efficiency

    def __run_planning(self):
        if not self.possible_variants:
            logging.info(f'{self} - нет возможных вариантов для планирования')
            return
        # Оцениваем варианты
        self.__evaluate_variants()
        # Сортируем варианты
        sorted_vars = sorted(self.possible_variants, key=lambda x: x.get('total_efficiency'))
        # Наилучший
        best_variant = sorted_vars[0]
        # Адрес лучшего варианта
        best_variant_address = self.dispatcher.reference_book.get_address(best_variant.get('courier'))

        logging.info(f'{self} - лучшим вариантом признан {best_variant}, '
                     f'адрес - {best_variant_address}')
        request_message = (MessageType.PLANNING_REQUEST, best_variant)
        self.send(best_variant_address, request_message)

    def handle_deleted(self, msg, sender):
        logging.info(f'{self} получил сообщение об удалении.')
        if self.entity.is_planned():
            courier = self.entity.delivery_data.get('courier')
            courier_address = self.dispatcher.reference_book.get_address(courier)
            request_message = (MessageType.UNPLANNING_REQUEST, self.entity)
            self.send(courier_address, request_message)
