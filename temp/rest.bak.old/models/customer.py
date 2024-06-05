import json

from rest.helpers import mysql
from .model import Model

__author__ = 'junior'


class CustomerModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'customer'
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

    def insert_into_db(self, cursor, code, name, email, phone, address, lng, lat, username, password, nfcid, contacts,
                       business_activity, is_branch, parent_code, create_date, update_date, is_approval, approval_by,
                       create_by):
        try:
            value = {
                "code": code, "name": name, "email": email, "phone": phone, "address": address, "lng": lng, "lat": lat,
                "username": username, "password": password, "nfcid": nfcid, "contacts": contacts,
                "business_activity": business_activity, "is_branch": is_branch, "parent_code": parent_code,
                "create_date": create_date,
                "update_date": update_date, "is_approval": is_approval,
                "approval_by": approval_by, "create_by": create_by
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, customer_data):
        try:
            # return self.update(cursor, customer_data, 'code')
            return self.update_key(cursor, customer_data, 'code', 'is_deleted', 0)
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

    def get_count_all_customer_nearby(self, cursor, select="code", select_nearby='', join='', where=''):
        try:
            return self.get_sql_count_rows_nearby(cursor, key=select, key_nearby=select_nearby, join=join, where=where)
        except Exception as e:
            raise e

    def get_all_customer_import(self, cursor, fields='*', where=""):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = """SELECT {} FROM {} {}""".format(fields, self.table_import, where)
            cursor.execute(sql)
            data = cursor.fetchall()
        except Exception:
            raise

        return data

    def get_count_all_customer_import(self, cursor, key='*', join='', where=''):
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
            where = "WHERE id = '{}'".format(_id)
            fields = '*'
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

    def get_customer_by_username(self, cursor, username, _id=''):
        try:
            where = "WHERE `username` = '{0}' AND `is_deleted` = 0".format(username)
            if _id:
                where = "WHERE `username` = '{0}' AND `code` != '{1}' AND `is_deleted` = 0".format(username, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_customer_by_code(self, cursor, code, _id='', ignore_is_deleted=False):
        try:
            if ignore_is_deleted:
                where = "WHERE `code` = '{0}'".format(code)
                if _id:
                    where = "WHERE `code` = '{0}' AND `code` != '{1}'".format(code, _id)
            else:
                where = "WHERE `code` = '{0}' AND `is_deleted` = 0".format(code)
                if _id:
                    where = "WHERE `code` = '{0}' AND `code` != '{1}' AND `is_deleted` = 0".format(code, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_customer_by_nfcid(self, cursor, nfcid, _id=''):
        try:
            where = "WHERE `nfcid` = '{0}' AND `is_deleted` = 0".format(nfcid)
            if _id:
                where = "WHERE `nfcid` = '{0}' AND `code` != '{1}' AND `is_deleted` = 0".format(nfcid, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e


class ContactModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'customer_contact'

    def insert_into_db(self, cursor, create_date, update_date, create_by):
        try:
            value = {
                "create_date": create_date, "update_date": update_date, "create_by": create_by
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, contact_data):
        try:
            return self.update(cursor, contact_data, 'id')
        except Exception as e:
            raise e

    def get_contact_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_contact(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_contact(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e
