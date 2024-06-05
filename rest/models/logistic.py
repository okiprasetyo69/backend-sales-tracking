import json

from rest.helpers import mysql
from .model import Model

__author__ = 'junior'


class PackingSlipModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'packing_slip'
        self.table_import = 'file_upload'

    def import_insert_file(self, cursor, file_name, file_name_origin, table, create_date, update_date, create_by):
        try:
            value = {"file_name": file_name, "file_name_origin": file_name_origin, "table_name": table,
                     "create_date": create_date, "update_date": update_date, "create_by": create_by}
            self.change_charset_to_utf8mb4(cursor)
            try:
                sql = self.qb.insert(value, self.table_import, True)
                print(sql)
                return cursor.execute(sql)
            except Exception:
                raise
        except Exception as e:
            raise e

    def import_insert(self, cursor, data, key):
        try:
            return self.insert_update(cursor, data, key)
        except Exception as e:
            raise e

    def delete_table(self, cursor):
        try:
            return self.truncate(cursor)
        except Exception as e:
            raise e

    def get_packing_slip_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE code = '{}'".format(_id))
        except Exception as e:
            raise e

    def get_all_packing_slip(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_packing_slip(self, cursor, select='code', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_all_packing_slip_import(self, cursor, fields='*', where=""):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = """SELECT {} FROM {} {}""".format(fields, self.table_import, where)
            cursor.execute(sql)
            data = cursor.fetchall()
        except Exception:
            raise

        return data

    def get_count_all_packing_slip_import(self, cursor, key='*', join='', where=''):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = """SELECT COUNT({0}) AS count FROM {1} {2} {3}""".format(key, self.table_import, join, where)
            cursor.execute(sql)
            count = cursor.fetchone()["count"]
        except Exception:
            raise

        return count

    def get_import_by_id(self, cursor, _id):
        try:
            where="WHERE id = '{}'".format(_id)
            fields='*'
            self.change_charset_to_utf8mb4(cursor)
            try:
                sql = """SELECT {} FROM {} {}""".format(fields, self.table_import, where)
                cursor.execute(sql)
                data = cursor.fetchall()
            except Exception:
                raise

            return data
        except Exception as e:
            raise e

    def update_import_by_id(self, cursor, _id, user_id):
        try:
            self.change_charset_to_utf8mb4(cursor)
            try:
                value = {"id": _id, "status": 1, "approval_by": user_id}
                sql = self.qb.update(value, self.table_import, 'id')
                # print(sql)
                return cursor.execute(sql)
            except Exception:
                raise
        except Exception as e:
            raise e