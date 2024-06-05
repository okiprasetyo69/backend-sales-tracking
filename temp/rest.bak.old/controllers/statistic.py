import re
import json
import time
import pandas as pd
import dateutil.parser

from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql, auto_correction_number_none
from rest.models import VisitPlanModel, SalesActivityModel, PermissionsModel, BranchesModel, PermissionsModel, \
    BreakTimeModel, SalesPaymentMobileModel, SalesOrderModel, RequestOrderModel, DeliveryCycleModel, \
    DeliveryPlanModel, DeliveryModel, PackingSlipModel, LogisticActivityModel

__author__ = 'Junior'


class SalesStatisticController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.visit_plan_model = VisitPlanModel()
        self.sales_activity_model = SalesActivityModel()
        self.branches_model = BranchesModel()
        self.permissions_model = PermissionsModel()
        self.break_time_model = BreakTimeModel()
        self.spm_model = SalesPaymentMobileModel()
        self.so_model = SalesOrderModel()
        self.ro_model = RequestOrderModel()

    def get_statistic_visit(self, branch_privilege: list, division_privilege: list, start_date: str, end_date: str):
        """

        :param branch_privilege: list
        :param division_privilege: list
        :param start_date: str
        :param end_date: str
        :return:
        statistic performance visit
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")

        # TODO: Get statitistic Visited plan
        select = "br.id, br.name"
        select_count = ", SUM(JSON_LENGTH(vp.destination)) as total"
        join = """as vp LEFT JOIN `users` as u ON vp.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_vp = """WHERE (vp.is_deleted = 0 AND vp.is_approval = 1) 
        AND (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_vp += """AND (vp.date >= '{0} 00:00:00' AND vp.date <= '{1} 23:59:59') """.format(start_date,
                                                                                                    end_date)
        else:
            where_vp += """AND (vp.date LIKE '{}%')""".format(today)
        group = """GROUP BY u.branch_id"""
        count_plan = self.visit_plan_model.get_count_all_visit_plan_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_vp, group=group
        )
        # TODO: Get Statistitic Actual Plan
        select = "br.id, br.name"
        select_from = """( SELECT act.* FROM (SELECT id, user_id, visit_plan_id, 
        REPLACE(nfc_code, " ", "") as nfc_code, tap_nfc_date, tap_nfc_type FROM sales_activity) as act 
        WHERE act.tap_nfc_type = 'IN' GROUP BY act.visit_plan_id, act.nfc_code, act.tap_nfc_type )"""
        select_count = ", COUNT(sa.id) as total"
        order = ''
        join = """as sa LEFT JOIN `users` as u ON sa.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_sa = """WHERE (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_sa += """AND (sa.tap_nfc_date >= '{0} 00:00:00' AND sa.tap_nfc_date <= '{1} 23:59:59') """.format(
                start_date, end_date)
        else:
            where_sa += """AND (sa.tap_nfc_date LIKE '{}%')""".format(today)
        group = """GROUP BY u.branch_id"""
        count_actual = self.sales_activity_model.get_count_all_activity_statistic(
            self.cursor, select=select, select_count=select_count, select_from=select_from, join=join,
            where=where_sa, order=order, group=group
        )
        where_br = """WHERE (is_deleted = 0 AND is_approval = 1) AND id IN ({0}) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        result = self.branches_model.get_all_branches(self.cursor, where=where_br, start=0, limit=1000)

        data_statistic_visit = dict()
        data_branch = []

        total_plan = 0
        total_visited = 0
        total_cancel = 0
        for res in result:
            plan = 0
            actual = 0
            if count_plan:
                for rec in count_plan:
                    if rec['id'] == res['id']:
                        plan += int(rec['total'])
                        if count_actual:
                            for rec_actual in count_actual:
                                if rec_actual['id'] == rec['id']:
                                    actual += int(rec_actual['total'])
            cancel = plan - actual
            data_plan_actual = {
                res['name']: {
                    "plan": plan,
                    "actual": actual,
                    "cancel": cancel
                }
            }
            data_branch.append(data_plan_actual)
            total_plan += plan
            total_visited += actual
            total_cancel += cancel

        data_total = {
            'plan': total_plan,
            'visited': total_visited,
            'cancel': total_cancel
        }
        data_statistic_visit['total_visit_actual'] = data_total
        data_statistic_visit['data_visit_actual'] = data_branch

        return data_statistic_visit

    def get_statistic_activities(self, branch_privilege: list, division_privilege: list, start_date: str,
                                 end_date: str):
        """

        :param branch_privilege: list
        :param division_privilege: list
        :param start_date: str
        :param end_date: str
        :return:
        statistic performance activities
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")

        # Init Value
        total_driving_time = 0
        total_visit_time = 0
        total_break_time = 0

        # TODO: Get statistic Driving and Visit Time
        select = "br.id, br.name, sa.tap_nfc_date, sa.visit_plan_id, sa.nfc_code, sa.tap_nfc_type"
        select_from = """( SELECT id, user_id, visit_plan_id, 
        REPLACE(nfc_code, " ", "") as nfc_code, tap_nfc_date, tap_nfc_type FROM sales_activity )"""
        order = 'ORDER BY sa.tap_nfc_date ASC'
        join = """as sa LEFT JOIN `users` as u ON sa.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_sa = """WHERE (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_sa += """AND (sa.tap_nfc_date >= '{0} 00:00:00' 
            AND sa.tap_nfc_date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_sa += """AND (sa.tap_nfc_date LIKE '{}%')""".format(today)
        group = """GROUP BY sa.visit_plan_id, sa.nfc_code, sa.tap_nfc_type"""
        drive_time = self.sales_activity_model.get_count_all_activity_statistic(
            self.cursor, select=select, select_from=select_from, join=join,
            where=where_sa, order=order, group=group
        )
        data_drive_time = []
        batch_data_driver = []
        batch_data_visit = []
        if drive_time:
            for rec in drive_time:
                data_drive_time.append(rec)

            df = pd.DataFrame(data_drive_time)
            # TODO: Calculate total drive time
            df_group = df.groupby(['id', 'visit_plan_id'])['tap_nfc_date'].agg(['first', 'last'])
            df_group['diff'] = df_group['last'] - df_group['first']
            df_group['diff'] = df_group['diff'].astype('timedelta64[m]')
            df_group_total = df_group.groupby(['id'])['diff'].sum().reset_index(name='total')
            df_group_total.set_index("id", inplace=True)
            df_group_total['total'] = df_group_total['total'].astype(int)
            df_group_total.index.names = ['id']

            df_driver_json = df_group_total.to_json(orient='index', date_format='iso')
            df_driver_json = json.loads(df_driver_json)
            for key, val in df_driver_json.items():
                value = val
                value['id'] = key
                batch_data_driver.append(value)
            # print(df_group_total.head(20))
            # print(df_driver_json)

            # TODO: Calculate total visit time
            # df_visit = df[df['tap_nfc_type'].isin(['IN', 'OUT'])]
            # df_visit_group = df_visit.groupby(['id', 'nfc_code', 'visit_plan_id'])['tap_nfc_date'].agg(['first', 'last'])
            # df_visit_group['diff'] = df_visit_group['last'] - df_visit_group['first']
            # df_visit_group['diff'] = df_visit_group['diff'].astype('timedelta64[m]')
            # df_visit_group_total = df_visit_group.groupby(['id'])['diff'].sum().reset_index(name ='total')
            # df_visit_group_total.set_index("id", inplace=True)
            # df_visit_group_total['total'] = df_visit_group_total['total'].astype(int)
            # df_visit_group_total.index.names = ['id']
            #
            # df_visit_json = df_visit_group_total.to_json(orient='index', date_format='iso')
            # df_visit_json = json.loads(df_visit_json)
            # for key, val in df_visit_json.items():
            #     value = val
            #     value['id'] = key
            #     batch_data_visit.append(value)
            # print(df_visit_group_total.head(20))
            # print(df_visit_json)

        # TODO: Get statistic Visit Time
        select = "br.id, br.name, sa.tap_nfc_date, sa.visit_plan_id, sa.nfc_code, sa.tap_nfc_type"
        select_from = """( SELECT id, user_id, visit_plan_id, 
        REPLACE(nfc_code, " ", "") as nfc_code, tap_nfc_date, tap_nfc_type FROM sales_activity )"""
        order = 'ORDER BY sa.tap_nfc_date ASC'
        join = """as sa LEFT JOIN `users` as u ON sa.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_sa = """WHERE (u.branch_id IN ({0}) AND u.division_id IN ({1})) AND sa.tap_nfc_type IN ('IN', 'OUT') """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_sa += """AND (sa.tap_nfc_date >= '{0} 00:00:00' 
            AND sa.tap_nfc_date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_sa += """AND (sa.tap_nfc_date LIKE '{}%')""".format(today)
        group = """"""
        visit_time = self.sales_activity_model.get_count_all_activity_statistic(
            self.cursor, select=select, select_from=select_from, join=join,
            where=where_sa, order=order, group=group
        )
        data_visit_time = []
        data_visit_group_time = []
        batch_data_visit_time = []
        if visit_time:
            counter_code = {}
            flag_record = {}
            for rec in visit_time:
                counter_code[rec['nfc_code']] = 1
                flag_record[rec['nfc_code']] = False
                data_visit_time.append(rec)
            idx = 0
            for rc in data_visit_time:
                if flag_record[rc['nfc_code']]:
                    counter_code[rc['nfc_code']] += 1
                    flag_record[rc['nfc_code']] = False
                if rc['tap_nfc_type'] == 'IN':
                    rc['counter'] = counter_code[rc['nfc_code']]
                if rc['tap_nfc_type'] == 'OUT':
                    if idx != 0:
                        cur_idx = idx
                        prev_idx = cur_idx - 1
                        while prev_idx >= 0:
                            if data_visit_time[prev_idx]['nfc_code'] == rc['nfc_code'] and data_visit_time[prev_idx][
                                'tap_nfc_type'] == 'IN':
                                rc['counter'] = counter_code[rc['nfc_code']]
                                flag_record[rc['nfc_code']] = True
                                break
                            prev_idx -= 1
                idx += 1
                data_visit_group_time.append(rc)
            df = pd.DataFrame(data_visit_group_time)
            # df_visit_time = df[df['tap_nfc_type'].isin(['IN', 'OUT'])]
            df_visit_time_group = df.groupby(['id', 'nfc_code', 'visit_plan_id', 'counter'])['tap_nfc_date'].agg(
                ['first', 'last'])
            df_visit_time_group['diff'] = df_visit_time_group['last'] - df_visit_time_group['first']
            df_visit_time_group['diff'] = df_visit_time_group['diff'].astype('timedelta64[m]')
            df_visit_time_group_total = df_visit_time_group.groupby(['id'])['diff'].sum().reset_index(name='total')
            df_visit_time_group_total.set_index("id", inplace=True)
            df_visit_time_group_total['total'] = df_visit_time_group_total['total'].astype(int)
            df_visit_time_group_total.index.names = ['id']

            df_visit_time_json = df_visit_time_group_total.to_json(orient='index', date_format='iso')
            df_visit_time_json = json.loads(df_visit_time_json)
            for key, val in df_visit_time_json.items():
                value = val
                value['id'] = key
                batch_data_visit.append(value)

        # TODO: Get statistic Break Time
        select = "br.id, br.name, CAST(SUM(bt.break_time) as UNSIGNED) as total"
        order = 'ORDER BY bt.create_date ASC'
        join = """as bt LEFT JOIN `users` as u ON bt.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_bt = """WHERE (u.branch_id IN ({0}) AND u.division_id IN ({1}) 
        AND visit_plan_id IS NOT NULL) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_bt += """AND (bt.create_date >= '{0} 00:00:00' 
                    AND bt.create_date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_bt += """AND (bt.create_date LIKE '{}%')""".format(today)
        group = """GROUP BY br.id"""
        break_time = self.break_time_model.get_count_all_break_time_statistic(
            self.cursor, select=select, join=join, where=where_bt, order=order, group=group
        )

        # TODO: SUM all total
        if batch_data_driver:
            for rec_driver in batch_data_driver:
                total_driving_time += rec_driver['total']
        if batch_data_visit:
            for rec_visit in batch_data_visit:
                total_visit_time += rec_visit['total']
        if break_time:
            for rec_break in break_time:
                total_break_time += rec_break['total']
        data_return = {
            'Driving Time': total_driving_time - total_visit_time,
            'Stop Time': total_visit_time,
            'Break Time': int(total_break_time / 60)
        }
        return data_return

    def get_statistic_permission_alert(self, branch_privilege: list, division_privilege: list,
                                       start_date: str, end_date: str):
        """

        :param branch_privilege: list
        :param division_privilege: list
        :param start_date: str
        :param end_date: str
        :return:
        statistic performance permission alert
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")
        data_statistic_permission_alert = dict()

        # TODO: Get statistic Alert
        select = "br.id, br.name"
        select_count = ", COUNT(al.id) as total"
        order = 'ORDER BY al.date ASC'
        join = """as al LEFT JOIN `users` as u ON al.create_by = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id 
        LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_al = """WHERE (al.type = 'alert') AND (e.job_function = 'sales' AND u.branch_id IN ({0}) 
        AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_al += """AND (al.date >= '{0} 00:00:00' 
            AND al.date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_al += """AND (al.date LIKE '{}%')""".format(today)
        count_alert = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_al, order=order
        )

        # TODO: Get statistic Permission
        select = "br.id, br.name"
        select_count = ", COUNT(al.id) as total"
        order = 'ORDER BY al.date ASC'
        join = """as al LEFT JOIN `users` as u ON al.create_by = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id 
        LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_al = """WHERE (al.type IN ('routes', 'break_time', 'visit_time', 'print', 'report')) 
        AND (e.job_function = 'sales' AND u.branch_id IN ({0}) 
        AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_al += """AND (al.date >= '{0} 00:00:00' 
            AND al.date <= '{1} 23:59:59')""".format(start_date, end_date)
        else:
            where_al += """AND (al.date LIKE '{}%')""".format(today)
        count_permission = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_al, order=order
        )

        where_br = """WHERE (is_deleted = 0 AND is_approval = 1) AND id IN ({0}) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        result = self.branches_model.get_all_branches(self.cursor, where=where_br, start=0, limit=1000)
        branch_alert = []
        branch_permission = []
        for res in result:
            total_alert = 0
            total_permission = 0
            for rec_alert in count_alert:
                if rec_alert['id'] == res['id']:
                    total_alert += int(rec_alert['total'])

            for rec_permission in count_permission:
                if rec_permission['id'] == res['id']:
                    total_permission += int(rec_permission['total'])

            branch_alert.append({
                res['name']: total_alert
            })
            branch_permission.append({
                res['name']: total_permission
            })
        data_statistic_permission_alert['data_statistic_alert'] = branch_alert
        data_statistic_permission_alert['data_statistic_permission'] = branch_permission
        return data_statistic_permission_alert

    def get_statistic_invoice(self, branch_privilege: list, division_privilege: list,
                              start_date: str, end_date: str):
        """

        :param branch_privilege: list
        :param division_privilege: list
        :param start_date: str
        :param end_date: str
        :return:
        statistic performance about orders
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")
        data_statistic_invoice = dict()

        # TODO: Get statitistic Invoice from Visited plan
        select = "br.id, br.name"
        select_count = ", SUM(JSON_LENGTH(vp.invoice_id)) as total"
        join = """as vp LEFT JOIN `users` as u ON vp.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_vp = """WHERE (vp.is_deleted = 0 AND vp.is_approval = 1) 
                AND (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_vp += """AND (vp.date >= '{0} 00:00:00' AND vp.date <= '{1} 23:59:59')""".format(start_date, end_date)
        else:
            where_vp += """AND (vp.date LIKE '{}%')""".format(today)
        group = """GROUP BY u.branch_id"""
        count_invoice = self.visit_plan_model.get_count_all_visit_plan_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_vp, group=group
        )

        # TODO: Get Statistic Payment
        select = """br.id, br.name, CAST(SUM(spm.invoice_amount) as UNSIGNED) as inv_amount, 
        CAST(SUM(spm.payment_amount) as UNSIGNED) as pay_amount"""
        select_count = ", SUM(JSON_LENGTH(spm.invoice)) as total"
        join = """as spm LEFT JOIN `users` as u ON spm.create_by = u.id 
        LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_spm = """WHERE (spm.is_confirm = 1) AND (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_spm += """AND (spm.create_date >= '{0} 00:00:00' AND spm.create_date <= '{1} 23:59:59')""".format(
                start_date, end_date)
        else:
            where_spm += """AND (spm.create_date LIKE '{}%')""".format(today)
        group = """GROUP BY u.branch_id"""
        count_payment = self.spm_model.get_count_all_sales_payment_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_spm, group=group
        )

        # TODO: Get Statistic Invoice and Payment Without Confirm
        select = """br.id, br.name, CAST(SUM(spm.invoice_amount) as UNSIGNED) as inv_amount, 
                        CAST(SUM(spm.payment_amount) as UNSIGNED) as pay_amount"""
        select_count = ", SUM(JSON_LENGTH(spm.invoice)) as total"
        join = """as spm LEFT JOIN `users` as u ON spm.create_by = u.id
        LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_spm_inv_wo = """WHERE (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_spm_inv_wo += """AND (spm.create_date >= '{0} 00:00:00' AND spm.create_date <= '{1} 23:59:59')""".format(
                start_date, end_date)
        else:
            where_spm_inv_wo += """AND (spm.create_date LIKE '{}%')""".format(today)
        group = """GROUP BY u.branch_id"""
        count_inv_pay_wo = self.spm_model.get_count_all_sales_payment_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_spm_inv_wo, group=group
        )

        where_br = """WHERE (is_deleted = 0 AND is_approval = 1) AND id IN ({0}) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        result = self.branches_model.get_all_branches(self.cursor, where=where_br, start=0, limit=1000)

        data_branch = []
        total_invoice = 0
        total_payment = 0
        total_pay_wo = 0
        total_invoice_amount = 0
        total_payment_amount = 0
        total_pay_amount_wo = 0
        for res in result:
            invoice = 0
            payment = 0
            payment_wo = 0
            if count_invoice:
                for rec in count_invoice:
                    if rec['id'] == res['id']:
                        invoice += (int(rec['total']) if (rec['total'] is not None) else 0)
                        if count_payment:
                            for rec_pay in count_payment:
                                if rec_pay['id'] == rec['id']:
                                    payment += int(rec_pay['total'])
                                    total_invoice_amount += int(rec_pay['inv_amount'])
                                    total_payment_amount += int(rec_pay['pay_amount'])
                        if count_inv_pay_wo:
                            for rec_pay_wo in count_inv_pay_wo:
                                if rec_pay_wo['id'] == rec['id']:
                                    payment_wo += int(rec_pay_wo['total'])
                                    total_pay_amount_wo += int(rec_pay_wo['pay_amount'])
            data_inv_pay = {
                res['name']: {
                    "invoice": invoice,
                    "payment": payment,
                    "payment_wo": payment_wo
                }
            }
            data_branch.append(data_inv_pay)
            total_invoice += invoice
            total_payment += payment
            total_pay_wo += payment_wo

        data_total = {
            'invoice': total_invoice,
            'payment': total_payment,
            'payment_wo': total_pay_wo
        }
        data_total_amount = {
            'invoice': total_invoice_amount,
            'payment': total_payment_amount,
            'payment_wo': total_pay_amount_wo
        }
        data_statistic_invoice['total_invoice_payment'] = data_total
        data_statistic_invoice['total_amount'] = data_total_amount
        data_statistic_invoice['data_invoice_payment'] = data_branch
        return data_statistic_invoice

    def get_statistic_orders(self, branch_privilege: list, division_privilege: list, start_date: str, end_date: str):
        """

        :param branch_privilege: list
        :param division_privilege: list
        :param start_date: str
        :param end_date: str
        :return:
        statistic performance about orders
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")
        data_statistic_orders = dict()

        # TODO: Get statitistic Request Order
        select = "br.id, br.name"
        select_count = ", COUNT(ro.id) as total"
        join = """as ro LEFT JOIN `users` as u ON ro.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_ro = """WHERE (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_ro += """AND (ro.date >= '{0} 00:00:00' AND ro.date <= '{1} 23:59:59')""".format(start_date, end_date)
        else:
            where_ro += """AND (ro.date LIKE '{}%')""".format(today)
        group = """GROUP BY u.branch_id"""
        count_ro = self.ro_model.get_count_all_request_order_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_ro, group=group
        )

        # TODO: Get Statistic Sales Order
        select = """br.id, br.name"""
        select_count = ", COUNT(so.code) as total"
        join = """as so LEFT JOIN `users` as u ON so.user_code = u.username 
        LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        # where_so = """WHERE (so.invoice_code is NULL AND (so.status != "canceled" OR so.status is NULL))
        # AND (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
        #     ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        # )
        where_so = """WHERE (so.status != "canceled" OR so.status is NULL) 
        AND (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_so += """AND (so.create_date >= '{0} 00:00:00' AND so.create_date <= '{1} 23:59:59')""".format(
                start_date, end_date)
        else:
            where_so += """AND (so.create_date LIKE '{}%')""".format(today)
        group = """GROUP BY u.branch_id"""
        count_so = self.so_model.get_count_all_sales_order_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_so, group=group
        )

        where_br = """WHERE (is_deleted = 0 AND is_approval = 1) AND id IN ({0}) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        result = self.branches_model.get_all_branches(self.cursor, where=where_br, start=0, limit=1000)

        data_branch = []
        total_ro = 0
        total_so = 0
        for res in result:
            ro = 0
            so = 0
            if count_ro:
                for rec in count_ro:
                    if rec['id'] == res['id']:
                        ro += int(rec['total'])
                        if count_so:
                            for rec_so in count_so:
                                if rec_so['id'] == rec['id']:
                                    so += int(rec_so['total'])
            data_ro_so = {
                res['name']: {
                    "Request Order": ro,
                    "Sales Order": so
                }
            }
            data_branch.append(data_ro_so)
            total_ro += ro
            total_so += so

        data_total = {
            'Request Order': total_ro,
            'Sales Order': total_so
        }
        data_statistic_orders['total_ro_so'] = data_total
        data_statistic_orders['data_ro_so'] = data_branch
        return data_statistic_orders

    def get_statistic_report(self, branch_privilege: list, division_privilege: list, start_date: str, end_date: str):
        """

        :param branch_privilege: list
        :param division_privilege: list
        :param start_date: str
        :param end_date: str
        :return:
        statistic performance about report
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")

        # TODO: Get statitistic Permission Report NFC
        select = "br.id, br.name"
        select_count = ", COUNT(al.id) as total"
        order = 'ORDER BY al.date ASC'
        join = """as al LEFT JOIN `users` as u ON al.create_by = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id 
        LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_nfc = """WHERE (al.type = 'report' AND JSON_CONTAINS(al.description, '{{\"type\": \"nfc\"}}')) 
        AND (e.job_function = 'sales' AND u.branch_id IN ({0}) 
        AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_nfc += """AND (al.date >= '{0} 00:00:00' 
            AND al.date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_nfc += """AND (al.date LIKE '{}%')""".format(today)
        count_nfc = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_nfc, order=order
        )

        # TODO: Get statitistic Permission Report Print
        select = "br.id, br.name"
        select_count = ", COUNT(al.id) as total"
        order = 'ORDER BY al.date ASC'
        join = """as al LEFT JOIN `users` as u ON al.create_by = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id 
        LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_print = """WHERE (al.type = 'report' AND JSON_CONTAINS(al.description, '{{\"type\": \"print\"}}')) 
        AND (e.job_function = 'sales' AND u.branch_id IN ({0}) 
        AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_print += """AND (al.date >= '{0} 00:00:00' 
            AND al.date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_print += """AND (al.date LIKE '{}%')""".format(today)
        count_print = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_print, order=order
        )

        # TODO: Get Statistic Payment reprint and cancel
        select = """br.id, br.name, CAST(SUM(spm.is_canceled) as UNSIGNED) as cancel, 
        CAST(SUM(spm.receipt_reprint) as UNSIGNED) as reprint"""
        select_count = ''
        join = """as spm LEFT JOIN `users` as u ON spm.create_by = u.id 
        LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_spm = """WHERE (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_spm += """AND (spm.create_date >= '{0} 00:00:00' AND spm.create_date <= '{1} 23:59:59') """.format(
                start_date, end_date)
        else:
            where_spm += """AND (spm.create_date LIKE '{}%')""".format(today)
        group = """GROUP BY u.branch_id"""
        count_reprint_cancel = self.spm_model.get_count_all_sales_payment_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_spm, group=group
        )

        # TODO: Get Statistic Permission Report Location
        select = "br.id, br.name"
        select_count = ", COUNT(al.id) as total"
        order = 'ORDER BY al.date ASC'
        join = """as al LEFT JOIN `users` as u ON al.create_by = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id 
        LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_location = """WHERE (al.type = 'report' AND JSON_CONTAINS(al.description, '{{\"type\": \"location\"}}')) 
        AND (e.job_function = 'sales' AND u.branch_id IN ({0}) 
        AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        if start_date and end_date:
            where_location += """AND (al.date >= '{0} 00:00:00' 
            AND al.date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_location += """AND (al.date LIKE '{}%')""".format(today)
        count_location = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_location, order=order
        )

        total_nfc = 0
        total_location = 0
        total_print = 0
        total_cancel = 0
        total_reprint = 0

        if count_nfc:
            for nfc in count_nfc:
                total_nfc += int(nfc['total'])
        if count_location:
            for location in count_location:
                total_location += int(location['total'])
        if count_print:
            for pr in count_print:
                total_print += int(pr['total'])
        if count_reprint_cancel:
            for rpc in count_reprint_cancel:
                total_reprint += int(rpc['reprint'])
                total_cancel += int(rpc['cancel'])

        data = {
            'Report NFC': total_nfc,
            'Report Location': total_location,
            'Report Print': total_print,
            'Reprint Receipe': total_reprint,
            'Payment Cancelled': total_cancel
        }
        return data


class LogisticStatisticController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.branches_model = BranchesModel()
        self.delivery_cycle_model = DeliveryCycleModel()
        self.delivery_plan_model = DeliveryPlanModel()
        self.delivery_model = DeliveryModel()
        self.permissions_model = PermissionsModel()
        self.break_time_model = BreakTimeModel()
        self.so_model = SalesOrderModel()
        self.packing_slip_model = PackingSlipModel()
        self.logistic_activity_model = LogisticActivityModel()

    def get_statistic_delivery(self, branch_privilege: list, start_date: str, end_date: str):
        """

        :param branch_privilege: list
        :param division_privilege: list
        :param start_date: str
        :param end_date: str
        :return:
        statistic performance visit
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")

        # TODO: Get statitistic Delivery plan
        select = "br.id, br.name"
        select_count = ", SUM(JSON_LENGTH(dp.destination)) as total"
        join = """as dp LEFT JOIN `users` as u ON dp.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_dp = """WHERE (dp.is_deleted = 0 AND dp.is_approval = 1) 
        AND (u.branch_id IN ({0})) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        if start_date and end_date:
            where_dp += """AND (dp.date >= '{0} 00:00:00' AND dp.date <= '{1} 23:59:59') """.format(start_date,
                                                                                                    end_date)
        else:
            where_dp += """AND (dp.date LIKE '{}%')""".format(today)
        group = """GROUP BY u.branch_id"""
        count_plan = self.delivery_plan_model.get_count_all_delivery_plan_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_dp, group=group
        )

        # TODO: Get Statistitic Actual Plan
        select = "br.id, br.name"
        select_count = ", COUNT(dd.id) as total"
        join = """as dd LEFT JOIN `users` as u ON dd.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_dd = """WHERE (u.branch_id IN ({0})) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        if start_date and end_date:
            where_dd += """AND (dd.delivery_date >= '{0} 00:00:00' 
            AND dd.delivery_date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_dd += """AND (dd.delivery_date LIKE '{}%')""".format(today)
        group = """GROUP BY u.branch_id"""
        count_actual = self.delivery_model.get_count_all_delivery_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_dd, group=group
        )

        where_br = """WHERE (is_deleted = 0 AND is_approval = 1) AND id IN ({0}) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        result = self.branches_model.get_all_branches(self.cursor, where=where_br, start=0, limit=1000)

        data_statistic_visit = dict()
        data_branch = []

        total_plan = 0
        total_visited = 0
        total_cancel = 0
        for res in result:
            plan = 0
            actual = 0
            if count_plan:
                for rec in count_plan:
                    if rec['id'] == res['id']:
                        plan += int(rec['total'])
                        if count_actual:
                            for rec_actual in count_actual:
                                if rec_actual['id'] == rec['id']:
                                    actual += int(rec_actual['total'])
            cancel = plan - actual
            data_plan_actual = {
                res['name']: {
                    "plan": plan,
                    "actual": actual,
                    "cancel": cancel
                }
            }
            data_branch.append(data_plan_actual)
            total_plan += plan
            total_visited += actual
            total_cancel += cancel

        data_total = {
            'plan': total_plan,
            'delivery': total_visited,
            'cancel': total_cancel
        }
        data_statistic_visit['total_delivery_actual'] = data_total
        data_statistic_visit['data_delivery_actual'] = data_branch

        return data_statistic_visit

    def get_statistic_report(self, branch_privilege: list, start_date: str, end_date: str):
        """

        :param branch_privilege: list
        :param start_date: str
        :param end_date: str
        :return:
        statistic performance about report
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")

        # TODO: Get statitistic Permission Report NFC
        select = "br.id, br.name"
        select_count = ", COUNT(al.id) as total"
        order = 'ORDER BY al.date ASC'
        join = """as al LEFT JOIN `users` as u ON al.create_by = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id 
        LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_nfc = """WHERE (al.type = 'report' AND JSON_CONTAINS(al.description, '{{\"type\": \"nfc\"}}')) 
        AND ((e.job_function = 'driver' OR e.job_function = 'crew') AND u.branch_id IN ({0})) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        if start_date and end_date:
            where_nfc += """AND (al.date >= '{0} 00:00:00' 
            AND al.date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_nfc += """AND (al.date LIKE '{}%')""".format(today)
        count_nfc = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_nfc, order=order
        )

        # TODO: Get Statistic Permission Report Location
        select = "br.id, br.name"
        select_count = ", COUNT(al.id) as total"
        order = 'ORDER BY al.date ASC'
        join = """as al LEFT JOIN `users` as u ON al.create_by = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id 
        LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_location = """WHERE (al.type = 'report' AND JSON_CONTAINS(al.description, '{{\"type\": \"location\"}}')) 
        AND ((e.job_function = 'driver' OR e.job_function = 'crew') AND u.branch_id IN ({0})) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        if start_date and end_date:
            where_location += """AND (al.date >= '{0} 00:00:00' 
            AND al.date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_location += """AND (al.date LIKE '{}%')""".format(today)
        count_location = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_location, order=order
        )

        # TODO: Get Statistic Delivery Cancelled
        select = "br.id, br.name"
        select_count = ", COUNT(dd.id) as total"
        join = """as dd LEFT JOIN `users` as u ON dd.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_dd = """WHERE (u.branch_id IN ({0}) AND dd.is_rejected = 1) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        if start_date and end_date:
            where_dd += """AND (dd.delivery_date >= '{0} 00:00:00' 
                    AND dd.delivery_date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_dd += """AND (dd.delivery_date LIKE '{}%')""".format(today)
        count_cancel = self.delivery_model.get_count_all_delivery_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_dd
        )

        total_nfc = 0
        total_location = 0
        total_cancel = 0
        if count_nfc:
            for nfc in count_nfc:
                total_nfc += int(nfc['total'])
        if count_location:
            for location in count_location:
                total_location += int(location['total'])
        if count_cancel:
            for cancel in count_cancel:
                total_cancel += int(cancel['total'])

        data = {
            'Report NFC': total_nfc,
            'Report Location': total_location,
            'Delivery Cancel': total_cancel
        }
        return data

    def get_statistic_packing_slip(self, branch_privilege: list, start_date: str, end_date: str):
        """

        :param branch_privilege: list
        :param start_date: str
        :param end_date: str
        :return:
        statistic performance about orders
        """
        try:
            today = datetime.today()
            today = today.strftime("%Y-%m-%d")
            data_statistic_packing_slip = dict()

            # TODO: Get statitistic Packing Slip from Delivery plan
            select = "br.id, br.name"
            select_count = ", SUM(JSON_LENGTH(dp.packing_slip_id)) as total"
            join = """as dp LEFT JOIN `users` as u ON dp.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
            where_dp = """WHERE (dp.is_deleted = 0 AND dp.is_approval = 1) 
                            AND (u.branch_id IN ({0})) """.format(
                ", ".join(str(x) for x in branch_privilege)
            )
            if start_date and end_date:
                where_dp += """AND (dp.date >= '{0} 00:00:00' AND dp.date <= '{1} 23:59:59')""".format(start_date,
                                                                                                       end_date)
            else:
                where_dp += """AND (dp.date LIKE '{}%')""".format(today)
            group = """GROUP BY u.branch_id"""
            count_packing_slip = self.delivery_plan_model.get_count_all_delivery_plan_statistic(
                self.cursor, select=select, select_count=select_count, join=join, where=where_dp, group=group
            )

            # TODO: Get Statistic Delivery Delivered
            select = "br.id, br.name"
            select_count = ", COUNT(dd.id) as total"
            join = """as dd LEFT JOIN `users` as u ON dd.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
            where_dd = """WHERE (u.branch_id IN ({0}) AND dd.is_accepted = 1) """.format(
                ", ".join(str(x) for x in branch_privilege)
            )
            if start_date and end_date:
                where_dd += """AND (dd.delivery_date >= '{0} 00:00:00' 
                                AND dd.delivery_date <= '{1} 23:59:59') """.format(start_date, end_date)
            else:
                where_dd += """AND (dd.delivery_date LIKE '{}%')""".format(today)
            group = """GROUP BY u.branch_id"""
            count_packing_slip_accept = self.delivery_model.get_count_all_delivery_statistic(
                self.cursor, select=select, select_count=select_count, join=join, where=where_dd, group=group
            )

            # TODO: Get Statistic Delivery Cancelled
            select = "br.id, br.name"
            select_count = ", COUNT(dd.id) as total"
            join = """as dd LEFT JOIN `users` as u ON dd.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
            where_dd = """WHERE (u.branch_id IN ({0}) AND dd.is_rejected = 1) """.format(
                ", ".join(str(x) for x in branch_privilege)
            )
            if start_date and end_date:
                where_dd += """AND (dd.delivery_date >= '{0} 00:00:00' 
                                AND dd.delivery_date <= '{1} 23:59:59') """.format(start_date, end_date)
            else:
                where_dd += """AND (dd.delivery_date LIKE '{}%')""".format(today)
            group = """GROUP BY u.branch_id"""
            count_packing_slip_cancel = self.delivery_model.get_count_all_delivery_statistic(
                self.cursor, select=select, select_count=select_count, join=join, where=where_dd, group=group
            )

            # TODO: Get Statistic Sales Order
            select = """br.id, br.name"""
            select_count = ", COUNT(so.code) as total"
            join = """as so LEFT JOIN `users` as u ON so.user_code = u.username 
                            LEFT JOIN `branches` as br ON u.branch_id = br.id"""
            # where_so = """WHERE (so.invoice_code is NULL AND (so.status != "canceled" OR so.status is NULL))
            #         AND (u.branch_id IN ({0})) """.format(
            #     ", ".join(str(x) for x in branch_privilege)
            # )
            where_so = """WHERE (so.status != "canceled" OR so.status is NULL) 
                            AND (u.branch_id IN ({0})) """.format(
                ", ".join(str(x) for x in branch_privilege)
            )
            if start_date and end_date:
                where_so += """AND (so.create_date >= '{0} 00:00:00' AND so.create_date <= '{1} 23:59:59')""".format(
                    start_date, end_date)
            else:
                where_so += """AND (so.create_date LIKE '{}%')""".format(today)
            group = """GROUP BY u.branch_id"""
            count_so = self.so_model.get_count_all_sales_order_statistic(
                self.cursor, select=select, select_count=select_count, join=join, where=where_so, group=group
            )

            where_br = """WHERE (is_deleted = 0 AND is_approval = 1) AND id IN ({0}) """.format(
                ", ".join(str(x) for x in branch_privilege)
            )
            result = self.branches_model.get_all_branches(self.cursor, where=where_br, start=0, limit=1000)

            data_branch = []
            total_packing_slip = 0
            total_packing_slip_accept = 0
            total_packing_slip_cancel = 0
            total_sales_order = 0
            for res in result:
                packing_slip = 0
                packing_slip_accept = 0
                packing_slip_cancel = 0
                sales_order = 0
                if count_packing_slip:
                    for rec in count_packing_slip:
                        if rec['id'] == res['id']:
                            packing_slip += auto_correction_number_none(rec['total'])
                if count_packing_slip_accept:
                    for rec_acp in count_packing_slip_accept:
                        if rec_acp['id'] == res['id']:
                            packing_slip_accept += auto_correction_number_none(rec_acp['total'])
                if count_packing_slip_cancel:
                    for rec_ccl in count_packing_slip_cancel:
                        if rec_ccl['id'] == res['id']:
                            packing_slip_cancel += auto_correction_number_none(rec_ccl['total'])
                if count_so:
                    for rec_so in count_so:
                        if rec_so['id'] == res['id']:
                            sales_order += auto_correction_number_none(rec_so['total'])

                data_ps_psc = {
                    res['name']: {
                        "packing_slip": packing_slip,
                        "packing_slip_accept": packing_slip_accept,
                        "packing_slip_cancel": packing_slip_cancel,
                        "sales_order": sales_order
                    }
                }
                data_branch.append(data_ps_psc)
                total_packing_slip += packing_slip
                total_packing_slip_accept += packing_slip_accept
                total_packing_slip_cancel += packing_slip_cancel
                total_sales_order += sales_order

            data_total = {
                'packing_slip': total_packing_slip,
                'packing_slip_accept': total_packing_slip_accept,
                'packing_slip_cancel': total_packing_slip_cancel,
                'sales_order': total_sales_order
            }
            data_statistic_packing_slip['total_packing_slip'] = data_total
            data_statistic_packing_slip['data_packing_slip'] = data_branch
            return data_statistic_packing_slip
        except NameError:
            print(NameError)

    def get_statistic_activities(self, branch_privilege: list, start_date: str, end_date: str):
        """

        :param branch_privilege: list
        :param division_privilege: list
        :param start_date: str
        :param end_date: str
        :return:
        statistic performance activities
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")

        # Init Value
        total_driving_time = 0
        total_visit_time = 0
        total_break_time = 0

        # TODO: Get statistic Driving and Visit Time
        select = "br.id, br.name, la.tap_nfc_date, la.delivery_plan_id, la.nfc_code, la.tap_nfc_type"
        select_from = """( SELECT id, user_id, delivery_plan_id, 
        REPLACE(nfc_code, " ", "") as nfc_code, tap_nfc_date, tap_nfc_type FROM logistic_activity )"""
        order = 'ORDER BY la.tap_nfc_date ASC'
        join = """as la LEFT JOIN `users` as u ON la.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_la = """WHERE (u.branch_id IN ({0})) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        if start_date and end_date:
            where_la += """AND (la.tap_nfc_date >= '{0} 00:00:00' 
            AND la.tap_nfc_date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_la += """AND (la.tap_nfc_date LIKE '{}%')""".format(today)
        group = """GROUP BY la.delivery_plan_id, la.nfc_code, la.tap_nfc_type"""
        drive_time = self.logistic_activity_model.get_count_all_activity_statistic(
            self.cursor, select=select, select_from=select_from, join=join,
            where=where_la, order=order, group=group
        )
        data_drive_time = []
        batch_data_driver = []
        batch_data_visit = []
        if drive_time:
            for rec in drive_time:
                data_drive_time.append(rec)

            df = pd.DataFrame(data_drive_time)
            # TODO: Calculate total drive time
            df_group = df.groupby(['id', 'delivery_plan_id'])['tap_nfc_date'].agg(['first', 'last'])
            df_group['diff'] = df_group['last'] - df_group['first']
            df_group['diff'] = df_group['diff'].astype('timedelta64[m]')
            df_group_total = df_group.groupby(['id'])['diff'].sum().reset_index(name='total')
            df_group_total.set_index("id", inplace=True)
            df_group_total['total'] = df_group_total['total'].astype(int)
            df_group_total.index.names = ['id']

            df_driver_json = df_group_total.to_json(orient='index', date_format='iso')
            df_driver_json = json.loads(df_driver_json)
            for key, val in df_driver_json.items():
                value = val
                value['id'] = key
                batch_data_driver.append(value)
            # print(df_group_total.head(20))
            # print(df_driver_json)

            # TODO: Calculate total visit time
            # df_visit = df[df['tap_nfc_type'].isin(['IN', 'OUT'])]
            # df_visit_group = df_visit.groupby(['id', 'nfc_code', 'delivery_plan_id'])['tap_nfc_date'].agg(['first', 'last'])
            # df_visit_group['diff'] = df_visit_group['last'] - df_visit_group['first']
            # df_visit_group['diff'] = df_visit_group['diff'].astype('timedelta64[m]')
            # df_visit_group_total = df_visit_group.groupby(['id'])['diff'].sum().reset_index(name ='total')
            # df_visit_group_total.set_index("id", inplace=True)
            # df_visit_group_total['total'] = df_visit_group_total['total'].astype(int)
            # df_visit_group_total.index.names = ['id']
            #
            # df_visit_json = df_visit_group_total.to_json(orient='index', date_format='iso')
            # df_visit_json = json.loads(df_visit_json)
            # for key, val in df_visit_json.items():
            #     value = val
            #     value['id'] = key
            #     batch_data_visit.append(value)
            # print(df_visit_group_total.head(20))
            # print(df_visit_json)

        # TODO: Get statistic Visit Time
        select = "br.id, br.name, la.tap_nfc_date, la.delivery_plan_id, la.nfc_code, la.tap_nfc_type"
        select_from = """( SELECT id, user_id, delivery_plan_id, 
        REPLACE(nfc_code, " ", "") as nfc_code, tap_nfc_date, tap_nfc_type FROM logistic_activity )"""
        order = 'ORDER BY la.tap_nfc_date ASC'
        join = """as la LEFT JOIN `users` as u ON la.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_la = """WHERE (u.branch_id IN ({0})) AND la.tap_nfc_type IN ('IN', 'OUT') """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        if start_date and end_date:
            where_la += """AND (la.tap_nfc_date >= '{0} 00:00:00' 
            AND la.tap_nfc_date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_la += """AND (la.tap_nfc_date LIKE '{}%')""".format(today)
        group = """"""
        visit_time = self.logistic_activity_model.get_count_all_activity_statistic(
            self.cursor, select=select, select_from=select_from, join=join,
            where=where_la, order=order, group=group
        )
        data_visit_time = []
        data_visit_group_time = []
        batch_data_visit_time = []
        if visit_time:
            counter_code = {}
            flag_record = {}
            for rec in visit_time:
                counter_code[rec['nfc_code']] = 1
                flag_record[rec['nfc_code']] = False
                data_visit_time.append(rec)
            idx = 0
            for rc in data_visit_time:
                if flag_record[rc['nfc_code']]:
                    counter_code[rc['nfc_code']] += 1
                    flag_record[rc['nfc_code']] = False
                if rc['tap_nfc_type'] == 'IN':
                    rc['counter'] = counter_code[rc['nfc_code']]
                if rc['tap_nfc_type'] == 'OUT':
                    if idx != 0:
                        cur_idx = idx
                        prev_idx = cur_idx - 1
                        while prev_idx >= 0:
                            if data_visit_time[prev_idx]['nfc_code'] == rc['nfc_code'] and data_visit_time[prev_idx][
                                'tap_nfc_type'] == 'IN':
                                rc['counter'] = counter_code[rc['nfc_code']]
                                flag_record[rc['nfc_code']] = True
                                break
                            prev_idx -= 1
                idx += 1
                data_visit_group_time.append(rc)
            df = pd.DataFrame(data_visit_group_time)
            # df_visit_time = df[df['tap_nfc_type'].isin(['IN', 'OUT'])]
            df_visit_time_group = df.groupby(['id', 'nfc_code', 'delivery_plan_id', 'counter'])['tap_nfc_date'].agg(
                ['first', 'last'])
            df_visit_time_group['diff'] = df_visit_time_group['last'] - df_visit_time_group['first']
            df_visit_time_group['diff'] = df_visit_time_group['diff'].astype('timedelta64[m]')
            df_visit_time_group_total = df_visit_time_group.groupby(['id'])['diff'].sum().reset_index(name='total')
            df_visit_time_group_total.set_index("id", inplace=True)
            df_visit_time_group_total['total'] = df_visit_time_group_total['total'].astype(int)
            df_visit_time_group_total.index.names = ['id']

            df_visit_time_json = df_visit_time_group_total.to_json(orient='index', date_format='iso')
            df_visit_time_json = json.loads(df_visit_time_json)
            for key, val in df_visit_time_json.items():
                value = val
                value['id'] = key
                batch_data_visit.append(value)

        # TODO: Get statistic Break Time
        select = "br.id, br.name, CAST(SUM(bt.break_time) as UNSIGNED) as total"
        order = 'ORDER BY bt.create_date ASC'
        join = """as bt LEFT JOIN `users` as u ON bt.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_bt = """WHERE (u.branch_id IN ({0}) AND delivery_plan_id IS NOT NULL) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        if start_date and end_date:
            where_bt += """AND (bt.create_date >= '{0} 00:00:00' 
                    AND bt.create_date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_bt += """AND (bt.create_date LIKE '{}%')""".format(today)
        group = """GROUP BY br.id"""
        break_time = self.break_time_model.get_count_all_break_time_statistic(
            self.cursor, select=select, join=join, where=where_bt, order=order, group=group
        )

        # TODO: SUM all total
        if batch_data_driver:
            for rec_driver in batch_data_driver:
                total_driving_time += rec_driver['total']
        if batch_data_visit:
            for rec_visit in batch_data_visit:
                total_visit_time += rec_visit['total']
        if break_time:
            for rec_break in break_time:
                total_break_time += rec_break['total']
        data_return = {
            'Driving Time': total_driving_time - total_visit_time,
            'Stop Time': total_visit_time,
            'Break Time': int(total_break_time / 60)
        }
        return data_return


class StatisticController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.branches_model = BranchesModel()
        self.delivery_cycle_model = DeliveryCycleModel()
        self.delivery_plan_model = DeliveryPlanModel()
        self.delivery_model = DeliveryModel()
        self.logistic_activity_model = LogisticActivityModel()
        self.permissions_model = PermissionsModel()
        self.break_time_model = BreakTimeModel()
        self.packing_slip_model = PackingSlipModel()
        self.visit_plan_model = VisitPlanModel()
        self.sales_activity_model = SalesActivityModel()
        self.spm_model = SalesPaymentMobileModel()
        self.so_model = SalesOrderModel()
        self.ro_model = RequestOrderModel()

    def get_statistic_performance_by_user_id(
            self, job_function: str, user_ids: list, start_date: str, end_date: str
    ):
        """

        :param job_function:str
        :param user_ids: list
        :param start_date: str
        :param end_date: str
        :return:
        statistic performance about report
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")
        # today = "2018-09-27"

        # TODO: Get statistic Alert
        select = "u.id"
        select_count = ", COUNT(al.id) as total"
        order = 'ORDER BY al.date ASC'
        join = """as al LEFT JOIN `users` as u ON al.create_by = u.id"""
        where_al = """WHERE (al.type = 'alert') AND al.create_by IN ({}) """.format(
            ", ".join(str(x) for x in user_ids),
        )
        if start_date and end_date:
            where_al += """AND (al.date >= '{0} 00:00:00' 
                    AND al.date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_al += """AND (al.date LIKE '{}%')""".format(today)
        group = """GROUP BY al.create_by"""
        count_alert = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_al, order=order, group=group
        )

        # TODO: Get statistic Permission
        select = "u.id"
        select_count = ", COUNT(al.id) as total"
        order = 'ORDER BY al.date ASC'
        join = """as al LEFT JOIN `users` as u ON al.create_by = u.id"""
        where_al = """WHERE (al.type IN ('routes', 'break_time', 'visit_time', 'print', 'report')) 
        AND al.create_by IN ({}) """.format(
            ", ".join(str(x) for x in user_ids),
        )
        if start_date and end_date:
            where_al += """AND (al.date >= '{0} 00:00:00' 
                    AND al.date <= '{1} 23:59:59')""".format(start_date, end_date)
        else:
            where_al += """AND (al.date LIKE '{}%')""".format(today)
        group = """GROUP BY al.create_by"""
        count_permission = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_al, order=order, group=group
        )

        if job_function == 'sales':
            # TODO: Get statitistic Visited plan
            select = "u.id"
            select_count = ", SUM(JSON_LENGTH(vp.destination)) as total"
            join = """as vp LEFT JOIN `users` as u ON vp.user_id = u.id """
            where_vp = """WHERE (vp.is_deleted = 0 AND vp.is_approval = 1) AND vp.user_id IN ({}) """.format(
                ", ".join(str(x) for x in user_ids)
            )
            if start_date and end_date:
                where_vp += """AND (vp.date >= '{0} 00:00:00' AND vp.date <= '{1} 23:59:59') """.format(
                    start_date, end_date
                )
            else:
                where_vp += """AND (vp.date LIKE '{}%')""".format(today)
            group = """GROUP BY vp.user_id"""
            count_plan = self.visit_plan_model.get_count_all_visit_plan_statistic(
                self.cursor, select=select, select_count=select_count, join=join, where=where_vp, group=group
            )

            # TODO: Get statistic New Destination
            select = "u.id"
            select_count_new_dest = ", SUM(JSON_LENGTH(vp.destination_new)) as total"
            join = """as vp LEFT JOIN `users` as u ON vp.user_id = u.id """
            where_vp = """WHERE (vp.is_deleted = 0 AND vp.is_approval = 1) AND vp.user_id IN ({}) """.format(
                ", ".join(str(x) for x in user_ids)
            )
            if start_date and end_date:
                where_vp += """AND (vp.date >= '{0} 00:00:00' AND vp.date <= '{1} 23:59:59') """.format(
                    start_date, end_date
                )
            else:
                where_vp += """AND (vp.date LIKE '{}%')""".format(today)

            group = """GROUP BY vp.user_id"""
            count_plan_new_dest = self.visit_plan_model.get_count_all_visit_plan_statistic(
                self.cursor, select=select, select_count=select_count_new_dest, join=join, where=where_vp, group=group
            )

            # TODO: Get Statistitic Actual Plan
            select = "sa.user_id AS id, "
            select_count = "COUNT(sa.id) AS total "
            select_from = """(SELECT la.* FROM sales_activity AS la INNER JOIN visit_plan AS dp on la.visit_plan_id = dp.id WHERE la.user_id IN ({2}) AND la.tap_nfc_type = 'IN' AND dp.is_deleted = 0 AND (DATE(la.tap_nfc_date) BETWEEN '{0}' AND '{1}') GROUP BY la.visit_plan_id, la.nfc_code, la.tap_nfc_type) as sa """.format(
                start_date, end_date, ", ".join(str(x) for x in user_ids)
            )
            group = """GROUP BY sa.user_id"""
            count_actual = self.sales_activity_model.get_count_all_activity_statistic(
                self.cursor, select=select, select_count=select_count, select_from=select_from, group=group
            )
        else:
            # TODO: Get statitistic Delivery plan
            select = "u.id"
            select_count = ", SUM(JSON_LENGTH(dp.destination)) as total"
            join = """as dp LEFT JOIN `users` as u ON dp.user_id = u.id """
            where_dp = """WHERE (dp.is_deleted = 0 AND dp.is_approval = 1) 
            AND dp.user_id IN ({0}) """.format(
                ", ".join(str(x) for x in user_ids)
            )
            if start_date and end_date:
                where_dp += """AND (dp.date >= '{0} 00:00:00' AND dp.date <= '{1} 23:59:59') """.format(
                    start_date, end_date
                )
            else:
                where_dp += """AND (dp.date LIKE '{}%')""".format(today)
            group = """GROUP BY dp.user_id"""
            count_plan = self.delivery_plan_model.get_count_all_delivery_plan_statistic(
                self.cursor, select=select, select_count=select_count, join=join, where=where_dp, group=group
            )

            # TODO: Get statistic New Destination
            select = "u.id"
            select_count = ", SUM(JSON_LENGTH(dp.destination_new)) as total"
            join = """as dp LEFT JOIN `users` as u ON dp.user_id = u.id """
            where_dp = """WHERE (dp.is_deleted = 0 AND dp.is_approval = 1) 
                            AND dp.user_id IN ({0}) """.format(
                ", ".join(str(x) for x in user_ids)
            )
            if start_date and end_date:
                where_dp += """AND (dp.date >= '{0} 00:00:00' AND dp.date <= '{1} 23:59:59') """.format(
                    start_date, end_date
                )
            else:
                where_dp += """AND (dp.date LIKE '{}%')""".format(today)

            group = """GROUP BY dp.user_id"""
            count_plan_new_dest = self.delivery_plan_model.get_count_all_delivery_plan_statistic(
                self.cursor, select=select, select_count=select_count, join=join, where=where_dp, group=group
            )

            # TODO: Get Statistic Actual Plan
            select = "sa.user_id AS id, "
            select_count = "COUNT(sa.id) AS total "
            select_from = """(SELECT la.* FROM logistic_activity AS la INNER JOIN delivery_plan AS dp on la.delivery_plan_id = dp.id WHERE la.user_id IN ({2}) AND la.tap_nfc_type = 'IN' AND dp.is_deleted = 0 AND (DATE(la.tap_nfc_date) BETWEEN '{0}' AND '{1}') GROUP BY la.delivery_plan_id, la.nfc_code, la.tap_nfc_type) as sa """.format(
                start_date, end_date, ", ".join(str(x) for x in user_ids)
            )
            group = """GROUP BY sa.user_id"""
            count_actual = self.logistic_activity_model.get_count_all_activity_statistic(
                self.cursor, select=select, select_count=select_count, select_from=select_from, group=group
            )

            # # TODO: Get Statistitic Actual Plan
            # select = "u.id"
            # select_count = ", COUNT(dd.id) as total"
            # join = """as dd LEFT JOIN `users` as u ON dd.user_id = u.id """
            # where_dd = """WHERE dd.user_id IN ({0}) """.format(
            #     ", ".join(str(x) for x in user_ids)
            # )
            # if start_date and end_date:
            #     where_dd += """AND (dd.delivery_date >= '{0} 00:00:00'
            #     AND dd.delivery_date <= '{1} 23:59:59') """.format(start_date, end_date)
            # else:
            #     where_dd += """AND (dd.delivery_date LIKE '{}%')""".format(today)
            # group = """GROUP BY dd.user_id"""
            # count_actual = self.delivery_model.get_count_all_delivery_statistic(
            #     self.cursor, select=select, select_count=select_count, join=join, where=where_dd, group=group
            # )

        if job_function == 'sales':
            # TODO: Get statistic Driving and Visit Time
            select = "u.id, sa.tap_nfc_date, sa.visit_plan_id, sa.nfc_code, sa.tap_nfc_type"
            select_from = """( SELECT id, user_id, visit_plan_id, 
                    REPLACE(nfc_code, " ", "") as nfc_code, tap_nfc_date, tap_nfc_type FROM sales_activity )"""
            order = 'ORDER BY sa.tap_nfc_date ASC'
            join = """as sa LEFT JOIN `users` as u ON sa.user_id = u.id"""
            where_sa = """WHERE sa.user_id IN ({0}) """.format(
                ", ".join(str(x) for x in user_ids)
            )
            if start_date and end_date:
                where_sa += """AND (sa.tap_nfc_date >= '{0} 00:00:00' 
                        AND sa.tap_nfc_date <= '{1} 23:59:59') """.format(start_date, end_date)
            else:
                where_sa += """AND (sa.tap_nfc_date LIKE '{}%')""".format(today)
            group = """GROUP BY sa.visit_plan_id, sa.nfc_code, sa.tap_nfc_type"""
            drive_time = self.sales_activity_model.get_count_all_activity_statistic(
                self.cursor, select=select, select_from=select_from, join=join,
                where=where_sa, order=order, group=group
            )
            data_drive_time = []
            batch_data_driver = []
            batch_data_visit = []
            if drive_time:
                for rec in drive_time:
                    data_drive_time.append(rec)

                df = pd.DataFrame(data_drive_time)
                # TODO: Calculate total drive time
                df_group = df.groupby(['id', 'visit_plan_id'])['tap_nfc_date'].agg(['first', 'last'])
                df_group['diff'] = df_group['last'] - df_group['first']
                df_group['diff'] = df_group['diff'].astype('timedelta64[m]')
                df_group_total = df_group.groupby(['id'])['diff'].sum().reset_index(name='total')
                df_group_total.set_index("id", inplace=True)
                df_group_total['total'] = df_group_total['total'].astype(int)
                df_group_total.index.names = ['id']

                df_driver_json = df_group_total.to_json(orient='index', date_format='iso')
                df_driver_json = json.loads(df_driver_json)
                for key, val in df_driver_json.items():
                    value = val
                    value['id'] = key
                    batch_data_driver.append(value)
                # print(df_group_total.head(20))
                # print(df_driver_json)

                # TODO: Calculate total visit time
                # df_visit = df[df['tap_nfc_type'].isin(['IN', 'OUT'])]
                # df_visit_group = df_visit.groupby(['id', 'nfc_code', 'visit_plan_id'])['tap_nfc_date'].agg(
                #     ['first', 'last'])
                # df_visit_group['diff'] = df_visit_group['last'] - df_visit_group['first']
                # df_visit_group['diff'] = df_visit_group['diff'].astype('timedelta64[m]')
                # df_visit_group_total = df_visit_group.groupby(['id'])['diff'].sum().reset_index(name='total')
                # df_visit_group_total.set_index("id", inplace=True)
                # df_visit_group_total['total'] = df_visit_group_total['total'].astype(int)
                # df_visit_group_total.index.names = ['id']
                #
                # df_visit_json = df_visit_group_total.to_json(orient='index', date_format='iso')
                # df_visit_json = json.loads(df_visit_json)
                # for key, val in df_visit_json.items():
                #     value = val
                #     value['id'] = key
                #     batch_data_visit.append(value)
                # print(df_visit_group_total.head(20))
                # print(df_visit_json)

            # TODO: Get statistic Visit Time
            select = "u.id, sa.tap_nfc_date, sa.visit_plan_id, sa.nfc_code, sa.tap_nfc_type"
            select_from = """( SELECT id, user_id, visit_plan_id, 
                    REPLACE(nfc_code, " ", "") as nfc_code, tap_nfc_date, tap_nfc_type FROM sales_activity )"""
            order = 'ORDER BY sa.tap_nfc_date ASC'
            join = """as sa LEFT JOIN `users` as u ON sa.user_id = u.id"""
            where_sa = """WHERE sa.user_id IN ({0}) AND sa.tap_nfc_type IN ('IN', 'OUT') """.format(
                ", ".join(str(x) for x in user_ids)
            )
            if start_date and end_date:
                where_sa += """AND (sa.tap_nfc_date >= '{0} 00:00:00' 
                        AND sa.tap_nfc_date <= '{1} 23:59:59') """.format(start_date, end_date)
            else:
                where_sa += """AND (sa.tap_nfc_date LIKE '{}%')""".format(today)
            group = """"""
            visit_time = self.sales_activity_model.get_count_all_activity_statistic(
                self.cursor, select=select, select_from=select_from, join=join,
                where=where_sa, order=order, group=group
            )
            data_visit_time = []
            data_visit_group_time = []
            batch_data_visit_time = []
            if visit_time:
                counter_code = {}
                flag_record = {}
                for rec in visit_time:
                    counter_code[rec['nfc_code']] = 1
                    flag_record[rec['nfc_code']] = False
                    data_visit_time.append(rec)
                idx = 0
                for rc in data_visit_time:
                    if flag_record[rc['nfc_code']]:
                        counter_code[rc['nfc_code']] += 1
                        flag_record[rc['nfc_code']] = False
                    if rc['tap_nfc_type'] == 'IN':
                        rc['counter'] = counter_code[rc['nfc_code']]
                    if rc['tap_nfc_type'] == 'OUT':
                        if idx != 0:
                            cur_idx = idx
                            prev_idx = cur_idx - 1
                            while prev_idx >= 0:
                                if data_visit_time[prev_idx]['nfc_code'] == rc['nfc_code'] and \
                                        data_visit_time[prev_idx]['tap_nfc_type'] == 'IN':
                                    rc['counter'] = counter_code[rc['nfc_code']]
                                    flag_record[rc['nfc_code']] = True
                                    break
                                prev_idx -= 1
                    idx += 1
                    data_visit_group_time.append(rc)
                df = pd.DataFrame(data_visit_group_time)
                # df_visit_time = df[df['tap_nfc_type'].isin(['IN', 'OUT'])]
                df_visit_time_group = df.groupby(['id', 'nfc_code', 'visit_plan_id', 'counter'])['tap_nfc_date'].agg(
                    ['first', 'last'])
                df_visit_time_group['diff'] = df_visit_time_group['last'] - df_visit_time_group['first']
                df_visit_time_group['diff'] = df_visit_time_group['diff'].astype('timedelta64[m]')
                df_visit_time_group_total = df_visit_time_group.groupby(['id'])['diff'].sum().reset_index(name='total')
                df_visit_time_group_total.set_index("id", inplace=True)
                df_visit_time_group_total['total'] = df_visit_time_group_total['total'].astype(int)
                df_visit_time_group_total.index.names = ['id']

                df_visit_time_json = df_visit_time_group_total.to_json(orient='index', date_format='iso')
                df_visit_time_json = json.loads(df_visit_time_json)
                for key, val in df_visit_time_json.items():
                    value = val
                    value['id'] = key
                    batch_data_visit.append(value)

            # TODO: Get statistic Break Time
            select = "u.id, CAST(SUM(bt.break_time) as UNSIGNED) as total"
            order = 'ORDER BY bt.create_date ASC'
            join = """as bt LEFT JOIN `users` as u ON bt.user_id = u.id"""
            where_bt = """WHERE bt.user_id IN ({0}) AND visit_plan_id IS NOT NULL """.format(
                ", ".join(str(x) for x in user_ids)
            )
            if start_date and end_date:
                where_bt += """AND (bt.create_date >= '{0} 00:00:00' 
                        AND bt.create_date <= '{1} 23:59:59') """.format(start_date, end_date)
            else:
                where_bt += """AND (bt.create_date LIKE '{}%')""".format(today)
            group = """GROUP BY bt.user_id"""
            break_time = self.break_time_model.get_count_all_break_time_statistic(
                self.cursor, select=select, join=join, where=where_bt, order=order, group=group
            )
        else:
            # TODO: Get statistic Driving and Visit Time
            select = "u.id, la.tap_nfc_date, la.delivery_plan_id, la.nfc_code, la.tap_nfc_type"
            select_from = """( SELECT id, user_id, delivery_plan_id, 
                    REPLACE(nfc_code, " ", "") as nfc_code, tap_nfc_date, tap_nfc_type FROM logistic_activity )"""
            order = 'ORDER BY la.tap_nfc_date ASC'
            join = """as la LEFT JOIN `users` as u ON la.user_id = u.id """
            where_la = """WHERE la.user_id IN ({0}) """.format(
                ", ".join(str(x) for x in user_ids)
            )
            if start_date and end_date:
                where_la += """AND (la.tap_nfc_date >= '{0} 00:00:00' 
                        AND la.tap_nfc_date <= '{1} 23:59:59') """.format(start_date, end_date)
            else:
                where_la += """AND (la.tap_nfc_date LIKE '{}%')""".format(today)
            group = """GROUP BY la.delivery_plan_id, la.nfc_code, la.tap_nfc_type"""
            drive_time = self.logistic_activity_model.get_count_all_activity_statistic(
                self.cursor, select=select, select_from=select_from, join=join,
                where=where_la, order=order, group=group
            )
            data_drive_time = []
            batch_data_driver = []
            batch_data_visit = []
            if drive_time:
                for rec in drive_time:
                    data_drive_time.append(rec)

                df = pd.DataFrame(data_drive_time)
                # TODO: Calculate total drive time
                df_group = df.groupby(['id', 'delivery_plan_id'])['tap_nfc_date'].agg(['first', 'last'])
                df_group['diff'] = df_group['last'] - df_group['first']
                df_group['diff'] = df_group['diff'].astype('timedelta64[m]')
                df_group_total = df_group.groupby(['id'])['diff'].sum().reset_index(name='total')
                df_group_total.set_index("id", inplace=True)
                df_group_total['total'] = df_group_total['total'].astype(int)
                df_group_total.index.names = ['id']

                df_driver_json = df_group_total.to_json(orient='index', date_format='iso')
                df_driver_json = json.loads(df_driver_json)
                for key, val in df_driver_json.items():
                    value = val
                    value['id'] = key
                    batch_data_driver.append(value)
                # print(batch_data_driver)

                # TODO: Calculate total visit time
                # df_visit = df[df['tap_nfc_type'].isin(['IN', 'OUT'])]
                # df_visit_group = df_visit.groupby(['id', 'nfc_code', 'delivery_plan_id'])['tap_nfc_date'].agg(
                #     ['first', 'last'])
                # df_visit_group['diff'] = df_visit_group['last'] - df_visit_group['first']
                # df_visit_group['diff'] = df_visit_group['diff'].astype('timedelta64[m]')
                # df_visit_group_total = df_visit_group.groupby(['id'])['diff'].sum().reset_index(name='total')
                # df_visit_group_total.set_index("id", inplace=True)
                # df_visit_group_total['total'] = df_visit_group_total['total'].astype(int)
                # df_visit_group_total.index.names = ['id']
                #
                # df_visit_json = df_visit_group_total.to_json(orient='index', date_format='iso')
                # df_visit_json = json.loads(df_visit_json)
                # for key, val in df_visit_json.items():
                #     value = val
                #     value['id'] = key
                #     batch_data_visit.append(value)
                # print(batch_data_visit)

            # TODO: Get statistic Visit Time
            select = "u.id, la.tap_nfc_date, la.delivery_plan_id, la.nfc_code, la.tap_nfc_type"
            select_from = """( SELECT id, user_id, delivery_plan_id, 
                    REPLACE(nfc_code, " ", "") as nfc_code, tap_nfc_date, tap_nfc_type FROM logistic_activity )"""
            order = 'ORDER BY la.tap_nfc_date ASC'
            join = """as la LEFT JOIN `users` as u ON la.user_id = u.id """
            where_la = """WHERE la.user_id IN ({0}) AND la.tap_nfc_type IN ('IN', 'OUT') """.format(
                ", ".join(str(x) for x in user_ids)
            )
            if start_date and end_date:
                where_la += """AND (la.tap_nfc_date >= '{0} 00:00:00' 
                        AND la.tap_nfc_date <= '{1} 23:59:59') """.format(start_date, end_date)
            else:
                where_la += """AND (la.tap_nfc_date LIKE '{}%')""".format(today)
            group = """"""
            visit_time = self.logistic_activity_model.get_count_all_activity_statistic(
                self.cursor, select=select, select_from=select_from, join=join,
                where=where_la, order=order, group=group
            )
            data_visit_time = []
            data_visit_group_time = []
            batch_data_visit_time = []
            if visit_time:
                counter_code = {}
                flag_record = {}
                for rec in visit_time:
                    counter_code[rec['nfc_code']] = 1
                    flag_record[rec['nfc_code']] = False
                    data_visit_time.append(rec)
                idx = 0
                for rc in data_visit_time:
                    if flag_record[rc['nfc_code']]:
                        counter_code[rc['nfc_code']] += 1
                        flag_record[rc['nfc_code']] = False
                    if rc['tap_nfc_type'] == 'IN':
                        rc['counter'] = counter_code[rc['nfc_code']]
                    if rc['tap_nfc_type'] == 'OUT':
                        if idx != 0:
                            cur_idx = idx
                            prev_idx = cur_idx - 1
                            while prev_idx >= 0:
                                if data_visit_time[prev_idx]['nfc_code'] == rc['nfc_code'] and \
                                        data_visit_time[prev_idx]['tap_nfc_type'] == 'IN':
                                    rc['counter'] = counter_code[rc['nfc_code']]
                                    flag_record[rc['nfc_code']] = True
                                    break
                                prev_idx -= 1
                    idx += 1
                    data_visit_group_time.append(rc)
                df = pd.DataFrame(data_visit_group_time)
                # df_visit_time = df[df['tap_nfc_type'].isin(['IN', 'OUT'])]
                df_visit_time_group = df.groupby(['id', 'nfc_code', 'delivery_plan_id', 'counter'])['tap_nfc_date'].agg(
                    ['first', 'last'])
                df_visit_time_group['diff'] = df_visit_time_group['last'] - df_visit_time_group['first']
                df_visit_time_group['diff'] = df_visit_time_group['diff'].astype('timedelta64[m]')
                df_visit_time_group_total = df_visit_time_group.groupby(['id'])['diff'].sum().reset_index(name='total')
                df_visit_time_group_total.set_index("id", inplace=True)
                df_visit_time_group_total['total'] = df_visit_time_group_total['total'].astype(int)
                df_visit_time_group_total.index.names = ['id']

                df_visit_time_json = df_visit_time_group_total.to_json(orient='index', date_format='iso')
                df_visit_time_json = json.loads(df_visit_time_json)
                for key, val in df_visit_time_json.items():
                    value = val
                    value['id'] = key
                    batch_data_visit.append(value)

            # TODO: Get statistic Break Time
            select = "u.id, CAST(SUM(bt.break_time) as UNSIGNED) as total"
            order = 'ORDER BY bt.create_date ASC'
            join = """as bt LEFT JOIN `users` as u ON bt.user_id = u.id"""
            where_bt = """WHERE bt.user_id IN ({0}) AND delivery_plan_id IS NOT NULL """.format(
                ", ".join(str(x) for x in user_ids)
            )
            if start_date and end_date:
                where_bt += """AND (bt.create_date >= '{0} 00:00:00' 
                AND bt.create_date <= '{1} 23:59:59') """.format(start_date, end_date)
            else:
                where_bt += """AND (bt.create_date LIKE '{}%')""".format(today)
            group = """GROUP BY bt.user_id"""
            break_time = self.break_time_model.get_count_all_break_time_statistic(
                self.cursor, select=select, join=join, where=where_bt, order=order, group=group
            )

        # TODO: Get statitistic Permission Report NFC and sales
        select = "u.id"
        select_count = ", COUNT(al.id) as total"
        order = 'ORDER BY al.date ASC'
        join = """as al LEFT JOIN `users` as u ON al.create_by = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id"""
        where_nfc = """WHERE (al.type = 'report' AND JSON_CONTAINS(al.description, '{{\"type\": \"nfc\"}}')) 
        AND (al.create_by IN ({1})) """.format(
            job_function, ", ".join(str(x) for x in user_ids)
        )
        if start_date and end_date:
            where_nfc += """AND (al.date >= '{0} 00:00:00' 
            AND al.date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_nfc += """AND (al.date LIKE '{}%')""".format(today)
        count_nfc_sales = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_nfc, order=order
        )

        # TODO: Get Statistic Permission Report Location
        select = "u.id"
        select_count = ", COUNT(al.id) as total"
        order = 'ORDER BY al.date ASC'
        join = """as al LEFT JOIN `users` as u ON al.create_by = u.id 
                LEFT JOIN `employee` as e ON u.employee_id = e.id"""
        where_location = """WHERE (al.type = 'report' AND JSON_CONTAINS(al.description, '{{\"type\": \"location\"}}')) 
                AND (al.create_by IN ({1})) """.format(
            job_function, ", ".join(str(x) for x in user_ids)
        )
        if start_date and end_date:
            where_location += """AND (al.date >= '{0} 00:00:00' 
                    AND al.date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_location += """AND (al.date LIKE '{}%')""".format(today)
        count_location = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_location, order=order
        )

        # TODO: Get statitistic Permission Report Print
        select = "u.id"
        select_count = ", COUNT(al.id) as total"
        order = 'ORDER BY al.date ASC'
        join = """as al LEFT JOIN `users` as u ON al.create_by = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id """
        where_print = """WHERE (al.type = 'report' AND JSON_CONTAINS(al.description, '{{\"type\": \"print\"}}')) 
        AND (al.create_by IN ({1})) """.format(
            job_function, ", ".join(str(x) for x in user_ids)
        )
        if start_date and end_date:
            where_print += """AND (al.date >= '{0} 00:00:00' 
                    AND al.date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_print += """AND (al.date LIKE '{}%')""".format(today)
        count_print_sales = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_print, order=order
        )

        # TODO: Get Statistic Payment reprint and cancel
        select = """u.id, CAST(SUM(spm.is_canceled) as UNSIGNED) as cancel, 
        CAST(SUM(spm.receipt_reprint) as UNSIGNED) as reprint"""
        select_count = ''
        join = """as spm LEFT JOIN `users` as u ON spm.create_by = u.id """
        where_spm = """WHERE spm.create_by IN ({0}) """.format(
            ", ".join(str(x) for x in user_ids)
        )
        if start_date and end_date:
            where_spm += """AND (spm.create_date >= '{0} 00:00:00' AND spm.create_date <= '{1} 23:59:59') """.format(
                start_date, end_date)
        else:
            where_spm += """AND (spm.create_date LIKE '{}%')""".format(today)
        group = """GROUP BY spm.create_by"""
        count_reprint_cancel = self.spm_model.get_count_all_sales_payment_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_spm, group=group
        )

        # TODO: Get statitistic Request Order
        select = "u.id"
        select_count = ", COUNT(ro.id) as total"
        join = """as ro LEFT JOIN `users` as u ON ro.user_id = u.id LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        where_ro = """WHERE ro.user_id IN ({0}) """.format(
            ", ".join(str(x) for x in user_ids)
        )
        if start_date and end_date:
            where_ro += """AND (ro.date >= '{0} 00:00:00' AND ro.date <= '{1} 23:59:59')""".format(start_date, end_date)
        else:
            where_ro += """AND (ro.date LIKE '{}%')""".format(today)
        group = """GROUP BY ro.id"""
        count_ro = self.ro_model.get_count_all_request_order_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_ro, group=group
        )

        # TODO: Get statitistic Request Order Special
        select = "u.id"
        select_count = ", COUNT(ro.id) as total"
        join = """as ro LEFT JOIN `users` as u ON ro.user_id = u.id """
        where_ro_special = """WHERE ro.user_id IN ({0}) AND ro.is_special_order = 1 """.format(
            ", ".join(str(x) for x in user_ids)
        )
        if start_date and end_date:
            where_ro_special += """AND (ro.date >= '{0} 00:00:00' AND ro.date <= '{1} 23:59:59')""".format(start_date,
                                                                                                           end_date)
        else:
            where_ro_special += """AND (ro.date LIKE '{}%')""".format(today)
        group = """GROUP BY ro.id"""
        count_ro_special = self.ro_model.get_count_all_request_order_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_ro_special, group=group
        )

        # TODO: Get Statistic Sales Order
        select = """br.id, br.name"""
        select_count = ", COUNT(so.code) as total, SUM(so.invoice_amount) as amount"
        join = """as so LEFT JOIN `users` as u ON so.user_code = u.username 
        LEFT JOIN `branches` as br ON u.branch_id = br.id"""
        # where_so = """WHERE (so.invoice_code is NULL AND (so.status != "canceled" OR so.status is NULL))
        # AND u.id IN ({0}) """.format(
        #     ", ".join(str(x) for x in user_ids)
        # )
        where_so = """WHERE (so.status != "canceled" OR so.status is NULL) 
        AND u.id IN ({0}) """.format(
            ", ".join(str(x) for x in user_ids)
        )
        if start_date and end_date:
            where_so += """AND (so.create_date >= '{0} 00:00:00' AND so.create_date <= '{1} 23:59:59')""".format(
                start_date, end_date)
        else:
            where_so += """AND (so.create_date LIKE '{}%')""".format(today)
        group = """GROUP BY u.id"""
        count_so = self.so_model.get_count_all_sales_order_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_so, group=group
        )

        # TODO: Get Statistic Invoice and Payment
        select = """u.id, CAST(SUM(spm.invoice_amount) as UNSIGNED) as inv_amount, 
                CAST(SUM(spm.payment_amount) as UNSIGNED) as pay_amount"""
        select_count = ", SUM(JSON_LENGTH(spm.invoice)) as total_inv, COUNT(spm.id) as total_pay"
        join = """as spm LEFT JOIN `users` as u ON spm.create_by = u.id"""
        where_spm_inv = """WHERE (spm.is_confirm = 1) AND spm.create_by IN ({0}) """.format(
            ", ".join(str(x) for x in user_ids)
        )
        if start_date and end_date:
            where_spm_inv += """AND (spm.create_date >= '{0} 00:00:00' AND spm.create_date <= '{1} 23:59:59')""".format(
                start_date, end_date)
        else:
            where_spm_inv += """AND (spm.create_date LIKE '{}%')""".format(today)
        group = """GROUP BY spm.create_by"""
        count_inv_pay = self.spm_model.get_count_all_sales_payment_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_spm_inv, group=group
        )

        # TODO: Get Statistic Invoice and Payment Without Confirm
        select = """u.id, CAST(SUM(spm.invoice_amount) as UNSIGNED) as inv_amount, 
                CAST(SUM(spm.payment_amount) as UNSIGNED) as pay_amount"""
        select_count = ", SUM(JSON_LENGTH(spm.invoice)) as total_inv, COUNT(spm.id) as total_pay"
        join = """as spm LEFT JOIN `users` as u ON spm.create_by = u.id"""
        where_spm_inv_wo = """WHERE spm.create_by IN ({0}) """.format(
            ", ".join(str(x) for x in user_ids)
        )
        if start_date and end_date:
            where_spm_inv_wo += """AND (spm.create_date >= '{0} 00:00:00' AND spm.create_date <= '{1} 23:59:59')""".format(
                start_date, end_date)
        else:
            where_spm_inv_wo += """AND (spm.create_date LIKE '{}%')""".format(today)
        group = """GROUP BY spm.create_by"""
        count_inv_pay_wo = self.spm_model.get_count_all_sales_payment_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_spm_inv_wo, group=group
        )

        # TODO: Get statitistic Packing Slip from Delivery plan
        select = "u.id"
        select_count = ", SUM(JSON_LENGTH(dp.packing_slip_id)) as total"
        join = """as dp LEFT JOIN `users` as u ON dp.user_id = u.id """
        where_dp = """WHERE (dp.is_deleted = 0 AND dp.is_approval = 1) AND (dp.user_id IN ({0})) """.format(
            ", ".join(str(x) for x in user_ids)
        )
        if start_date and end_date:
            where_dp += """AND (dp.date >= '{0} 00:00:00' AND dp.date <= '{1} 23:59:59')""".format(start_date, end_date)
        else:
            where_dp += """AND (dp.date LIKE '{}%')""".format(today)
        group = """GROUP BY dp.user_id"""
        count_packing_slip = self.delivery_plan_model.get_count_all_delivery_plan_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_dp, group=group
        )

        # TODO: Get Statistic Delivery Delivered
        select = "u.id"
        select_count = ", COUNT(dd.id) as total"
        join = """as dd LEFT JOIN `users` as u ON dd.user_id = u.id """
        where_dd = """WHERE (dd.user_id IN ({0}) AND dd.is_accepted = 1) """.format(
            ", ".join(str(x) for x in user_ids)
        )
        if start_date and end_date:
            where_dd += """AND (dd.delivery_date >= '{0} 00:00:00' 
            AND dd.delivery_date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_dd += """AND (dd.delivery_date LIKE '{}%')""".format(today)
        group = """GROUP BY dd.user_id"""
        count_packing_slip_accept = self.delivery_model.get_count_all_delivery_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_dd, group=group
        )

        # TODO: Get Statistic Delivery Cancelled
        select = "u.id"
        select_count = ", COUNT(dd.id) as total"
        join = """as dd LEFT JOIN `users` as u ON dd.user_id = u.id """
        where_dd = """WHERE (dd.user_id IN ({0}) AND dd.is_rejected = 1) """.format(
            ", ".join(str(x) for x in user_ids)
        )
        if start_date and end_date:
            where_dd += """AND (dd.delivery_date >= '{0} 00:00:00' 
            AND dd.delivery_date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_dd += """AND (dd.delivery_date LIKE '{}%')""".format(today)
        group = """GROUP BY dd.user_id"""
        count_packing_slip_cancel = self.delivery_model.get_count_all_delivery_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_dd, group=group
        )

        data_performance = dict()
        for rec_id in user_ids:
            total_alert = 0
            total_permission = 0
            for rec_alert in count_alert:
                if rec_alert['id'] == rec_id:
                    total_alert += int(rec_alert['total'])

            for rec_permission in count_permission:
                if rec_permission['id'] == rec_id:
                    total_permission += int(rec_permission['total'])
            plan = 0
            actual = 0
            new_destination = 0
            if count_plan:
                for rec in count_plan:
                    if rec['id'] == rec_id:
                        plan += int(rec['total'])
                        if count_actual:
                            for rec_actual in count_actual:
                                if rec_actual['id'] == rec['id']:
                                    actual += int(rec_actual['total'])
                        if count_plan_new_dest:
                            for rec_new_dest in count_plan_new_dest:
                                if rec_new_dest['id'] == rec['id']:
                                    if rec_new_dest['total']:
                                        new_destination += int(rec_new_dest['total'])
            cancel = plan - actual + new_destination
            total_driving_time = 0
            total_visit_time = 0
            total_break_time = 0
            if batch_data_driver:
                for rec_driver in batch_data_driver:
                    if rec_driver['id']:
                        if int(rec_driver['id']) == rec_id:
                            total_driving_time += rec_driver['total']
            if batch_data_visit:
                for rec_visit in batch_data_visit:
                    if rec_visit['id']:
                        if int(rec_visit['id']) == rec_id:
                            total_visit_time += rec_visit['total']
            if break_time:
                for rec_break in break_time:
                    if rec_break['id']:
                        if int(rec_break['id']) == rec_id:
                            total_break_time += rec_break['total']
            total_location = 0
            total_nfc = 0
            total_print = 0
            total_pay_cancel = 0
            total_reprint = 0
            if count_location:
                for rec_location in count_location:
                    if rec_location['id'] == rec_id:
                        total_location += int(rec_location['total'])
            if count_nfc_sales:
                for rec_nfc in count_nfc_sales:
                    if rec_nfc['id'] == rec_id:
                        total_nfc += int(rec_nfc['total'])
            if count_print_sales:
                for rec_pr in count_print_sales:
                    if rec_pr['id'] == rec_id:
                        total_print += int(rec_pr['total'])
            if count_reprint_cancel:
                for rec_rpc in count_reprint_cancel:
                    if rec_rpc['id'] == rec_id:
                        total_reprint += int(rec_rpc['reprint'])
                        total_pay_cancel += int(rec_rpc['cancel'])
            total_ro = 0
            total_ro_spc = 0
            if count_ro:
                for rec_ro in count_ro:
                    if rec_ro['id'] == rec_id:
                        total_ro += int(rec_ro['total'])
            if count_ro_special:
                for rec_ro_spc in count_ro_special:
                    if rec_ro_spc['id'] == rec_id:
                        total_ro_spc += int(rec_ro_spc['total'])
            total_so = 0
            total_so_amount = 0
            if count_so:
                for rec_so in count_so:
                    if rec_so['id'] == rec_id:
                        total_so += int(rec_so['total'])
                        total_so_amount += int(rec_so['amount'])
            total_inv = 0
            total_inv_amount = 0
            total_pay = 0
            total_pay_amount = 0
            if count_inv_pay:
                for rec_inv_pay in count_inv_pay:
                    if rec_inv_pay['id'] == rec_id:
                        if rec_inv_pay['total_inv']:
                            total_inv += int(rec_inv_pay['total_inv'])
                        total_pay += int(rec_inv_pay['total_pay'])
                        total_inv_amount += int(rec_inv_pay['inv_amount'])
                        total_pay_amount += int(rec_inv_pay['pay_amount'])
            total_pay_wo = 0
            total_pay_amount_wo = 0
            if count_inv_pay_wo:
                for rec_inv_pay_wo in count_inv_pay_wo:
                    if rec_inv_pay_wo['id'] == rec_id:
                        total_pay_wo += int(rec_inv_pay_wo['total_pay'])
                        total_pay_amount_wo += int(rec_inv_pay_wo['pay_amount'])
            total_packing = 0
            total_packing_cancel = 0
            total_packing_accept = 0
            if count_packing_slip:
                for rec_pack in count_packing_slip:
                    if rec_pack['id'] == rec_id:
                        if rec_pack['total']:
                            total_packing += int(rec_pack['total'])
            if count_packing_slip_accept:
                for rec_pack_acp in count_packing_slip_accept:
                    if rec_pack_acp['id'] == rec_id:
                        total_packing_accept += int(rec_pack_acp['total'])
            if count_packing_slip_cancel:
                for rec_pack_ccl in count_packing_slip_cancel:
                    if rec_pack_ccl['id'] == rec_id:
                        total_packing_cancel += int(rec_pack_ccl['total'])
            # print(total_driving_time)
            # print(total_visit_time)
            if job_function == 'sales':
                data = {
                    "plan": plan,
                    "visited": actual,
                    "cancel": cancel,
                    "alert": total_alert,
                    "permission": total_permission,
                    "visit_time": total_visit_time,
                    "break_time": int(total_break_time / 60),
                    "driving_time": total_driving_time - total_visit_time,
                    "report_nfc": total_nfc,
                    "report_location": total_location,
                    "report_print": total_print,
                    "payment_cancel": total_pay_cancel,
                    "reprint": total_reprint,
                    "request_order": total_ro,
                    "request_order_special": total_ro_spc,
                    "sales_order": total_so,
                    "sales_order_amount": total_so_amount,
                    "invoice": total_inv,
                    "payment": total_pay,
                    "payment_wo_confirm": total_pay_wo,
                    "invoice_amount": total_inv_amount,
                    "payment_amount": total_pay_amount,
                    "payment_amount_wo_confirm": total_pay_amount_wo
                }
            else:
                data = {
                    "plan": plan,
                    "visited": actual,
                    "cancel": cancel,
                    "alert": total_alert,
                    "permission": total_permission,
                    "visit_time": total_visit_time,
                    "break_time": int(total_break_time / 60),
                    "driving_time": total_driving_time - total_visit_time,
                    "report_nfc": total_nfc,
                    "report_location": total_location,
                    "packing_slip": total_packing,
                    "packing_slip_accept": total_packing_accept,
                    "packing_slip_cancel": total_packing_cancel
                }
            data_performance[rec_id] = data

        return data_performance
