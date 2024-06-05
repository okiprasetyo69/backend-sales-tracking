import json

from rest.helpers import mysql
from .model import Model

__author__ = 'junior'


class PermissionsModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'mobile_permission_alert'

    def insert_into_db(self, cursor, subject, customer_code, visit_plan_id, delivery_plan_id, date, type, description, notes, create_by):
        try:
            value = {
                'subject': subject, 'customer_code': customer_code, 'visit_plan_id': visit_plan_id,
                'delivery_plan_id': delivery_plan_id, 'date': date, 'type': type,
                'description': description, 'notes': notes, 'create_by': create_by
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, division_data):
        try:
            return self.update(cursor, division_data, 'id')
        except Exception as e:
            raise e

    def get_permission_alert_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_permission_alert(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_permission_alert(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_count_all_permission_alert_statistic(
            self, cursor, select='*', select_count='', select_from='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_from, join=join, where=where,
                order=order, group=group
            )
        except Exception as e:
            raise e