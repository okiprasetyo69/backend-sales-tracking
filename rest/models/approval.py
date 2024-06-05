import json

from rest.helpers import mysql
from .model import Model

__author__ = 'junior'


class ApprovalModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'data_approval'

    def insert_into_db(
            self, cursor, prefix, data_id, type, data, create_by, create_date, update_date, is_approved,
            approved_by, is_rejected, rejected_by
    ):
        try:
            value = {
                "prefix": prefix, "data_id": data_id, "type": type, "data": data, "create_by": create_by,
                "create_date": create_date, "update_date": update_date, "is_approved": is_approved,
                "approved_by": approved_by, "is_rejected": is_rejected, "rejected_by": rejected_by
            }
            return self.insert_update(cursor, value, "prefix, data_id, type")
        except Exception as e:
            raise e

    def update_by_id(self, cursor, update_data):
        try:
            return self.update(cursor, update_data, 'id')
        except Exception as e:
            raise e

    def get_approval_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_approval(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_approval(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e