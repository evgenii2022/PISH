import logging

from agents.agents_dispatcher import AgentsDispatcher
from agents.scene import Scene
from entities.courier_entity import CourierEntity
from entities.order_entity import OrderEntity
from utils.excel_utils import get_excel_data, save_schedule_to_excel
from utils.json_utils import save_json
from pathlib import Path

def add_entity(scene: Scene):
    type_input = input("Выберите тип. С - курьер, O - заказ: ")
    required_params = []
    entity_class = None
    if type_input.upper() in ["С", "C"]:
        required_params = [
            'Табельный номер', 'ФИО', 'Координата начального положения x',
            'Координата начального положения y', 'Типы доставляемых заказов',
            'Стоимость выхода на работу', 'Цена работы за единицу времени', 'Скорость',
            'Объем ранца', 'Грузоподъемность',
        ]
        entity_class = CourierEntity
    if type_input.upper() in ["O", "О"]:
        required_params = [
            'Номер', 'Наименование', 'Масса', 'Объем', 'Стоимость', 'Координата получения x', 'Координата получения y',
            'Координата доставки x', 'Координата доставки y', 'Время получения заказа', 'Время доставки заказа',
            'Тип заказа',
        ]
        entity_class = OrderEntity
    if required_params and entity_class:
        result = {}
        for param in required_params:
            param_input = input(f'Введите параметр {param}: ')
            result[param] = param_input
        if result:
            onto_description = {}
            # TODO: Тут не хватает проверки на дублирование идентификаторов.
            entity = entity_class(onto_description, result, scene)
            return entity
        return result
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    logging.info("Добро пожаловать в мир агентов")
    scene = Scene()
    dispatcher = AgentsDispatcher(scene)

    couriers = get_excel_data('Исходные данные.xlsx', 'Курьеры')
    logging.info(f'Прочитаны курьеры: {couriers}')
    for courier in couriers:
        onto_description = {}
        entity = CourierEntity(onto_description, courier, scene)
        dispatcher.add_entity(entity)

    orders = get_excel_data('Исходные данные.xlsx', 'Заказы')
    logging.info(f'Прочитаны заказы: {orders}')
    for order in orders:
        onto_description = {}
        entity = OrderEntity(onto_description, order, scene)
        dispatcher.add_entity(entity)

    all_schedule_records = []
    for courier in scene.get_entities_by_type('COURIER'):
        all_schedule_records.extend(courier.get_schedule_json())
    Path("./out").mkdir(parents=True, exist_ok=True)
    save_schedule_to_excel(all_schedule_records, 'Результаты.xlsx')
    save_json(all_schedule_records, './out', 'Результаты.json')

    while True:
        logging.info("A - добавить агента")
        logging.info("D - удалить агента")
        logging.info("L - посмотреть список агентов")
        logging.info("Q - Выход")
        user_input = input(": ")
        was_events_added = False
        if user_input.upper() == "Q":
            break
        if user_input.upper() == "A":
            entity = add_entity(scene)
            if entity:
                dispatcher.add_entity(entity)
                was_events_added = True
        elif user_input.upper() == "D":
            logging.info("Запускаем удаление агента")
            logging.info("Введите идентификатор агента")
            id_input = input(": ")
            remove_result = dispatcher.remove_agent(id_input)
            logging.info(f'Результат удаления агента: {remove_result}')
            was_events_added = remove_result
        elif user_input.upper() == "L":
            agents_addresses = dispatcher.get_agents_id()
            logging.info(agents_addresses)

        if was_events_added:
            new_schedule_records = []
            for courier in scene.get_entities_by_type('COURIER'):
                assert isinstance(courier, CourierEntity)
                new_schedule_records.extend(courier.get_schedule_json())
            Path("./out").mkdir(parents=True, exist_ok=True)
            save_schedule_to_excel(new_schedule_records, 'Результаты.xlsx')
            save_json(new_schedule_records, './out', 'Результаты.json')
