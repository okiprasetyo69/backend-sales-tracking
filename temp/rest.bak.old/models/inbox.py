import json

from rest.helpers import mysql
from .model import Model

__author__ = 'junior'


class InboxModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'inbox'

    def insert_into_db(
            self, cursor, title, date, message, payload, category, user_id, from_id, create_date, update_date
    ):
        try:
            value = {
                "title": title, "date": date, "message": message, "payload": payload, "category": category,
                "user_id": user_id, "from_id": from_id, "create_date": create_date, "update_date": update_date
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, update_data):
        try:
            return self.update(cursor, update_data, 'id')
        except Exception as e:
            raise e

    def get_inbox_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_inbox(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_inbox(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e