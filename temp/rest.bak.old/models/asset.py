import json

from rest.helpers import mysql
from .model import Model

__author__ = 'junior'


class AssetModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'assets'

    def insert_into_db(self, cursor, code, device_code, name, asset_type_id, asset_status, notes, create_date,
                       update_date, is_approval, approval_by, create_by):
        try:
            value = {
                "code": code, "device_code": device_code, "name": name, "asset_type_id": asset_type_id,
                "asset_status": asset_status, "notes": notes, "create_date": create_date, "update_date": update_date,
                "is_approval": is_approval, "approval_by": approval_by, "create_by": create_by
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, asset_data):
        try:
            return self.update(cursor, asset_data, 'id')
        except Exception as e:
            raise e

    def get_asset_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_asset(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_asset(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_asset_by_code(self, cursor, name, _id=''):
        try:
            where = "WHERE `code` = '{}' AND `is_deleted` = 0".format(name)
            if _id:
                where = "WHERE `code` = '{0}' AND `id` != {1} AND `is_deleted` = 0".format(name, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e


class AssetTypeModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'asset_types'

    def get_all_asset_type(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_asset_type_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_count_all_asset_type(self, cursor, select='*', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e