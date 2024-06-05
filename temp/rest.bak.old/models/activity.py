import json

from rest.helpers import mysql
from .model import Model

__author__ = 'junior'


class SalesActivityModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'sales_activity'

    def insert_into_db(
            self, cursor, user_id, visit_plan_id, nfc_code, route_breadcrumb, distance, total_distance,
            tap_nfc_date, tap_nfc_type, create_date, update_date
    ):
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

    def update_by_id(self, cursor, update_data):
        try:
            return self.update(cursor, update_data, 'id')
        except Exception as e:
            raise e

    def get_activity_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_activity(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_activity(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_count_all_activity_statistic(
            self, cursor, select='*', select_count='', select_from='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_from, join=join, where=where,
                order=order, group=group
            )
        except Exception as e:
            raise e

    def get_activity_by_visit_plan(self, cursor, visit_plan, _id=''):
        try:
            where = "WHERE `visit_plan_id` = '{0}'".format(visit_plan)
            if _id:
                where = "WHERE `visit_plan_id` = '{0}' AND `id` != {1}".format(visit_plan, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e


class SalesActivityBreadcrumbModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'sales_activity_breadcrumb'

    def insert_into_db(
            self, cursor, user_id, visit_plan_id, lat, lng, create_date, update_date
    ):
        try:
            value = {
                "user_id": user_id, "visit_plan_id": visit_plan_id, "lat": lat, "lng": lng,
                "create_date": create_date, "update_date": update_date
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def get_all_activity_breadcrumb(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_activity_breadcrumb(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_activity_breadcrumb_by_visit_plan(self, cursor, visit_plan, _id=''):
        try:
            where = "WHERE `visit_plan_id` = '{0}'".format(visit_plan)
            if _id:
                where = "WHERE `visit_plan_id` = '{0}' AND `id` != {1}".format(visit_plan, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e


class LogisticActivityModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'logistic_activity'

    def insert_into_db(
            self, cursor, user_id, delivery_plan_id, nfc_code, route_breadcrumb, distance, total_distance,
            tap_nfc_date, tap_nfc_type, create_date, update_date
    ):
        try:
            value = {
                "user_id": user_id, "delivery_plan_id": delivery_plan_id, "nfc_code": nfc_code,
                "route_breadcrumb": route_breadcrumb, "distance": distance, "total_distance": total_distance,
                "tap_nfc_date": tap_nfc_date, "tap_nfc_type": tap_nfc_type, "create_date": create_date,
                "update_date": update_date
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, update_data):
        try:
            return self.update(cursor, update_data, 'id')
        except Exception as e:
            raise e

    def get_activity_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_activity(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_activity(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_count_all_activity_statistic(
            self, cursor, select='*', select_count='', select_from='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_from, join=join, where=where,
                order=order, group=group
            )
        except Exception as e:
            raise e

    def get_activity_by_delivery_plan(self, cursor, delivery_plan, _id=''):
        try:
            where = "WHERE `delivery_plan_id` = '{0}'".format(delivery_plan)
            if _id:
                where = "WHERE `delivery_plan_id` = '{0}' AND `id` != {1}".format(delivery_plan, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e


class LogisticActivityBreadcrumbModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'logistic_activity_breadcrumb'

    def insert_into_db(
            self, cursor, user_id, delivery_plan_id, lat, lng, create_date, update_date
    ):
        try:
            value = {
                "user_id": user_id, "delivery_plan_id": delivery_plan_id, "lat": lat, "lng": lng,
                "create_date": create_date, "update_date": update_date
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def get_all_activity_breadcrumb(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_activity_breadcrumb(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_activity_breadcrumb_by_delivery_plan(self, cursor, delivery_plan, _id=''):
        try:
            where = "WHERE `delivery_plan_id` = '{0}'".format(delivery_plan)
            if _id:
                where = "WHERE `delivery_plan_id` = '{0}' AND `id` != {1}".format(delivery_plan, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e


class BreakTimeModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'break_time'

    def insert_into_db(self, cursor, user_id, visit_plan_id, delivery_plan_id, break_time, create_date, update_date):
        try:
            value = {
                "user_id": user_id, "visit_plan_id": visit_plan_id, "delivery_plan_id": delivery_plan_id,
                "break_time": break_time, "create_date": create_date, "update_date": update_date
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def get_count_all_break_time_statistic(
            self, cursor, select='*', select_count='', select_form='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_form, join=join, where=where,
                order=order, group=group
            )
        except Exception as e:
            raise e


class IdleTimeModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'idle_time'

    def insert_into_db(self, cursor, user_id, visit_plan_id, delivery_plan_id, idle_time, create_date, update_date):
        try:
            value = {
                "user_id": user_id, "visit_plan_id": visit_plan_id, "delivery_plan_id": delivery_plan_id,
                "idle_time": idle_time, "create_date": create_date, "update_date": update_date
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def get_count_all_idle_time_statistic(
            self, cursor, select='*', select_count='', select_form='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_form, join=join, where=where,
                order=order, group=group
            )
        except Exception as e:
            raise e