import json

from rest.helpers import mysql
from .model import Model

__author__ = 'junior'


class CompanyModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'company'

    def update_by_id(self, cursor, employee_data):
        try:
            return self.update(cursor, employee_data, 'id')
        except Exception as e:
            raise e

    def get_company_by_id(self, cursor, _id):
        try:
            return self.get(cursor, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e


class GeneralModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'setting_general'

    def update_by_id(self, cursor, setting_data):
        try:
            return self.update(cursor, setting_data, 'id')
        except Exception as e:
            raise e

    def get_general_by_id(self, cursor, _id):
        try:
            return self.get(cursor, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e


class NotifModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'setting_notifications'

    def update_by_id(self, cursor, setting_data):
        try:
            return self.update(cursor, setting_data, 'id')
        except Exception as e:
            raise e

    def get_notif_by_id(self, cursor, _id):
        try:
            return self.get(cursor, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_notif_by_type(self, cursor, type):
        try:
            return self.get(cursor, where="WHERE category = '{}'".format(type))
        except Exception as e:
            raise e