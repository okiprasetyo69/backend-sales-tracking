import json

from rest.helpers import mysql
from .model import Model

__author__ = 'oki'

class AbsenceDailyModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'sales_activity'
        
    def get_all_absences(self, cursor, start=0, limit=200, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order, limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e 
    
    def get_absences_for_count(self, cursor, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order)
        except Exception as e:
            raise e 
        
    def get_count_all_absences(self, cursor, select='*', join='', where='', order=''):
        try:
            return self.get_sql_count_rows_absences(cursor, key=select, join=join, where=where, order=order)
        except Exception as e:
            raise e
        
    def get_total_user_check_in(self, cursor, start=0, limit=10000, select='*', join='', where='', order='') :
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e
    
    def get_total_user_stop(self, cursor, start=0, limit=10000, select='*', join='', where='', order='') :
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e
        
    def get_total_user_start(self, cursor, start=0, limit=10000, select='*', join='', where='', order='') :
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e
        
    def get_total_user_stop(self, cursor, start=0, limit=10000, select='*', join='', where='', order='') :
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e
    
    def get_daily_absence_report(self, cursor, start=0, limit=10000, select='*', join='', where='', order='') :
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e
        
    def get_user_stop_status(self, cursor, select='*', where='', order='') :
        try:
            return self.get(cursor, fields=select, where=where, order=order)
        except Exception as e:
            raise e 
    def update_checkout_user_now(self, cursor, user_id, date):
        try:
            self.change_charset_to_utf8mb4(cursor)
            try:
                value = {"id": _id, "status": 1, "approval_by": user_id}
                sql = self.qb.update(value, self.table, 'id')
                return cursor.execute(sql)
            except Exception:
                raise
        except Exception as e:
            raise e
        
    def insert_into_db(self, cursor, user_id, visit_plan_id, nfc_code, route_breadcrumb, distance, total_distance, tap_nfc_date, tap_nfc_type, create_date, update_date) :
        try:
            value = {
                "user_id": user_id, "visit_plan_id": visit_plan_id, "nfc_code": nfc_code,
                "route_breadcrumb": route_breadcrumb, "distance": distance, "total_distance": total_distance,
                "tap_nfc_date": tap_nfc_date, "tap_nfc_type": tap_nfc_type, "create_date": create_date,
                "update_date": update_date
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e
        
        
    def get_sql_count_rows_absences(self, cursor, key='*', join='', where='', order=''):
        self.change_charset_to_utf8mb4(cursor)
        try:
            sql = """SELECT COUNT({0}) AS count FROM {1} {2} {3}""".format(key, self.table, join, where, order)
            cursor.execute(sql)
            count = cursor.fetchone()["count"]
        except Exception:
            raise

        return count
        
        
class AbsenceTotalOnlineModel(Model) :
    def __init__(self):
        Model.__init__(self)
        self.table = 'visit_plan'
    
    def get_total_user_online(self, cursor, start=0, limit=10000, select='*', join='', where='', order='') :
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e