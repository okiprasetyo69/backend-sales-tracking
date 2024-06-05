import json

from rest.helpers import mysql
from .model import Model

__author__ = 'junior'


class AreaModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'area'

    def insert_into_db(self, cursor, name, marker_type, marker_color, markers, description,
                       create_date, update_date, is_approval, approval_by, create_by):
        try:
            value = {
                "name": name, "marker_type": marker_type, "marker_color": marker_color, "markers": markers,
                "description": description, "create_date": create_date, "update_date": update_date,
                "is_approval": is_approval, "approval_by": approval_by, "create_by": create_by
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, employee_data):
        try:
            return self.update(cursor, employee_data, 'id')
        except Exception as e:
            raise e

    def get_area_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_area(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_area(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_area_by_name(self, cursor, name, _id=''):
        try:
            where = "WHERE `name` = '{0}'".format(name)
            if _id:
                where = "WHERE `name` = '{0}' AND `id` != {1}".format(name, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e