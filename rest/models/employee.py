import json

from rest.helpers import mysql
from .model import Model

__author__ = 'junior'


class EmployeeModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'employee'
        self.table_import = 'file_upload'

    def insert_into_db(
            self, cursor, name, nip, email, phone, job_function, is_supervisor_sales, is_supervisor_logistic,
            is_collector_only, is_can_collect, create_date, update_date, is_approval, approval_by, create_by
    ):
        try:
            value = {
                "name": name, "nip": nip, "email": email, "phone": phone, "job_function": job_function,
                "is_supervisor_sales": is_supervisor_sales, "is_supervisor_logistic": is_supervisor_logistic,
                "is_collector_only": is_collector_only, "is_can_collect": is_can_collect,
                "create_date": create_date, "update_date": update_date, "is_approval": is_approval,
                "approval_by": approval_by, "create_by": create_by
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

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

    def update_by_id(self, cursor, employee_data):
        try:
            return self.update(cursor, employee_data, 'id')
        except Exception as e:
            raise e

    def get_employee_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_employee(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_employee(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_employee_by_name(self, cursor, name, _id=''):
        try:
            where = "WHERE `name` = '{0}' AND `is_deleted` = 0".format(name)
            if _id:
                where = "WHERE `name` = '{0}' AND `id` != {1} AND `is_deleted` = 0".format(name, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_all_employee_import(self, cursor, fields='*', where=""):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = """SELECT {} FROM {} {}""".format(fields, self.table_import, where)
            cursor.execute(sql)
            data = cursor.fetchall()
        except Exception:
            raise

        return data

    def get_count_all_employee_import(self, cursor, key='*', join='', where=''):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = """SELECT COUNT({0}) AS count FROM {1} {2} {3}""".format(key, self.table_import, join, where)
            cursor.execute(sql)
            count = cursor.fetchone()["count"]
        except Exception:
            raise

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