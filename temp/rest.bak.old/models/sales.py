import json

from rest.helpers import mysql
from .model import Model

__author__ = 'junior'


class RequestOrderModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'request_orders'

    def insert_into_db(
            self, cursor, date, user_id, customer_code, is_special_order, contacts, delivery_address, lat, lng, notes,
            create_date, update_date
    ):
        try:
            value = {
                "date": date, "user_id": user_id, "customer_code": customer_code, "is_special_order": is_special_order,
                "contacts": contacts, "delivery_address": delivery_address, "lat": lat, "lng": lng,
                "notes": notes, "create_date": create_date, "update_date": update_date
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, update_data):
        try:
            return self.update(cursor, update_data, 'id')
        except Exception as e:
            raise e

    def get_request_order_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_request_order(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_request_order(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_count_all_request_order_statistic(
            self, cursor, select='*', select_count='id', select_form='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_form, join=join, where=where,
                order=order, group=group
            )
        except Exception as e:
            raise e


class RequestOrderProductModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table ='request_orders_product'

    def insert_into_db(self, cursor, request_orders_id, item_name, qty, create_date, update_date):
        try:
            value = {
                "request_orders_id": request_orders_id, "item_name": item_name, "qty": qty,
                "create_date": create_date, "update_date": update_date
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def get_all_request_order_product(self, cursor, _id):
        try:
            where = "WHERE `request_orders_id` = {0}".format(_id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_count_all_request_order_product(self, cursor, _id, select='id'):
        try:
            where = "WHERE `request_orders_id` = {0}".format(_id)
            return self.get_sql_count_rows(cursor, key=select, where=where)
        except Exception as e:
            raise e


class RequestOrderImageModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'request_orders_image'

    def insert_into_db(self, cursor, request_orders_id, filename, file, create_date, update_date):
        try:
            value = {
                "request_orders_id": request_orders_id, "filename": filename, "file": file,
                "create_date": create_date, "update_date": update_date
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def get_all_request_order_image(self, cursor, _id):
        try:
            where = "WHERE `request_orders_id` = {0}".format(_id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_count_all_request_order_image(self, cursor, _id, select='id'):
        try:
            where = "WHERE `request_orders_id` = {0}".format(_id)
            return self.get_sql_count_rows(cursor, key=select, where=where)
        except Exception as e:
            raise e


class SalesOrderModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'sales_orders'
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

    def get_sales_order_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE code = '{}'".format(_id))
        except Exception as e:
            raise e

    def get_sales_order_by_invoice_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE invoice_code = '{}'".format(_id))
        except Exception as e:
            raise e

    def get_all_sales_order(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_sales_order(self, cursor, select='code', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_count_all_sales_order_statistic(
            self, cursor, select='*', select_count='id', select_form='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_form, join=join, where=where,
                order=order, group=group
            )
        except Exception as e:
            raise e

    def get_all_sales_order_import(self, cursor, fields='*', where=""):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = """SELECT {} FROM {} {}""".format(fields, self.table_import, where)
            cursor.execute(sql)
            data = cursor.fetchall()
        except Exception:
            raise

        return data

    def get_count_all_sales_order_import(self, cursor, key='*', join='', where=''):
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


class SalesPaymentModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'sales_payment'
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

    def get_sales_payment_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE code = '{}'".format(_id))
        except Exception as e:
            raise e

    def get_all_sales_payment(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_sales_payment(self, cursor, select='code', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_all_sales_payment_import(self, cursor, fields='*', where=""):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = """SELECT {} FROM {} {}""".format(fields, self.table_import, where)
            cursor.execute(sql)
            data = cursor.fetchall()
        except Exception:
            raise

        return data

    def get_count_all_sales_payment_import(self, cursor, key='*', join='', where=''):
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


class SalesPaymentMobileModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'sales_payment_mobile'

    # def insert_into_db(
    #         self, cursor, visit_plan_id, customer_code, invoice, invoice_amount, payment_amount, payment_date,
    #         payment_method, payment_info, receipt_printed, create_by, create_date, update_date
    # ):
    def insert_into_db(
            self, cursor, visit_plan_id, customer_code, invoice, invoice_amount, payment_amount, payment_date,
            receipt_printed, create_by, create_date, update_date
    ):
        try:
            # value = {
            #     "visit_plan_id": visit_plan_id, "customer_code": customer_code, "invoice": invoice,
            #     "invoice_amount": invoice_amount, "payment_amount": payment_amount, "payment_date": payment_date,
            #     "payment_method": payment_method, "payment_info": payment_info, "receipt_printed": receipt_printed,
            #     "create_by": create_by, "create_date": create_date, "update_date": update_date
            # }
            value = {
                "visit_plan_id": visit_plan_id, "customer_code": customer_code, "invoice": invoice,
                "invoice_amount": invoice_amount, "payment_amount": payment_amount, "payment_date": payment_date,
                "receipt_printed": receipt_printed, "create_by": create_by, "create_date": create_date,
                "update_date": update_date
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, visit_data):
        try:
            return self.update(cursor, visit_data, 'id')
        except Exception as e:
            raise e

    def get_sales_payment_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = '{}'".format(_id))
        except Exception as e:
            raise e

    def get_all_sales_payment(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_sales_payment(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_count_all_sales_payment_statistic(
            self, cursor, select='*', select_count='id', select_form='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_form, join=join, where=where,
                order=order, group=group
            )
        except Exception as e:
            raise e
