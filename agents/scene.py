""" Реализация класса сцены"""
from collections import defaultdict
from typing import Union

from entities.base_entity import BaseEntity
from entities.order_entity import OrderEntity
from entities.courier_entity import CourierEntity


class Scene:
    """
    Класс сцены
    """

    def __init__(self):
        self.entities = defaultdict(list[BaseEntity])

    def get_entities_by_type(self, entity_type) -> Union[OrderEntity, CourierEntity]:
        """
        Возвращает список сущностей заданного типа
        :param entity_type:
        :return:
        """
        return self.entities.get(entity_type, [])

    def get_entity_by_uri(self, uri):
        """
        Возвращает сущность по URI.
        :param uri:
        :return:
        """
        for entity_list in self.entities.values():
            for entity in entity_list:
                if entity.get_uri() == uri:
                    return entity
        return None

    def remove_entity_by_uri(self, uri):
        """
        Удвляет сущность по URI.
        :param uri:
        :return:
        """
        for key in self.entities.keys():
            for entity in self.entities.get(key):
                if entity.get_uri() == uri:
                    self.entities.get(key).remove(entity)
                    return True
        return False
