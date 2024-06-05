import json

from rest.helpers import mysql
from .model import Model

__author__ = 'junior'


class VisitCycleModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'visit_cycle'

    def insert_into_db(self, cursor, user_id, asset_id, cycle_number, cycle_monday, cycle_tuesday, cycle_wednesday,
                       cycle_thursday, cycle_friday, cycle_saturday, cycle_sunday, create_date, update_date,
                       is_approval, approval_by, create_by):
        try:
            value = {
                "user_id": user_id, "asset_id": asset_id, "cycle_number": cycle_number, "cycle_monday": cycle_monday,
                "cycle_tuesday": cycle_tuesday, "cycle_wednesday": cycle_wednesday, "cycle_thursday": cycle_thursday,
                "cycle_friday": cycle_friday, "cycle_saturday": cycle_saturday, "cycle_sunday": cycle_sunday,
                "create_date": create_date, "update_date": update_date, "is_approval": is_approval,
                "approval_by": approval_by, "create_by": create_by
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def import_insert(self, cursor, data, key):
        try:
            return self.insert_update(cursor, data, key)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, visit_data):
        try:
            return self.update(cursor, visit_data, 'id')
        except Exception as e:
            raise e

    def get_visit_cycle_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_visit_cycle(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_visit_cycle(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_count_all_visit_cycle_statistic(
            self, cursor, select='*', select_count='id', select_form='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_form, join=join, where=where,
                order='', group=group
            )
        except Exception as e:
            raise e

    def get_visit_cycle_by_name(self, cursor, name, _id=''):
        try:
            where = "WHERE `user_id` = '{0}' AND `is_deleted` = 0".format(name)
            if _id:
                where = "WHERE `user_id` = '{0}' AND `id` != {1} AND `is_deleted` = 0".format(name, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_visit_cycle_by_user_cycle(self, cursor, user_id, cycle_number, _id=''):
        try:
            where = "WHERE `user_id` = '{0}' AND `cycle_number` = {1} AND `is_deleted` = 0".format(user_id, cycle_number)
            if _id:
                where = "WHERE `user_id` = '{0}' AND `cycle_number` = {1} AND `id` != {2} AND `is_deleted` = 0".format(
                    user_id, cycle_number, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e


class VisitPlanModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'visit_plan'

    def insert_into_db(
            self, cursor, user_id, asset_id, route, date, destination, destination_order, start_route_branch_id,
            end_route_branch_id, invoice_id, is_use_route, create_date, update_date, is_approval, approval_by, create_by
    ):
        try:
            value = {
                "user_id": user_id, "date": date, "asset_id": asset_id, "route": route, "destination": destination,
                "destination_order": destination_order, "start_route_branch_id": start_route_branch_id,
                "end_route_branch_id": end_route_branch_id, "create_date": create_date, "update_date": update_date,
                "is_approval": is_approval, "invoice_id": invoice_id, "is_use_route": is_use_route,
                "approval_by": approval_by, "create_by": create_by
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, visit_data):
        try:
            return self.update(cursor, visit_data, 'id')
        except Exception as e:
            raise e

    def get_visit_plan_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_visit_plan(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_visit_plan(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_count_all_visit_plan_statistic(
            self, cursor, select='*', select_count='id', select_form='', join='', where='', order='', group=''
    ):
        try:
            query = self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_form, join=join, where=where,
                order='', group=group
            )
            # print("query : ", query)
            return query
            # return self.get_sql_count_statistic(
            #     cursor, key=select, key_count=select_count, from_select=select_form, join=join, where=where,
            #     order='', group=group
            # )
        except Exception as e:
            raise e

    def get_visit_plan_by_name(self, cursor, name, _id=''):
        try:
            where = "WHERE `user_id` = '{0}' AND `is_deleted` = 0".format(name)
            if _id:
                where = "WHERE `user_id` = '{0}' AND `id` != {1} AND `is_deleted` = 0".format(name, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_visit_plan_by_user_date(self, cursor, user_id, date, _id=''):
        try:
            order = "ORDER BY id ASC"
            where = """WHERE `user_id` = '{0}' AND `date` LIKE '{1}%' 
            AND `is_approval` = 1 AND `is_deleted` = 0 AND `status` = 0""".format(user_id, date)
            if _id:
                where = """WHERE `user_id` = '{0}' AND `date` LIKE '{1}%' AND `id` != {2} 
                AND `is_approval` = 1 AND `is_deleted` = 0 AND `status` = 0""".format(
                    user_id, date, _id
                )
            return self.get(cursor, where=where, order=order)
        except Exception as e:
            raise e


class VisitPlanSummaryModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'visit_plan_summary'

    def insert_into_db(
            self, cursor, plan_id, customer_code, notes, visit_images, have_competitor, competitor_images,
            create_date, update_date, create_by
    ):
        try:
            value = {
                "plan_id": plan_id, "customer_code": customer_code, "notes": notes, "visit_images": visit_images,
                "have_competitor": have_competitor, "competitor_images": competitor_images,
                "create_date": create_date, "update_date": update_date, "create_by": create_by
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, update_data):
        try:
            return self.update(cursor, update_data, 'id')
        except Exception as e:
            raise e

    def get_visit_plan_summary_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_visit_plan_summary(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_visit_plan_summary(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_count_all_visit_plan_summary_statistic(
            self, cursor, select='*', select_count='id', select_form='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_form, join=join, where=where,
                order='', group=group
            )
        except Exception as e:
            raise e

    def get_visit_plan_summary_by_plan_id(self, cursor, plan_id, _id=''):
        try:
            where = "WHERE `plan_id` = '{0}' ".format(plan_id)
            if _id:
                where = "WHERE `plan_id` = '{0}' AND `id` != {1} ".format(plan_id, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_visit_plan_summary_by_customer_code(self, cursor, customer_code, _id=''):
        try:
            where = "WHERE `customer_code` = '{0}' ".format(customer_code)
            if _id:
                where = "WHERE `customer_code` = '{0}' AND `id` != {1} ".format(customer_code, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_visit_plan_summary_by_plan_id_customer_code(self, cursor, plan_id, customer_code, _id=''):
        try:
            where = "WHERE `plan_id` = '{0}' AND `customer_code` = '{1}' ".format(plan_id, customer_code)
            if _id:
                where = "WHERE `plan_id` = '{0}' AND `customer_code` = '{1}' AND `id` != {1} ".format(plan_id, customer_code, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_lastest_competitor_product_by_customer_code(self, cursor, customer_code):
        try:
            select = "id, customer_code, competitor_images, create_date"
            where = "WHERE customer_code='{0}' ORDER BY id DESC LIMIT 1".format(customer_code)
            return self.get(cursor, fields=select, where=where)
        except Exception as e:
            raise e