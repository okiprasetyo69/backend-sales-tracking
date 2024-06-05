import json

from rest.helpers import mysql
from .model import Model

__author__ = 'junior'


class DeliveryCycleModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'delivery_cycle'

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

    def update_by_id(self, cursor, delivery_data):
        try:
            return self.update(cursor, delivery_data, 'id')
        except Exception as e:
            raise e

    def get_delivery_cycle_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_delivery_cycle(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_delivery_cycle(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_count_all_delivery_cycle_statistic(
            self, cursor, select='*', select_count='id', select_form='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_form, join=join, where=where,
                order=order, group=group
            )
        except Exception as e:
            raise e

    def get_delivery_cycle_by_name(self, cursor, name, _id=''):
        try:
            where = "WHERE `user_id` = '{0}' AND `is_deleted` = 0".format(name)
            if _id:
                where = "WHERE `user_id` = '{0}' AND `id` != {1} AND `is_deleted` = 0".format(name, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_delivery_cycle_by_user_cycle(self, cursor, user_id, cycle_number, _id=''):
        try:
            where = "WHERE `user_id` = '{0}' AND `cycle_number` = {1} AND `is_deleted` = 0".format(user_id, cycle_number)
            if _id:
                where = "WHERE `user_id` = '{0}' AND `cycle_number` = {1} AND `id` != {2} AND `is_deleted` = 0".format(
                    user_id, cycle_number, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e


class DeliveryPlanModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'delivery_plan'

    def insert_into_db(
            self, cursor, user_id, asset_id, route, date, destination, destination_order, start_route_branch_id,
            end_route_branch_id, packing_slip_id, is_use_route, create_date, update_date, is_approval, approval_by, create_by
    ):
        try:
            value = {
                "user_id": user_id, "date": date, "asset_id": asset_id, "route": route, "destination": destination,
                "destination_order": destination_order, "start_route_branch_id": start_route_branch_id,
                "end_route_branch_id": end_route_branch_id, "create_date": create_date, "update_date": update_date,
                "is_approval": is_approval, "packing_slip_id": packing_slip_id, "is_use_route": is_use_route,
                "approval_by": approval_by, "create_by": create_by
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, delivery_data):
        try:
            return self.update(cursor, delivery_data, 'id')
        except Exception as e:
            raise e

    def get_delivery_plan_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_delivery_plan(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_delivery_plan(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_count_all_delivery_plan_statistic(
            self, cursor, select='*', select_count='id', select_form='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_form, join=join, where=where,
                order=order, group=group
            )
        except Exception as e:
            raise e

    def get_delivery_plan_by_name(self, cursor, name, _id=''):
        try:
            where = "WHERE `user_id` = '{0}' AND `is_deleted` = 0".format(name)
            if _id:
                where = "WHERE `user_id` = '{0}' AND `id` != {1} AND `is_deleted` = 0".format(name, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_delivery_plan_by_user_date(self, cursor, user_id, date, _id=''):
        try:
            # where = """WHERE `user_id` = '{0}' AND `date` LIKE '{1}%'
            # AND `is_approval` = 1 AND `is_deleted` = 0  AND `status` = 0""".format(user_id, date)
            where = """WHERE `user_id` = '{0}' AND `id` = '{1}' 
            AND `is_approval` = 1 AND `is_deleted` = 0  AND `status` = 0""".format(user_id, date)
            if _id:
                where = """WHERE `user_id` = '{0}' AND `date` LIKE '{1}%' AND `id` != {2}
                AND `is_approval` = 1 AND `is_deleted` = 0  AND `status` = 0""".format(
                    user_id, date, _id
                )
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_delivery_plan_list_by_user_date(self, cursor, user_id, date, _id=''):
        try:
            where = """WHERE `user_id` = '{0}' AND `date` <= '{1} 23:59:59' 
            AND `is_approval` = 1 AND `is_deleted` = 0  AND `status` = 0""".format(user_id, date)
            if _id:
                where = """WHERE `user_id` = '{0}' AND `date` <= '{1} 23:59:59' AND `id` != {2} 
                AND `is_approval` = 1 AND `is_deleted` = 0  AND `status` = 0""".format(
                    user_id, date, _id
                )
            return self.get(cursor, where=where)
        except Exception as e:
            raise e


class DeliveryModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'delivery'

    def insert_into_db(
            self, cursor, packing_slip_code, delivery_date, user_id, customer_code, delivery_plan_id,
            product, is_accepted, accepted_by, is_rejected, rejected_by, reason_reject, create_date, update_date
    ):
        try:
            value = {
                "packing_slip_code": packing_slip_code, "delivery_date": delivery_date, "user_id": user_id,
                "customer_code": customer_code, "delivery_plan_id": delivery_plan_id, "product": product,
                "is_accepted": is_accepted, "accepted_by": accepted_by, "is_rejected": is_rejected,
                "rejected_by": rejected_by, "reason_reject": reason_reject, "create_date": create_date,
                "update_date": update_date
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def get_delivery_by_slip_code(self, cursor, code, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE packing_slip_code = '{}'".format(code))
        except Exception as e:
            raise e

    def update_by_id(self, cursor, delivery_data):
        try:
            return self.update(cursor, delivery_data, 'id')
        except Exception as e:
            raise e

    def get_delivery_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_delivery(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_delivery(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_count_all_delivery_statistic(
            self, cursor, select='*', select_count='id', select_form='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_form, join=join, where=where,
                order=order, group=group
            )
        except Exception as e:
            raise e


class DeliveryPlanSummaryModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = 'delivery_plan_summary'

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

    def get_delivery_plan_summary_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_delivery_plan_summary(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_delivery_plan_summary(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_count_all_delivery_plan_summary_statistic(
            self, cursor, select='*', select_count='id', select_form='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_form, join=join, where=where,
                order='', group=group
            )
        except Exception as e:
            raise e

    def get_delivery_plan_summary_by_plan_id(self, cursor, plan_id, _id=''):
        try:
            where = "WHERE `plan_id` = '{0}' ".format(plan_id)
            if _id:
                where = "WHERE `plan_id` = '{0}' AND `id` != {1} ".format(plan_id, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_delivery_plan_summary_by_customer_code(self, cursor, customer_code, _id=''):
        try:
            where = "WHERE `customer_code` = '{0}' ".format(customer_code)
            if _id:
                where = "WHERE `customer_code` = '{0}' AND `id` != {1} ".format(customer_code, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_delivery_plan_summary_by_plan_id_customer_code(self, cursor, plan_id, customer_code, _id=''):
        try:
            where = "WHERE `plan_id` = '{0}' AND `customer_code` = '{1}' ".format(plan_id, customer_code)
            if _id:
                where = "WHERE `plan_id` = '{0}' AND `customer_code` = '{1}' AND `id` != {1} ".format(plan_id, customer_code, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e
