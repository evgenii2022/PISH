""" Реализация класса агента курьера"""
import logging
import typing

from point import Point
from .agent_base import AgentBase
from .messages import MessageType
from entities.courier_entity import CourierEntity, ScheduleItem
from entities.order_entity import OrderEntity


class CourierAgent(AgentBase):
    """
    Класс агента курьера
    """

    def __init__(self):
        super().__init__()
        self.entity: CourierEntity
        self.name = 'Агент курьера'
        self.shift_event_messages = []
        self.n_orders_to_shift = 0
        self.shifter_params: dict = {}
        self.subscribe(MessageType.PRICE_REQUEST, self.handle_price_request)
        self.subscribe(MessageType.PLANNING_REQUEST, self.handle_planning_request)
        self.subscribe(MessageType.UNPLANNING_REQUEST, self.handle_unplanning_request)
        self.subscribe(MessageType.SHIFT_EVENT_RESPONSE, self.handle_shift_event_request)

    def handle_price_request(self, message, sender):
        """
        Обработка сообщения с запросом параметров заказа.
        Выполняет расчет в зависимости от текущего расписания курьера.
        :param message:
        :param sender:
        :return:
        """
        order: OrderEntity = message[1]
        params = self.__get_params(order)
        price_message = (MessageType.PRICE_RESPONSE, params)
        self.send(sender, price_message)
    
    def handle_shift_event_request(self, message, sender):
        variant = message[1]
        self.shift_event_messages.extend(variant)
        if len(self.shift_event_messages) == self.n_orders_to_shift:
            new_inv_efficiency = sum((m['total_efficiency'] for m in self.shift_event_messages))
            if self.inverse_efficiency <= new_inv_efficiency:
                print('11111111111 не берем новый заказ')
                
                self.shifter_params['success'] = False
                address = self.dispatcher.reference_book.get_address(self.shifter_params['order'])
                result_msg = (MessageType.SHIFT_IS_DONE, self.shifter_params)
                self.send(address, result_msg)
            else:
                print('11111111111 берем новый заказ')
                self.inverse_efficiency = new_inv_efficiency
                self.shifter_params['success'] = True
                address = self.dispatcher.reference_book.get_address(self.shifter_params['order'])
                result_msg = (MessageType.SHIFT_IS_DONE, self.shifter_params)
                self.send(address, result_msg)
                
                self.entity.schedule = [item for item in self.entity.schedule \
                    if item.order not in list([item2['order'] for item2 in self.shift_event_messages])]
                self.shift_event_messages.sort(key=lambda a: a['time_from'])
                
                mess['success'] = True
                
                for mess in self.shift_event_messages:
                    self.entity.add_order_to_schedule(
                        mess['order'], 
                        mess['time_from'], 
                        mess['time_to'], 
                        mess['price'], 
                        mess
                    )
                    '''address = self.dispatcher.reference_book.get_address(mess['order'])
                    self.send(address, (MessageType.SHIFT_IS_DONE, mess))
                    order: OrderEntity = mess['order']
                    schedule_item_to_order = ScheduleItem(
                        order, 
                        'Движение за грузом', 
                        mess['time_from'], 
                        mess['time_from'] + (mess['time_to'] - mess['time_from']) / 2,
                        Point(0, 0),#last_point, 
                        order.point_from, 
                        0, 
                        mess
                    )
                    schedule_item = ScheduleItem(
                        order, 
                        'Движение с грузом', 
                        mess['time_from'] + (mess['time_to'] - mess['time_from']) / 2,
                        mess['time_to'],
                        order.point_from, 
                        order.point_to, 
                        mess['price'],
                        mess
                    )
                    self.entity.schedule.append(schedule_item_to_order)
                    self.entity.schedule.append(schedule_item)'''

    def __get_params(self, order: OrderEntity) -> typing.List:
        """
        Формирует возможные варианты размещения заказа
        :param order:
        :return:
        """
        p1 = order.point_from
        # Надо посчитать стоимость выполнения заказа, сроки доставки
        last_point: Point = self.entity.get_last_point()
        distance_to_order = last_point.get_distance_to_other(p1)

        p2 = order.point_to
        distance_with_order = p1.get_distance_to_other(p2)
        time_to_order = distance_to_order / self.entity.velocity
        time_with_order = distance_with_order / self.entity.velocity
        duration = time_to_order + time_with_order

        price = duration * self.entity.rate
        logging.info(f'{self} - заказ {order} надо пронести {distance_with_order},'
                     f' к нему идти {distance_to_order}'
                     f'это займет {duration} и будет стоить {price}')

        last_time = self.entity.get_last_time()

        asap_time_from = last_time
        asap_time_to = asap_time_from + time_to_order + time_with_order
        # Вариант, при котором мы выполняем заказ как только можем
        asap_variant = {'courier': self.entity, 'time_from': asap_time_from, 'time_to': asap_time_to,
                        'price': price, 'order': order, 'variant_name': 'asap'}
        params = [asap_variant]

        '''if asap_time_from < order.time_from:
            # Генерируем вариант, при котором мы заберем заказ вовремя
            jit_time_from = order.time_from - time_to_order
            # JIT-вариант можно генерировать и при наличии записей, но надо расширить
            # проверки на возможность доставки.
            if jit_time_from > 0 and not self.entity.schedule:
                jit_time_to = jit_time_from + time_to_order + time_with_order
                jit_from_variant = {'courier': self.entity, 'time_from': jit_time_from, 'time_to': jit_time_to,
                                    'price': price, 'order': order, 'variant_name': 'jit'}
                params.append(jit_from_variant)'''
        # FIXME: Добавить поиск свободных интервалов в расписании.
        
        # new
        temp_point = None
        temp_time_from = None
        for i, item in enumerate(self.entity.schedule):
            if item.rec_type != 'Движение с грузом':
                continue
            if temp_point is None or temp_time_from is None:
                point_from_prev_order = self.entity.init_point
                time_from = 0
            else:
                assert temp_point is not None
                assert temp_time_from is not None
                point_from_prev_order = temp_point
                time_from = temp_time_from
            temp_point = Point(item.point_to.x, item.point_to.y)
            temp_time_from = item.end_time
            
            distance_to_order = point_from_prev_order.get_distance_to_other(order.point_from)
            distance_with_order = order.point_from.get_distance_to_other(order.point_to)
            time_to_order = distance_to_order / self.entity.velocity
            time_with_order = distance_with_order / self.entity.velocity
            duration = time_to_order + time_with_order
            price = duration * self.entity.rate
            
            logging.info(
                f'{self} - {len(params)+1}-й вариант. Заказ {order} надо пронести {distance_with_order},'
                f' к нему идти {distance_to_order}'
                f'это займет {duration} и будет стоить {price}'
            )
            time_to = time_from + time_to_order + time_with_order
                
            params.append({
                'courier': self.entity, 
                'time_from': time_from, 
                'time_to': time_to, 
                'price': price, 
                'order': order, 
                'variant_name': 'after exsisting order'
            })
        
        return params

    def handle_planning_request(self, message, sender):
        """
        Обработка сообщения с запросом на планирования.
        :param message:
        :param sender:
        :return:
        """
        params = message[1]
        # Пытаемся добавить заказ в свое расписание
        order: OrderEntity = params.get('order')
        adding_result = self.entity.add_order_to_schedule(
            order,
            params.get('time_from'),
            params.get('time_to'),
            params.get('price'),
            params
        )
            
        conflicted_records: list[ScheduleItem] = []
        shifter = order
        occupied_time_from = params.get('time_from')
        occupied_time_to = params.get('time_to')
        new_variants = []
        checked_orders = []
        self.shift_event_messages = []
        self.inverse_efficiency = sum((
            item.all_params['total_efficiency'] for item in self.entity.schedule if item.rec_type == 'Движение с грузом'
        ))
        while True:
            conflicted_records.extend(self.entity.get_conflicts(occupied_time_from, occupied_time_to, checked_orders))
            if len(conflicted_records) == 0:
                break
            new_variant = self.get_variant_after_shift(conflicted_records, shifter, occupied_time_to)
            new_variants.append(new_variant)
            shifter = new_variant['order']
            occupied_time_from = new_variant['time_from']
            occupied_time_to = new_variant['time_to']
            checked_orders.append(shifter)
            conflicted_records = [item for item in conflicted_records if item.order is not shifter]
        
        self.n_orders_to_shift = len(new_variants)
        for item in new_variants:
            address = self.dispatcher.reference_book.get_address(item['order'])
            self.send(address, (MessageType.SHIFT_EVENT_REQUEST, item))
        if self.n_orders_to_shift > 0:
            self.shifter_params = params

        '''logging.info(f'{self} получил запрос на размещение {params}, '
                     f'результат - {adding_result}, конфликты - {conflicted_records}')
        params['success'] = adding_result
        result_msg = (MessageType.PLANNING_RESPONSE, params)
        self.send(sender, result_msg)'''
    
    def get_variant_after_shift(self, conflicted_records: list[ScheduleItem], shifter_order: OrderEntity, shift_time_to: float):
        conflicted_order = conflicted_records[0].order
        distance_to_order = shifter_order.point_to.get_distance_to_other(conflicted_order.point_from)
        distance_with_order = conflicted_order.point_from.get_distance_to_other(conflicted_order.point_to)
        time_to_order = distance_to_order / self.entity.velocity
        time_with_order = distance_with_order / self.entity.velocity
        duration = time_to_order + time_with_order
        price = duration * self.entity.rate
        
        variant = {
            'courier': self.entity, 
            'time_from': shift_time_to, 
            'time_to': shift_time_to + duration, 
            'price': price, 
            'order': conflicted_order, 
            'variant_name': 'after shifting'
        }
        return variant
        
    def handle_deleted(self, msg, sender):
        logging.info(f'{self} получил сообщение об удалении')
        planned_orders = self.entity.get_planned_orders()
        logging.info(f'{self} - список запланированных на курьере заказов: {planned_orders}')
        for order in planned_orders:
            order_address = self.dispatcher.reference_book.get_address(order)
            info_message = (MessageType.COURIER_REMOVED_EVENT, self.entity)
            self.send(order_address, info_message)

    def handle_init_message(self, message, sender):
        super().handle_init_message(message, sender)
        # Ищем в системе заказы и отправляем им сообщение о появлении нового курьера
        self.__send_new_courier_event()

    def handle_unplanning_request(self, message, sender):
        order = message[1]
        logging.info(f'{self} получил запрос на удаление из расписания курьера заказа {order}')
        removing_result = self.entity.remove_order_from_schedule(order)
        if removing_result.is_successful:
            logging.info(f'{self} заказ {order} удален из расписания')
            if removing_result.affected_order is not None:
                affected_order = removing_result.affected_order
                logging.info(f'{self} при удаленнии заказа {order} был затронут заказ {affected_order}')
                order_address = self.dispatcher.reference_book.get_address(affected_order)
                info_message = (MessageType.NEW_PLACEMENT_EVENT, removing_result.affected_order_new_delivery_data)
                self.send(order_address, info_message)
        else:
            logging.info(f'{self} ошибка при удалении заказа {order} из расписания')

    def __send_new_courier_event(self):
        all_orders: typing.List[OrderEntity] = self.scene.get_entities_by_type('ORDER')
        logging.info(f'{self} - список заказов: {all_orders}')
        for order in all_orders:
            order_address = self.dispatcher.reference_book.get_address(order)
            info_message = (MessageType.NEW_COURIER_EVENT, self.entity)
            self.send(order_address, info_message)
