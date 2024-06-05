import json

from rest.helpers import mysql
from .model import Model

__author__ = 'junior'


class VisitEyeCustomerModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'customer_visit_eye'

    def import_insert(self, cursor, data, key):
        try:
            return self.insert_update(cursor, data, key)
        except Exception as e:
            raise e

    def get_customer_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE code = '{}'".format(_id))
        except Exception as e:
            raise e

    def get_all_customer(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_customer(self, cursor, select='code', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_customer_by_username(self, cursor, username, _id=''):
        try:
            where = "WHERE `username` = '{0}' ".format(username)
            if _id:
                where = "WHERE `username` = '{0}' AND `code` != '{1}' ".format(username, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_customer_by_code(self, cursor, code, _id=''):
        try:
            where = "WHERE `code` = '{0}' ".format(code)
            if _id:
                where = "WHERE `code` = '{0}' AND `code` != '{1}' ".format(code, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e


class VisitEyeUserModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = "user_visit_eye"

    def import_insert(self, cursor, data, key):
        try:
            return self.insert_update(cursor, data, key)
        except Exception as e:
            raise e

    def get_user_by_username(self, cursor, username, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE username = '{}'".format(username))
        except Exception as e:
            raise e

    def get_user_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE username = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_user(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_user(self, cursor, select='username', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e