from rest.helpers import QueryBuilder

__author__ = 'root'


class Model:

    table = None

    def __init__(self):
        self.qb = QueryBuilder()

    def get(self, cursor, fields='*', join="", where="", order="", limit=""):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = """SELECT {} FROM {} {} {} {} {}""".format(fields, self.table, join, where, order, limit)
            # print("sql get : ", sql)
            cursor.execute(sql)
            data = cursor.fetchall()
        except Exception:
            raise

        return data

    def insert(self, cursor, value):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = self.qb.insert(value, self.table)
            return cursor.execute(sql)
        except Exception:
            raise

    def insert_ignore(self, cursor, value):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = self.qb.insert(value, self.table, True)
            # print(sql)
            return cursor.execute(sql)
        except Exception:
            raise

    def insert_update(self, cursor, value, key, exclude_field=''):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = self.qb.insert_update(value, key, self.table, exclude_field)
            # print(sql)
            return cursor.execute(sql)
        except Exception:
            raise

    def insert_update_batch(self, cursor, value, exclude_field=''):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = self.qb.insert_update_batch(value, self.table, exclude_field)
            # print("###{}###".format(sql))
            return cursor.execute(sql)
        except Exception:
            raise

    def update(self, cursor, value, key):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = self.qb.update(value, self.table, key)
            # print(sql)
            return cursor.execute(sql)
        except Exception:
            raise

    def update_key(self, cursor, value, key, key2, val):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = self.qb.update_key(value, self.table, key, key2, val)
            # print(sql)
            return cursor.execute(sql)
        except Exception:
            raise

    def truncate(self, cursor):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = self.qb.truncate(self.table)
            # print(sql)
            return cursor.execute(sql)
        except Exception:
            raise

    def get_sql_rows_found(self, cursor):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = "SELECT FOUND_ROWS() AS count"
            cursor.execute(sql)
            count = cursor.fetchone()["count"]
        except Exception:
            raise

        return count

    def get_sql_count_rows(self, cursor, key='*', join='', where=''):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = """SELECT COUNT({0}) AS count FROM {1} {2} {3}""".format(key, self.table, join, where)
            cursor.execute(sql)
            count = cursor.fetchone()["count"]
        except Exception:
            raise

        return count

    def get_sql_count_rows_nearby(self, cursor, key='*', key_nearby='', join='', where=''):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = """SELECT COUNT({0}) AS count FROM {1} {2} {3}""".format(key, key_nearby, join, where)
            # print(sql)
            cursor.execute(sql)
            count = cursor.fetchone()["count"]
        except Exception:
            raise

        return count

    def get_sql_count_statistic(self, cursor, key='*', key_count='', from_select='', join='', where='',
                                group='', order=''):
        self.change_charset_to_utf8mb4(cursor)
        try:
            if from_select:
                sql = """SELECT {0} {1} FROM {2} {3} {4} {5} {6}""".format(
                    key, key_count, from_select, join, where, group, order
                )
            else:
                sql = """SELECT {0} {1} FROM {2} {3} {4} {5} {6}""".format(
                    key, key_count, self.table, join, where, group, order
                )
            # print("sql : ",sql)
            cursor.execute(sql)
            data = cursor.fetchall()
        except Exception:
            raise

        return data

    @staticmethod
    def change_charset_to_utf8mb4(cursor):
        cursor.execute("SET NAMES utf8mb4;")  # or utf8 or any other charset you want to handle
        cursor.execute("SET CHARACTER SET utf8mb4;")  # same as above
        cursor.execute("SET character_set_connection=utf8mb4;")  # same as above