import json

from rest.helpers import mysql
from .model import Model

__author__ = 'junior'


class UserGroupModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = "user_groups"

    def insert_into_db(self, cursor, group_name, code, have_asset, asset, create_date, update_date, permissions,
                       is_approval, approval_by, create_by):
        try:
            value = {"group_name": group_name, "code": code, "have_asset": have_asset, "asset": asset,
                     "create_date": create_date, "update_date": update_date, "permissions": permissions,
                     "is_approval": is_approval, "approval_by": approval_by, "create_by": create_by}
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, user_group_data):
        try:
            return self.update(cursor, user_group_data, 'id')
        except Exception as e:
            raise e

    def get_all_user_group(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_user_group(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_user_group_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_user_group_by_name(self, cursor, name, _id=''):
        try:
            where = "WHERE `group_name` = '{0}' AND is_deleted = 0".format(name)
            if _id:
                where = "WHERE `group_name` = '{0}' AND `id` != {1} AND is_deleted = 0".format(name, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_count_all_user_group_statistic(
            self, cursor, select='*', select_count='id', select_form='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_form, join=join, where=where,
                order=order, group=group
            )
        except Exception as e:
            raise e

