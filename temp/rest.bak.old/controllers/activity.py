import os
import re
import json
import sys
import time
import pandas as pd
import dateutil.parser
import xlsxwriter
import pdfkit

from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template
from collections import OrderedDict
from sqlalchemy import desc, asc, or_
from sqlalchemy.orm import aliased

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql
from rest.models import UserModel, BranchesModel, EmployeeModel, DivisionModel, SalesActivityModel, \
    SalesActivityBreadcrumbModel, LogisticActivityModel, LogisticActivityBreadcrumbModel, BreakTimeModel, \
    IdleTimeModel, VisitPlanModel, CustomerModel, DeliveryPlanModel, DeliveryModel, DeliveryCycleModel, \
    PermissionsModel, SalesPaymentMobileModel, PackingSlipModel, SalesOrderModel, RequestOrderModel, \
    VisitPlanSummaryModel

from rest.models.orm import VisitPlanModel as VisitPlanModelAlchemy
from rest.models.orm import UserModel as UserModelAlchemy
from rest.models.orm import BranchesModel as BranchesModelAlchemy
from rest.models.orm import DivisionModel as DivisionModelAlchemy
from rest.models.orm import EmployeeModel as EmployeeModelAlchemy
from rest.models.orm import SalesActivityModel as SalesActivityModelAlchemy
from rest.configuration import session

__author__ = 'Junior'


class SalesActivityController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.sales_activity_model = SalesActivityModel()
        self.sab_model = SalesActivityBreadcrumbModel()
        self.break_time_model = BreakTimeModel()
        self.idle_time_model = IdleTimeModel()
        self.user_model = UserModel()
        self.branch_model = BranchesModel()
        self.employee_model = EmployeeModel()
        self.division_model = DivisionModel()
        self.customer_model = CustomerModel()
        self.visit_plan_model = VisitPlanModel()
        self.visit_plan_summary_model = VisitPlanSummaryModel()
        self.delivery_cycle_model = DeliveryCycleModel()
        self.delivery_plan_model = DeliveryPlanModel()
        self.delivery_model = DeliveryModel()
        self.logistic_activity_model = LogisticActivityModel()
        self.permissions_model = PermissionsModel()
        self.packing_slip_model = PackingSlipModel()
        self.spm_model = SalesPaymentMobileModel()
        self.so_model = SalesOrderModel()
        self.ro_model = RequestOrderModel()

    def create(self, create_data: 'dict', user_id: 'int'):
        """
        Function for create new log activity

        :param create_data: dict
        :param user_id: int
        :return:
            Success or failure message
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.sales_activity_model.insert_into_db(
                self.cursor, user_id=user_id, visit_plan_id=create_data['visit_plan_id'],
                nfc_code=create_data['nfc_code'], route_breadcrumb=create_data['route_breadcrumb'],
                distance=create_data['distance'], total_distance=create_data['total_distance'], tap_nfc_date=today,
                tap_nfc_type=create_data['tap_nfc_type'], create_date=today, update_date=today
            )
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        # TODO: update visit plan to status finish
        if create_data['tap_nfc_type'] == "STOP":
            try:
                update_data = {
                    'id': create_data['visit_plan_id'],
                    'status': True
                }
                update_visit_plan = self.visit_plan_model.update_by_id(self.cursor, update_data)
                mysql.connection.commit()
            except Exception as e:
                print(e)
                pass

        return result

    def get_all_activity_data(
            self, page: int, limit: int, search: str, column: str, direction: str,
            branch_privilege: list, division_privilege: list
    ):
        """
        Get List Of visit cycle
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: branch_privilige: list
        :param: division_privilige: list
        :return:
            Visit Cycle Object
        """
        activity = {}
        data = []
        start = page * limit - limit
        where = """WHERE (sa.id IN (SELECT MIN(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'START' 
        GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MAX(id) FROM `sales_activity` 
        WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MIN(id) 
        FROM `sales_activity` WHERE `tap_nfc_type` = 'IN' GROUP BY user_id, visit_plan_id, nfc_code) 
        OR sa.id IN (SELECT MAX(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'OUT' 
        GROUP BY user_id, visit_plan_id, nfc_code)) AND (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        where_original = where
        order = ''
        if column:
            if column == 'branch':
                order = """ORDER BY b.name {0}""".format(direction)
            elif column == 'division':
                order = """ORDER BY d.division_name {0}""".format(direction)
            elif column == 'user':
                order = """ORDER BY u.username {0}""".format(direction)
            else:
                order = """ORDER BY sa.{0} {1}""".format(column, direction)
        select = "sa.*"
        select_count = "sa.id"
        join = """as sa LEFT JOIN `users` as u ON sa.user_id = u.id 
        LEFT JOIN `branches` as b ON u.branch_id = b.id 
        LEFT JOIN `divisions` as d ON u.division_id = d.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR e.name LIKE '%{0}%' 
            OR sa.tap_nfc_type LIKE '%{0}%') """.format(search)
        activity_data = self.sales_activity_model.get_all_activity(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.sales_activity_model.get_count_all_activity(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.sales_activity_model.get_count_all_activity(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if activity_data:
            for ad in activity_data:
                if ad['tap_nfc_date'] is not None:
                    ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                if ad['create_date'] is not None:
                    ad['create_date'] = str(ad['create_date'])
                if ad['update_date'] is not None:
                    ad['update_date'] = str(ad['update_date'])
                ad['branch_name'] = None
                if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                    if ad['nfc_code'] is not None:
                        try:
                            ad['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, ad['nfc_code'], select="""name"""
                            )[0]['name']
                        except:
                            ad['branch_name'] = None
                ad['customer_code'] = None
                if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                    if ad['nfc_code'] is not None:
                        ad['customer_code'] = ad['nfc_code']
                if ad['user_id'] is not None:
                    try:
                        ad['user'] = self.user_model.get_user_by_id(
                            self.cursor, ad['user_id'], select="username, employee_id, branch_id, division_id"
                        )[0]
                        if ad['user']['employee_id'] is not None:
                            try:
                                ad['user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    ad['user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                ad['user']['name'] = None
                        if ad['user']['branch_id'] is not None:
                            try:
                                ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    ad['user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                ad['user']['branch_name'] = None
                        if ad['user']['division_id'] is not None:
                            try:
                                ad['user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, ad['user']['division_id'], select="division_name")[0][
                                    'division_name']
                            except:
                                ad['user']['division_name'] = None
                    except:
                        ad['user'] = {}
                else:
                    ad['user'] = {}
                data.append(ad)
        activity['data'] = data
        activity['total'] = count
        activity['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if activity['total'] > page * limit:
            activity['has_next'] = True
        else:
            activity['has_next'] = False
        if limit <= page * count - count:
            activity['has_prev'] = True
        else:
            activity['has_prev'] = False
        return activity

    def get_all_activity_data_by_visit_plan(
            self, page: int, limit: int, search: str, column: str, direction: str,
            branch_privilege: list, division_privilege: list, data_filter: list
    ):
        """
        Get List Of visit cycle
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: branch_privilige: list
        :param: division_privilige: list
        :return:
            Visit Cycle Object
        """

        cycle = {}
        data = []
        start = page * limit - limit
        order = ''
        where = """WHERE (vp.is_approval = 1 AND vp.is_deleted = 0) 
        AND (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        where_original = where
        if column:
            if column == 'start_branch':
                order = """ORDER BY b1.name {0}""".format(direction)
            elif column == 'end_branch':
                order = """ORDER BY b2.name {0}""".format(direction)
            elif column == 'username':
                order = """ORDER BY u.username {0}""".format(direction)
            elif column == 'user':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY br.name {0}""".format(direction)
            elif column == 'division':
                order = """ORDER BY dv.division_name {0}""".format(direction)
            elif column == 'date':
                order = """ORDER BY vp.{0} {1}, vp.create_date {1}""".format(column, direction)
            else:
                order = """ORDER BY vp.{0} {1}""".format(column, direction)
        select = "vp.*"
        select_count = "vp.id"
        join = """as vp LEFT JOIN `users` as u ON vp.user_id = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id
        LEFT JOIN `branches` as br ON u.branch_id = br.id
        LEFT JOIN `divisions` as dv ON u.division_id = dv.id
        LEFT JOIN `branches` as b1 ON vp.start_route_branch_id = b1.id
        LEFT JOIN `branches` as b2 ON vp.end_route_branch_id = b2.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR br.name LIKE '%{0}%' OR dv.division_name LIKE '%{0}%' 
            OR b1.name LIKE '%{0}%' OR b2.name LIKE '%{0}%' OR e.name LIKE '%{0}%') """.format(search)
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date']:
                where += """AND (vp.date >= '{0} 00:00:00' AND vp.date <= '{1} 23:59:59') """.format(
                    data_filter['start_date'], data_filter['end_date']
                )
            if data_filter['user_id']:
                where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in data_filter['user_id']))
            if data_filter['branch_id']:
                where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['branch_id']))
            if data_filter['division_id']:
                where += """AND u.division_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['division_id']))

        # Mempersiapkan Query dan
        # Check apakah sudah di approve juga data tidak dalam posisi telah dihapus, dan
        # Check apakah user yang request memiliki hak akses untuk mendapatkan data ini
        # branch_user = aliased(BranchesModelAlchemy, name="branch_user")
        # branch_start = aliased(BranchesModelAlchemy, name="branch_start")
        # branch_end = aliased(BranchesModelAlchemy, name="branch_end")
        #
        # division_user = aliased(DivisionModelAlchemy, name="division_user")
        # visit_plan_query_prepare = session.query(VisitPlanModelAlchemy).join(
        #     UserModelAlchemy,
        #     VisitPlanModelAlchemy.user_id == UserModelAlchemy.id
        # ).join(
        #     EmployeeModelAlchemy,
        #     UserModelAlchemy.employee_id == EmployeeModelAlchemy.id
        # ).join(
        #     branch_user,
        #     UserModelAlchemy.branch_id == branch_user.id
        # ).join(
        #     division_user,
        #     UserModelAlchemy.division_id == division_user.id
        # ).join(
        #     branch_start,
        #     VisitPlanModelAlchemy.start_route_branch_id == branch_start.id
        # ).join(
        #     branch_end,
        #     VisitPlanModelAlchemy.end_route_branch_id == branch_end.id
        # ).filter(
        #     VisitPlanModelAlchemy.is_approval == 1
        # ).filter(
        #     VisitPlanModelAlchemy.is_deleted == 0
        # ).filter(
        #     UserModelAlchemy.branch_id.in_(branch_privilege)
        # ).filter(
        #     UserModelAlchemy.division_id.in_(division_privilege)
        # )
        # find = "%{}%".format(search)
        # # Search
        # if search:
        #     visit_plan_query_prepare = visit_plan_query_prepare.filter(
        #         or_(
        #             UserModelAlchemy.username.like(find), branch_user.name.like(find),
        #             division_user.division_name.like(find), branch_start.name.like(find), branch_end.name.like(find),
        #             EmployeeModelAlchemy.name.like(find)
        #         )
        #     )
        # # Check data filter
        # if data_filter:
        #     # Filter berdasarkan branch_id
        #     if data_filter['branch_id']:
        #         visit_plan_query_prepare = visit_plan_query_prepare.filter(
        #             UserModelAlchemy.branch_id.in_(data_filter['branch_id'])
        #         )
        #     # Filter berdasarkan division_id
        #     if data_filter['division_id']:
        #         visit_plan_query_prepare = visit_plan_query_prepare.filter(
        #             UserModelAlchemy.division_id.in_(data_filter['division_id'])
        #         )
        #
        #     # Filter berdasarkan start_date
        #     if data_filter['start_date']:
        #         visit_plan_query_prepare = visit_plan_query_prepare.filter(
        #             VisitPlanModelAlchemy.date >= data_filter['start_date']
        #         ).filter(
        #             VisitPlanModelAlchemy.date <= data_filter['end_date']
        #         )
        #
        #     # Filter berdasarkan user_id
        #     if data_filter['user_id']:
        #         visit_plan_query_prepare = visit_plan_query_prepare.filter(
        #             VisitPlanModelAlchemy.user_id.in_(data_filter['user_id'])
        #         )
        # # Check Order Tabel
        # if column:
        #     if column == 'start_branch':
        #         visit_plan_query_prepare = visit_plan_query_prepare.order_by(
        #             desc(branch_start.name) if direction is "desc" else asc(branch_start.name)
        #         )
        #     elif column == 'end_branch':
        #         visit_plan_query_prepare = visit_plan_query_prepare.order_by(
        #             desc(branch_end.name) if direction is "desc" else asc(branch_end.name)
        #         )
        #     elif column == 'username':
        #         visit_plan_query_prepare = visit_plan_query_prepare.order_by(
        #             desc(UserModelAlchemy.username) if direction is "desc" else asc(UserModelAlchemy.username)
        #         )
        #     elif column == 'user':
        #         visit_plan_query_prepare = visit_plan_query_prepare.order_by(
        #             desc(EmployeeModelAlchemy.name) if direction is "desc" else asc(EmployeeModelAlchemy.name)
        #         )
        #     elif column == 'branch':
        #         visit_plan_query_prepare = visit_plan_query_prepare.order_by(
        #             desc(branch_user.name) if direction is "desc" else asc(branch_user.name)
        #         )
        #     elif column == 'division':
        #         visit_plan_query_prepare = visit_plan_query_prepare.order_by(
        #             desc(division_user.division_name) if direction is "desc" else asc(division_user.division_name)
        #         )
        #     elif column == 'date':
        #         visit_plan_query_prepare = visit_plan_query_prepare.order_by(
        #             (desc(VisitPlanModelAlchemy.date) if direction is "desc" else asc(VisitPlanModelAlchemy.date)),
        #             (desc(VisitPlanModelAlchemy.create_date) if direction is "desc" else asc(
        #                 VisitPlanModelAlchemy.create_date
        #             ))
        #         )
        # else:
        #     order = """ORDER BY vp.{0} {1}""".format(column, direction)
        # count_all_visit_plan = visit_plan_query_prepare.count()
        # count_filtered_visit_plan = visit_plan_query_prepare.limit(limit).offset(start).count()
        # list_visit_plan = [VisitPlanModelAlchemy(x) for x in visit_plan_query_prepare.limit(limit).offset(start)]
        visit_plan_data = self.visit_plan_model.get_all_visit_plan(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.visit_plan_model.get_count_all_visit_plan(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.visit_plan_model.get_count_all_visit_plan(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if visit_plan_data:
            for vp in visit_plan_data:
                list_customer = []
                list_visited_customer = []
                list_new_customer = []
                list_unvisit_customer = []

                if vp['edit_data'] is not None:
                    vp['edit_data'] = json.loads(vp['edit_data'])
                if vp['date'] is not None:
                    vp['date'] = str(vp['date'])
                if vp['create_date'] is not None:
                    vp['create_date'] = str(vp['create_date'])
                if vp['update_date'] is not None:
                    vp['update_date'] = str(vp['update_date'])

                # Get Activity data
                data_activity_dict = dict()
                data_activity = []
                list_nfc_code = []

                plan_activity = []
                try:
                    # where = """WHERE (sa.id IN (SELECT MIN(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'START'
                    # GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MAX(id) FROM `sales_activity`
                    # WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MIN(id)
                    # FROM `sales_activity` WHERE `tap_nfc_type` = 'IN' GROUP BY user_id, visit_plan_id, nfc_code)
                    # OR sa.id IN (SELECT MAX(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'OUT'
                    # GROUP BY user_id, visit_plan_id, nfc_code)) AND (visit_plan_id = {0}) """.format(vp['id'])

                    # query without grouping
                    where = """ WHERE (
                            sa.id IN (SELECT MIN(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'START' GROUP BY user_id, visit_plan_id, nfc_code) OR
                            sa.id IN (SELECT MAX(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, visit_plan_id, nfc_code) OR
                            sa.id IN (SELECT id FROM `sales_activity` WHERE `tap_nfc_type` = 'IN' ) OR
                            sa.id IN (SELECT id FROM `sales_activity` WHERE `tap_nfc_type` = 'OUT')
                        ) AND (visit_plan_id = {0}) """.format(vp['id'])
                    order = ""
                    select = "sa.*"
                    join = """AS sa"""
                    activity_data = self.sales_activity_model.get_all_activity(
                        self.cursor, select=select, join=join, where=where, order=order, start=0, limit=1000
                    )

                    # Process data for Plan Activity key-> plan_activity
                    if activity_data:
                        for ad in activity_data:
                            if ad['tap_nfc_date'] is not None:
                                ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                            if ad['create_date'] is not None:
                                ad['create_date'] = str(ad['create_date'])
                            if ad['update_date'] is not None:
                                ad['update_date'] = str(ad['update_date'])

                            ad['branch_name'] = None
                            ad['branch_location'] = None
                            if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                                if ad['nfc_code'] is not None:
                                    try:
                                        branch = self.branch_model.get_branches_by_id(self.cursor, ad['nfc_code'])[0]
                                        ad['branch_name'] = branch['name']
                                        ad['branch_location'] = branch['address']
                                    except:
                                        ad['branch_name'] = None
                                        ad['branch_location'] = None
                                if ad['route_breadcrumb'] is not None:
                                    ad['route_breadcrumb'] = json.loads(ad['route_breadcrumb'])

                            ad['customer_code'] = None
                            ad['customer_name'] = None
                            ad['customer_address'] = None
                            if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                                if ad['nfc_code'] is not None:
                                    ad['customer_code'] = ad['nfc_code']
                                    try:
                                        customer = \
                                            self.customer_model.get_customer_by_code(self.cursor, ad['nfc_code'],
                                                                                     ignore_is_deleted=True)[0]
                                        ad['customer_name'] = customer['name']
                                        ad['customer_address'] = customer['address']
                                    except:
                                        ad['customer_name'] = None
                                        ad['customer_address'] = None
                                if ad['route_breadcrumb'] is not None:
                                    ad['route_breadcrumb'] = json.loads(ad['route_breadcrumb'])

                            if ad['user_id'] is not None:
                                try:
                                    ad['user'] = self.user_model.get_user_by_id(
                                        self.cursor, ad['user_id'],
                                        select="username, employee_id, branch_id, division_id"
                                    )[0]
                                    if ad['user']['employee_id'] is not None:
                                        try:
                                            ad['user']['name'] = self.employee_model.get_employee_by_id(
                                                self.cursor,
                                                ad['user']['employee_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['name'] = None
                                    if ad['user']['branch_id'] is not None:
                                        try:
                                            ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                self.cursor,
                                                ad['user']['branch_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['branch_name'] = None
                                    if ad['user']['division_id'] is not None:
                                        try:
                                            ad['user']['division_name'] = self.division_model.get_division_by_id(
                                                self.cursor, ad['user']['division_id'], select="division_name")[0][
                                                'division_name']
                                        except:
                                            ad['user']['division_name'] = None
                                except:
                                    ad['user'] = {}
                            else:
                                ad['user'] = {}

                            # check activity checkin on customer, not checkin on branch
                            if ad['nfc_code'] is not None and ad['customer_name'] is not None:
                                if len(list_visited_customer) > 0:
                                    if ad['nfc_code'] not in list_visited_customer:
                                        list_visited_customer.append(ad['nfc_code'])
                                else:
                                    list_visited_customer.append(ad['nfc_code'])

                            plan_activity.append(ad)

                    if plan_activity:
                        plan_activity_list = []
                        for rec in plan_activity:
                            plan_activity_dict = dict()
                            # print("======== Plan Activity {0}".format(rec))
                            if rec['tap_nfc_type'] == 'START':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = 0
                                plan_activity_dict['start_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['start_location_custom'] = False
                                    plan_activity_dict['start_location_name'] = rec['branch_name']
                                    plan_activity_dict['start_location_address'] = rec['branch_location']
                                else:
                                    # custom start
                                    plan_activity_dict['start_location_custom'] = True
                                    plan_activity_dict['start_location_name'] = None
                                    plan_activity_dict['start_location_address'] = rec['route_breadcrumb']['address']
                                plan_activity_dict['start_location'] = rec['route_breadcrumb']

                            if rec['tap_nfc_type'] == 'STOP':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = 0
                                plan_activity_dict['stop_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['stop_location_custom'] = False
                                    plan_activity_dict['stop_location_name'] = rec['branch_name']
                                    plan_activity_dict['stop_location_address'] = rec['branch_location']
                                else:
                                    # custom stop
                                    plan_activity_dict['stop_location_custom'] = True
                                    plan_activity_dict['stop_location_name'] = None
                                    plan_activity_dict['stop_location_address'] = rec['route_breadcrumb']['address']
                                plan_activity_dict['stop_location'] = rec['route_breadcrumb']

                            if rec['tap_nfc_type'] == 'IN':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = rec['distance']
                                plan_activity_dict['in_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['in_location_custom'] = False
                                    plan_activity_dict['in_location_name'] = rec['customer_name']
                                    plan_activity_dict['in_location_address'] = rec['customer_address']
                                else:
                                    # custom checkin
                                    plan_activity_dict['in_location_custom'] = True
                                    plan_activity_dict['in_location_name'] = rec['customer_name']
                                    plan_activity_dict['in_location_address'] = rec['route_breadcrumb']['address']

                            if rec['tap_nfc_type'] == 'OUT':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['out_time'] = rec['tap_nfc_date']

                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['out_location_custom'] = False
                                    plan_activity_dict['out_location_name'] = rec['customer_name']
                                    plan_activity_dict['out_location_address'] = rec['customer_address']
                                else:
                                    # custom checkout
                                    plan_activity_dict['out_location_custom'] = True
                                    plan_activity_dict['out_location_name'] = rec['customer_name']
                                    plan_activity_dict['out_location_address'] = rec['route_breadcrumb']['address']

                            plan_activity_list.append(plan_activity_dict)
                        plan_result = []
                        i = 0
                        for plan in plan_activity_list:
                            data_dict = dict()
                            if plan.get('start_time'):
                                data_dict['nfc_code'] = plan['nfc_code']
                                data_dict['start_time'] = plan['start_time']
                                data_dict['location_name'] = plan['start_location_name']
                                data_dict['location_address'] = plan['start_location_address']
                                data_dict['location_custom'] = plan['start_location_custom']
                                data_dict['distance'] = plan['distance']
                                data_dict['duration'] = 0

                            if plan.get('in_time'):
                                code = plan['nfc_code']
                                data_dict['nfc_code'] = code
                                data_dict['in_time'] = plan['in_time']
                                data_dict['distance'] = plan['distance']
                                data_dict['in_location_address'] = plan['in_location_address']
                                data_dict['in_location_name'] = plan['in_location_name']
                                data_dict['in_location_custom'] = plan['in_location_custom']
                                next_idx = i
                                next = next_idx + 1
                                if plan_activity_list[next]['nfc_code'] == code and plan_activity_list[next][
                                    'tap_nfc_type'] == 'OUT':
                                    # Tap Type STOP found
                                    data_dict['out_time'] = plan_activity_list[next]['out_time']
                                    data_dict['out_location_address'] = plan_activity_list[next]['out_location_address']
                                    data_dict['out_location_name'] = plan_activity_list[next]['out_location_name']
                                    data_dict['out_location_custom'] = plan_activity_list[next]['out_location_custom']

                                    # calculate duration
                                    out_time = datetime.strptime(data_dict['out_time'], "%Y-%m-%d %H:%M:%S")
                                    in_time = datetime.strptime(data_dict['in_time'], "%Y-%m-%d %H:%M:%S")
                                    if out_time > in_time:
                                        data_dict['duration'] = int((out_time - in_time).seconds / 60)
                                    else:
                                        data_dict['duration'] = 0
                                else:
                                    data_dict['out_time'] = None
                                    data_dict['out_location_address'] = None
                                    data_dict['out_location_name'] = None
                                    data_dict['out_location_custom'] = False
                                    data_dict['duration'] = 0

                            if plan.get('stop_time'):
                                data_dict['nfc_code'] = plan['nfc_code']
                                data_dict['stop_time'] = plan['stop_time']
                                data_dict['location_name'] = plan['stop_location_name']
                                data_dict['location_address'] = plan['stop_location_address']
                                data_dict['location_custom'] = plan['stop_location_custom']
                                data_dict['distance'] = plan['distance']
                                data_dict['duration'] = 0

                            if data_dict:
                                plan_result.append(data_dict)
                            i += 1

                        # calculate time range between activity
                        # and add key order
                        position = 0
                        if plan_result:
                            for plan in plan_result:
                                plan['order'] = position
                                if plan.get('start_time') and position == 0:
                                    plan['time_range'] = 0
                                else:
                                    if plan.get('in_time'):
                                        next_time = plan['in_time']
                                    elif plan.get('stop_time'):
                                        next_time = plan['stop_time']
                                    else:
                                        next_time = 0

                                    post = position
                                    index = post - 1
                                    if index >= 0:
                                        if plan_result[index].get('start_time'):
                                            prev_time = plan_result[index]['start_time']
                                        elif plan_result[index].get('out_time'):
                                            prev_time = plan_result[index]['out_time']
                                        else:
                                            prev_time = 0
                                    else:
                                        prev_time = 0

                                    if prev_time and next_time:
                                        prev_time_fmt = datetime.strptime(prev_time, "%Y-%m-%d %H:%M:%S")
                                        next_time_fmt = datetime.strptime(next_time, "%Y-%m-%d %H:%M:%S")
                                        if next_time_fmt > prev_time_fmt:
                                            plan['time_range'] = int((next_time_fmt - prev_time_fmt).seconds / 60)
                                        else:
                                            plan['time_range'] = 0
                                    else:
                                        plan['time_range'] = 0
                                position += 1
                            # print("result Plan Activity = {0}".format(plan_result))
                        vp['plan_activity'] = plan_result
                    else:
                        vp['plan_activity'] = []

                    # Process data for data Activity key-> data_activity
                    # previous process before ignore grouping
                    if activity_data:
                        for ad in activity_data:
                            if ad['tap_nfc_date'] is not None:
                                ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                            if ad['create_date'] is not None:
                                ad['create_date'] = str(ad['create_date'])
                            if ad['update_date'] is not None:
                                ad['update_date'] = str(ad['update_date'])
                            ad['branch_name'] = None
                            if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                                if ad['nfc_code'] is not None:
                                    try:
                                        ad['branch_name'] = self.branch_model.get_branches_by_id(
                                            self.cursor, ad['nfc_code'], select="""name"""
                                        )[0]['name']
                                    except:
                                        ad['branch_name'] = None
                                if ad['route_breadcrumb'] is not None:
                                    ad['route_breadcrumb'] = json.loads(ad['route_breadcrumb']) if type(
                                        ad['route_breadcrumb']) is str else ad['route_breadcrumb']
                            ad['customer_code'] = None
                            if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                                if ad['nfc_code'] is not None:
                                    ad['customer_code'] = ad['nfc_code']
                            if ad['user_id'] is not None:
                                try:
                                    ad['user'] = self.user_model.get_user_by_id(
                                        self.cursor, ad['user_id'],
                                        select="username, employee_id, branch_id, division_id"
                                    )[0]
                                    if ad['user']['employee_id'] is not None:
                                        try:
                                            ad['user']['name'] = self.employee_model.get_employee_by_id(
                                                self.cursor,
                                                ad['user']['employee_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['name'] = None
                                    if ad['user']['branch_id'] is not None:
                                        try:
                                            ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                self.cursor,
                                                ad['user']['branch_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['branch_name'] = None
                                    if ad['user']['division_id'] is not None:
                                        try:
                                            ad['user']['division_name'] = self.division_model.get_division_by_id(
                                                self.cursor, ad['user']['division_id'], select="division_name")[0][
                                                'division_name']
                                        except:
                                            ad['user']['division_name'] = None
                                except:
                                    ad['user'] = {}
                            else:
                                ad['user'] = {}
                            if ad['nfc_code'] is not None:
                                data_activity_dict[ad['nfc_code']] = dict()
                                list_nfc_code.append(ad['nfc_code'])
                            data_activity.append(ad)
                    if data_activity:
                        for rec in data_activity:
                            if rec['tap_nfc_type'] == 'START':
                                data_activity_dict[rec['nfc_code']]['start_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = 0
                            if rec['tap_nfc_type'] == 'STOP':
                                data_activity_dict[rec['nfc_code']]['stop_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = 0
                            if rec['tap_nfc_type'] == 'IN':
                                data_activity_dict[rec['nfc_code']]['in_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = rec['distance']
                            if rec['tap_nfc_type'] == 'OUT':
                                data_activity_dict[rec['nfc_code']]['out_time'] = rec['tap_nfc_date']

                        # Calculation duration
                        unique_code = set(list_nfc_code)
                        for code in unique_code:
                            if data_activity_dict[code].get('in_time'):
                                in_time = data_activity_dict[code]['in_time']
                            else:
                                in_time = 0
                            if data_activity_dict[code].get('out_time'):
                                out_time = data_activity_dict[code]['out_time']
                            else:
                                out_time = 0
                            if in_time and out_time:
                                out_time_fmt = datetime.strptime(out_time, "%Y-%m-%d %H:%M:%S")
                                in_time_fmt = datetime.strptime(in_time, "%Y-%m-%d %H:%M:%S")
                                data_activity_dict[code]['duration'] = int((out_time_fmt - in_time_fmt).seconds / 60)
                            else:
                                data_activity_dict[code]['duration'] = 0

                    vp['data_activity'] = data_activity_dict
                except Exception as e:
                    print("Some Exception {}".format(e))
                    vp['data_activity'] = dict()
                    vp['plan_activity'] = []

                # Get Data Performance
                try:
                    performance_date = vp['date'].split(" ")
                    performance_date = performance_date[0]
                    data_performance = self.get_statistic_performance_by_user_id(
                        job_function='sales', user_ids=[vp['user_id']], start_date=performance_date,
                        end_date=performance_date, plan_id=vp['id']
                    )
                    # vp['data_performance'] = data_performance

                    # TODO Get Data Total Distance
                    select = "*"
                    where_distance = """WHERE user_id={0} AND tap_nfc_type='STOP' """.format(vp['user_id'])
                    where_distance += """AND visit_plan_id={} """.format(vp['id'])
                    where_distance += """AND (tap_nfc_date >= '{0} 00:00:00' AND tap_nfc_date <= '{1} 23:59:59') """.format(
                        performance_date, performance_date)
                    order = 'ORDER BY create_date ASC'
                    data_distance = self.sales_activity_model.get_all_activity(self.cursor, select=select,
                                                                               where=where_distance, order=order)
                    total_distance = 0
                    if data_distance:
                        for rec_distance in data_distance:
                            total_distance += rec_distance['total_distance']
                    data_performance['total_distance'] = total_distance

                    vp['data_performance'] = data_performance
                except Exception as e:
                    print(e)
                    vp['data_performance'] = dict()
                if vp['destination_order'] is not None:
                    vp['destination_order'] = json.loads(vp['destination_order'])
                if vp['destination'] is not None:
                    vp['destination'] = json.loads(vp['destination'])
                    idx = 0
                    for rec in vp['destination']:
                        try:
                            customer = self.customer_model.get_customer_by_id(
                                self.cursor, rec['customer_code'],
                                select="name, email, phone, address, lng, lat, nfcid, contacts, business_activity")[0]
                            vp['destination'][idx]['customer_name'] = customer['name']
                            vp['destination'][idx]['customer_email'] = customer['email']
                            vp['destination'][idx]['phone'] = customer['phone']
                            vp['destination'][idx]['address'] = customer['address']
                            vp['destination'][idx]['lng'] = customer['lng']
                            vp['destination'][idx]['lat'] = customer['lat']
                            vp['destination'][idx]['nfcid'] = customer['nfcid']
                            if customer['contacts'] is not None:
                                vp['destination'][idx]['contacts'] = json.loads(customer['contacts'])
                            else:
                                vp['destination'][idx]['contacts'] = None
                            if customer['business_activity'] is not None:
                                vp['destination'][idx]['business_activity'] = json.loads(customer['business_activity'])
                            else:
                                vp['destination'][idx]['business_activity'] = None
                        except:
                            vp['destination'][idx]['customer_name'] = None
                            vp['destination'][idx]['customer_email'] = None
                            vp['destination'][idx]['phone'] = None
                            vp['destination'][idx]['address'] = None
                            vp['destination'][idx]['lng'] = None
                            vp['destination'][idx]['lat'] = None
                            vp['destination'][idx]['nfcid'] = None
                            vp['destination'][idx]['contacts'] = None
                            vp['destination'][idx]['business_activity'] = None
                        list_customer.append(rec['customer_code'])
                        idx += 1
                if vp['destination_new'] is not None:
                    vp['destination_new'] = json.loads(vp['destination_new'])
                    for rec in vp['destination_new']:
                        list_new_customer.append(rec['customer_code'])

                # process unvisited customer
                list_all_customer = list_customer
                list_all_customer.extend(list_new_customer)
                if len(list_all_customer) >= len(list_visited_customer):
                    diff = list(set(list_all_customer) - set(list_visited_customer))
                    for code in diff:
                        data_cust = dict()
                        try:
                            customer = self.customer_model.get_customer_by_id(
                                self.cursor, code,
                                select="name, email, phone, address, lng, lat, nfcid, contacts, business_activity")[0]
                            data_cust['customer_name'] = customer['name']
                            data_cust['customer_email'] = customer['email']
                            data_cust['phone'] = customer['phone']
                            data_cust['address'] = customer['address']
                            data_cust['lng'] = customer['lng']
                            data_cust['lat'] = customer['lat']
                            data_cust['nfcid'] = customer['nfcid']
                            if customer['contacts'] is not None:
                                data_cust['contacts'] = json.loads(customer['contacts'])
                            else:
                                data_cust['contacts'] = None
                            if customer['business_activity'] is not None:
                                data_cust['business_activity'] = json.loads(customer['business_activity'])
                            else:
                                data_cust['business_activity'] = None
                        except:
                            data_cust['customer_name'] = None
                            data_cust['customer_email'] = None
                            data_cust['phone'] = None
                            data_cust['address'] = None
                            data_cust['lng'] = None
                            data_cust['lat'] = None
                            data_cust['nfcid'] = None
                            data_cust['contacts'] = None
                            data_cust['business_activity'] = None
                        list_unvisit_customer.append(data_cust)

                vp['unvisit_customer'] = list_unvisit_customer
                vp['total_customer'] = len(set(list_customer))
                if vp['user_id'] is not None:
                    try:
                        vp['user'] = self.user_model.get_user_by_id(
                            self.cursor, vp['user_id'], select="username, employee_id, branch_id, division_id")[0]
                    except:
                        vp['user'] = {}
                    if vp['user']['employee_id'] is not None:
                        try:
                            vp['user']['name'] = self.employee_model.get_employee_by_id(
                                self.cursor, vp['user']['employee_id'], select="""name""")[0]['name']
                        except:
                            vp['user']['name'] = None
                    if vp['user']['branch_id'] is not None:
                        try:
                            vp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, vp['user']['branch_id'], select="""name""")[0]['name']
                        except:
                            vp['user']['branch_name'] = None
                    if vp['user']['division_id'] is not None:
                        try:
                            vp['user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, vp['user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            vp['user']['division_name'] = None
                    else:
                        vp['user']['division_name'] = None
                else:
                    vp['user'] = {}
                if vp['start_route_branch_id'] is not None:
                    try:
                        vp['start_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, vp['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        vp['start_route_branch'] = {}
                else:
                    vp['start_route_branch'] = {}
                if vp['end_route_branch_id'] is not None:
                    try:
                        vp['end_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, vp['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        vp['end_route_branch'] = {}
                else:
                    vp['end_route_branch'] = {}
                del vp['route']

                data.append(vp)
        cycle['data'] = data
        cycle['total'] = count
        cycle['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if cycle['total_filter'] > page * limit:
            cycle['has_next'] = True
        else:
            cycle['has_next'] = False
        if limit <= page * count_filter - count_filter:
            cycle['has_prev'] = True
        else:
            cycle['has_prev'] = False
        return cycle

    def get_all_export_activity_data_by_visit_plan(
            self, page: int, limit: int, search: str, column: str, direction: str,
            branch_privilege: list, division_privilege: list, data_filter: list
    ):
        """
        Get List Of visit cycle
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: branch_privilige: list
        :param: division_privilige: list
        :return:
            Visit Cycle Object
        """
        result_data = {}
        cycle = {}
        data = []
        start = page * limit - limit
        order = ''
        where = """WHERE (vp.is_approval = 1 AND vp.is_deleted = 0) 
        AND (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        where_original = where
        if column:
            if column == 'start_branch':
                order = """ORDER BY b1.name {0}""".format(direction)
            elif column == 'end_branch':
                order = """ORDER BY b2.name {0}""".format(direction)
            elif column == 'username':
                order = """ORDER BY u.username {0}""".format(direction)
            elif column == 'user':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY br.name {0}""".format(direction)
            elif column == 'division':
                order = """ORDER BY dv.division_name {0}""".format(direction)
            elif column == 'date':
                order = """ORDER BY vp.{0} {1}, vp.create_date {1}""".format(column, direction)
            else:
                order = """ORDER BY vp.{0} {1}""".format(column, direction)
        select = "vp.*"
        select_count = "vp.id"
        join = """as vp LEFT JOIN `users` as u ON vp.user_id = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id
        LEFT JOIN `branches` as br ON u.branch_id = br.id
        LEFT JOIN `divisions` as dv ON u.division_id = dv.id
        LEFT JOIN `branches` as b1 ON vp.start_route_branch_id = b1.id
        LEFT JOIN `branches` as b2 ON vp.end_route_branch_id = b2.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR br.name LIKE '%{0}%' OR dv.division_name LIKE '%{0}%' 
            OR b1.name LIKE '%{0}%' OR b2.name LIKE '%{0}%' OR e.name LIKE '%{0}%') """.format(search)
        if data_filter:
            tmp_data_filter = data_filter[0]
            if tmp_data_filter['start_date']:
                where += """AND (vp.date >= '{0} 00:00:00' AND vp.date <= '{1} 23:59:59') """.format(
                    tmp_data_filter['start_date'], tmp_data_filter['end_date']
                )
            if tmp_data_filter['user_id']:
                where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['user_id']))
            if tmp_data_filter['branch_id']:
                where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['branch_id']))
            if tmp_data_filter['division_id']:
                where += """AND u.division_id IN ({0}) """.format(
                    ", ".join(str(x) for x in tmp_data_filter['division_id']))

        visit_plan_data = self.visit_plan_model.get_all_visit_plan(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        # count_filter = self.visit_plan_model.get_count_all_visit_plan(
        #     self.cursor, select=select_count, join=join, where=where
        # )
        # count = self.visit_plan_model.get_count_all_visit_plan(
        #     self.cursor, select=select_count, join=join, where=where_original
        # )
        if visit_plan_data:
            for vp in visit_plan_data:
                list_customer = []
                if vp['edit_data'] is not None:
                    vp['edit_data'] = json.loads(vp['edit_data'])
                if vp['date'] is not None:
                    vp['date'] = str(vp['date'])
                if vp['create_date'] is not None:
                    vp['create_date'] = str(vp['create_date'])
                if vp['update_date'] is not None:
                    vp['update_date'] = str(vp['update_date'])

                # Get Activity data
                data_activity_dict = dict()
                data_activity = []
                list_nfc_code = []

                plan_activity = []
                try:
                    # where = """WHERE (sa.id IN (SELECT MIN(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'START'
                    # GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MAX(id) FROM `sales_activity`
                    # WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MIN(id)
                    # FROM `sales_activity` WHERE `tap_nfc_type` = 'IN' GROUP BY user_id, visit_plan_id, nfc_code)
                    # OR sa.id IN (SELECT MAX(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'OUT'
                    # GROUP BY user_id, visit_plan_id, nfc_code)) AND (visit_plan_id = {0}) """.format(vp['id'])

                    # query without grouping
                    where = """ WHERE (
                            sa.id IN (SELECT MIN(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'START' GROUP BY user_id, visit_plan_id, nfc_code) OR
                            sa.id IN (SELECT MAX(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, visit_plan_id, nfc_code) OR
                            sa.id IN (SELECT id FROM `sales_activity` WHERE `tap_nfc_type` = 'IN' ) OR
                            sa.id IN (SELECT id FROM `sales_activity` WHERE `tap_nfc_type` = 'OUT')
                        ) AND (visit_plan_id = {0}) """.format(vp['id'])
                    order = ""
                    select = "sa.*"
                    join = """AS sa"""
                    activity_data = self.sales_activity_model.get_all_activity(
                        self.cursor, select=select, join=join, where=where, order=order, start=0, limit=1000
                    )

                    # Process data for Plan Activity key-> plan_activity
                    if activity_data:
                        for ad in activity_data:
                            if ad['tap_nfc_date'] is not None:
                                ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                            if ad['create_date'] is not None:
                                ad['create_date'] = str(ad['create_date'])
                            if ad['update_date'] is not None:
                                ad['update_date'] = str(ad['update_date'])

                            ad['branch_name'] = None
                            ad['branch_location'] = None
                            if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                                if ad['nfc_code'] is not None:
                                    try:
                                        branch = self.branch_model.get_branches_by_id(self.cursor, ad['nfc_code'])[0]
                                        ad['branch_name'] = branch['name']
                                        ad['branch_location'] = branch['address']
                                    except:
                                        ad['branch_name'] = None
                                        ad['branch_location'] = None
                                if ad['route_breadcrumb'] is not None:
                                    ad['route_breadcrumb'] = json.loads(ad['route_breadcrumb'])

                            ad['customer_code'] = None
                            ad['customer_name'] = None
                            ad['customer_address'] = None
                            if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                                if ad['nfc_code'] is not None:
                                    ad['customer_code'] = ad['nfc_code']
                                    try:
                                        customer = \
                                            self.customer_model.get_customer_by_code(self.cursor, ad['nfc_code'])[0]
                                        ad['customer_name'] = customer['name']
                                        ad['customer_address'] = customer['address']
                                    except:
                                        ad['customer_name'] = None
                                        ad['customer_address'] = None
                                if ad['route_breadcrumb'] is not None:
                                    ad['route_breadcrumb'] = json.loads(ad['route_breadcrumb'])

                            if ad['user_id'] is not None:
                                try:
                                    ad['user'] = self.user_model.get_user_by_id(
                                        self.cursor, ad['user_id'],
                                        select="username, employee_id, branch_id, division_id"
                                    )[0]
                                    if ad['user']['employee_id'] is not None:
                                        try:
                                            ad['user']['name'] = self.employee_model.get_employee_by_id(
                                                self.cursor,
                                                ad['user']['employee_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['name'] = None
                                    if ad['user']['branch_id'] is not None:
                                        try:
                                            ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                self.cursor,
                                                ad['user']['branch_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['branch_name'] = None
                                    if ad['user']['division_id'] is not None:
                                        try:
                                            ad['user']['division_name'] = self.division_model.get_division_by_id(
                                                self.cursor, ad['user']['division_id'], select="division_name")[0][
                                                'division_name']
                                        except:
                                            ad['user']['division_name'] = None
                                except:
                                    ad['user'] = {}
                            else:
                                ad['user'] = {}

                            plan_activity.append(ad)

                    if plan_activity:
                        plan_activity_list = []
                        for rec in plan_activity:
                            plan_activity_dict = dict()
                            # print("======== Plan Activity {0}".format(rec))
                            if rec['tap_nfc_type'] == 'START':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = 0
                                plan_activity_dict['start_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['start_location_custom'] = False
                                    plan_activity_dict['start_location_name'] = rec['branch_name']
                                    plan_activity_dict['start_location_address'] = rec['branch_location']
                                else:
                                    # custom start
                                    plan_activity_dict['start_location_custom'] = True
                                    plan_activity_dict['start_location_name'] = None
                                    plan_activity_dict['start_location_address'] = rec['route_breadcrumb']['address']
                                plan_activity_dict['start_location'] = rec['route_breadcrumb']

                            if rec['tap_nfc_type'] == 'STOP':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = 0
                                plan_activity_dict['stop_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['stop_location_custom'] = False
                                    plan_activity_dict['stop_location_name'] = rec['branch_name']
                                    plan_activity_dict['stop_location_address'] = rec['branch_location']
                                else:
                                    # custom stop
                                    plan_activity_dict['stop_location_custom'] = True
                                    plan_activity_dict['stop_location_name'] = None
                                    plan_activity_dict['stop_location_address'] = rec['route_breadcrumb']['address']
                                plan_activity_dict['stop_location'] = rec['route_breadcrumb']

                            if rec['tap_nfc_type'] == 'IN':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = rec['distance']
                                plan_activity_dict['in_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['in_location_custom'] = False
                                    plan_activity_dict['in_location_name'] = rec['customer_name']
                                    plan_activity_dict['in_location_address'] = rec['customer_address']
                                else:
                                    # custom checkin
                                    plan_activity_dict['in_location_custom'] = True
                                    plan_activity_dict['in_location_name'] = rec['customer_name']
                                    plan_activity_dict['in_location_address'] = rec['route_breadcrumb']['address']

                            if rec['tap_nfc_type'] == 'OUT':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['out_time'] = rec['tap_nfc_date']

                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['out_location_custom'] = False
                                    plan_activity_dict['out_location_name'] = rec['customer_name']
                                    plan_activity_dict['out_location_address'] = rec['customer_address']
                                else:
                                    # custom checkout
                                    plan_activity_dict['out_location_custom'] = True
                                    plan_activity_dict['out_location_name'] = rec['customer_name']
                                    plan_activity_dict['out_location_address'] = rec['route_breadcrumb']['address']

                            plan_activity_list.append(plan_activity_dict)
                        plan_result = []
                        i = 0
                        for plan in plan_activity_list:
                            data_dict = dict()
                            if plan.get('start_time'):
                                data_dict['nfc_code'] = plan['nfc_code']
                                data_dict['start_time'] = plan['start_time']
                                data_dict['location_name'] = plan['start_location_name']
                                data_dict['location_address'] = plan['start_location_address']
                                data_dict['location_custom'] = plan['start_location_custom']
                                data_dict['distance'] = plan['distance']
                                data_dict['duration'] = 0

                            if plan.get('in_time'):
                                code = plan['nfc_code']
                                data_dict['nfc_code'] = code
                                data_dict['in_time'] = plan['in_time']
                                data_dict['distance'] = plan['distance']
                                data_dict['in_location_address'] = plan['in_location_address']
                                data_dict['in_location_name'] = plan['in_location_name']
                                data_dict['in_location_custom'] = plan['in_location_custom']
                                next_idx = i
                                next = next_idx + 1
                                if plan_activity_list[next]['nfc_code'] == code and plan_activity_list[next][
                                    'tap_nfc_type'] == 'OUT':
                                    # Tap Type STOP found
                                    data_dict['out_time'] = plan_activity_list[next]['out_time']
                                    data_dict['out_location_address'] = plan_activity_list[next]['out_location_address']
                                    data_dict['out_location_name'] = plan_activity_list[next]['out_location_name']
                                    data_dict['out_location_custom'] = plan_activity_list[next]['out_location_custom']

                                    # calculate duration
                                    out_time = datetime.strptime(data_dict['out_time'], "%Y-%m-%d %H:%M:%S")
                                    in_time = datetime.strptime(data_dict['in_time'], "%Y-%m-%d %H:%M:%S")
                                    if out_time > in_time:
                                        data_dict['duration'] = int((out_time - in_time).seconds / 60)
                                    else:
                                        data_dict['duration'] = 0
                                else:
                                    data_dict['out_time'] = None
                                    data_dict['out_location_address'] = None
                                    data_dict['out_location_name'] = None
                                    data_dict['out_location_custom'] = False
                                    data_dict['duration'] = 0

                            if plan.get('stop_time'):
                                data_dict['nfc_code'] = plan['nfc_code']
                                data_dict['stop_time'] = plan['stop_time']
                                data_dict['location_name'] = plan['stop_location_name']
                                data_dict['location_address'] = plan['stop_location_address']
                                data_dict['location_custom'] = plan['stop_location_custom']
                                data_dict['distance'] = plan['distance']
                                data_dict['duration'] = 0

                            if data_dict:
                                plan_result.append(data_dict)
                            i += 1

                        # calculate time range between activity
                        # and add key order
                        position = 0
                        if plan_result:
                            for plan in plan_result:
                                plan['order'] = position
                                if plan.get('start_time') and position == 0:
                                    plan['time_range'] = 0
                                else:
                                    if plan.get('in_time'):
                                        next_time = plan['in_time']
                                    elif plan.get('stop_time'):
                                        next_time = plan['stop_time']
                                    else:
                                        next_time = 0

                                    post = position
                                    index = post - 1
                                    if index >= 0:
                                        if plan_result[index].get('start_time'):
                                            prev_time = plan_result[index]['start_time']
                                        elif plan_result[index].get('out_time'):
                                            prev_time = plan_result[index]['out_time']
                                        else:
                                            prev_time = 0
                                    else:
                                        prev_time = 0

                                    if prev_time and next_time:
                                        prev_time_fmt = datetime.strptime(prev_time, "%Y-%m-%d %H:%M:%S")
                                        next_time_fmt = datetime.strptime(next_time, "%Y-%m-%d %H:%M:%S")
                                        if next_time_fmt > prev_time_fmt:
                                            plan['time_range'] = int((next_time_fmt - prev_time_fmt).seconds / 60)
                                        else:
                                            plan['time_range'] = 0
                                    else:
                                        plan['time_range'] = 0
                                position += 1
                            # print("result Plan Activity = {0}".format(plan_result))
                        vp['plan_activity'] = plan_result
                    else:
                        vp['plan_activity'] = []

                    # Process data for data Activity key-> data_activity
                    # previous process before ignore grouping
                    if activity_data:
                        for ad in activity_data:
                            if ad['tap_nfc_date'] is not None:
                                ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                            if ad['create_date'] is not None:
                                ad['create_date'] = str(ad['create_date'])
                            if ad['update_date'] is not None:
                                ad['update_date'] = str(ad['update_date'])
                            ad['branch_name'] = None
                            if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                                if ad['nfc_code'] is not None:
                                    try:
                                        ad['branch_name'] = self.branch_model.get_branches_by_id(
                                            self.cursor, ad['nfc_code'], select="""name"""
                                        )[0]['name']
                                    except:
                                        ad['branch_name'] = None
                                if ad['route_breadcrumb'] is not None:
                                    ad['route_breadcrumb'] = json.loads(json.dumps(ad['route_breadcrumb']))
                            ad['customer_code'] = None
                            if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                                if ad['nfc_code'] is not None:
                                    ad['customer_code'] = ad['nfc_code']
                            if ad['user_id'] is not None:
                                try:
                                    ad['user'] = self.user_model.get_user_by_id(
                                        self.cursor, ad['user_id'],
                                        select="username, employee_id, branch_id, division_id"
                                    )[0]
                                    if ad['user']['employee_id'] is not None:
                                        try:
                                            ad['user']['name'] = self.employee_model.get_employee_by_id(
                                                self.cursor,
                                                ad['user']['employee_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['name'] = None
                                    if ad['user']['branch_id'] is not None:
                                        try:
                                            ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                self.cursor,
                                                ad['user']['branch_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['branch_name'] = None
                                    if ad['user']['division_id'] is not None:
                                        try:
                                            ad['user']['division_name'] = self.division_model.get_division_by_id(
                                                self.cursor, ad['user']['division_id'], select="division_name")[0][
                                                'division_name']
                                        except:
                                            ad['user']['division_name'] = None
                                except:
                                    ad['user'] = {}
                            else:
                                ad['user'] = {}
                            if ad['nfc_code'] is not None:
                                data_activity_dict[ad['nfc_code']] = dict()
                                list_nfc_code.append(ad['nfc_code'])
                            data_activity.append(ad)
                    if data_activity:
                        for rec in data_activity:
                            if rec['tap_nfc_type'] == 'START':
                                data_activity_dict[rec['nfc_code']]['start_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = 0
                            if rec['tap_nfc_type'] == 'STOP':
                                data_activity_dict[rec['nfc_code']]['stop_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = 0
                            if rec['tap_nfc_type'] == 'IN':
                                data_activity_dict[rec['nfc_code']]['in_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = rec['distance']
                            if rec['tap_nfc_type'] == 'OUT':
                                data_activity_dict[rec['nfc_code']]['out_time'] = rec['tap_nfc_date']

                        # Calculation duration
                        unique_code = set(list_nfc_code)
                        for code in unique_code:
                            if data_activity_dict[code].get('in_time'):
                                in_time = data_activity_dict[code]['in_time']
                            else:
                                in_time = 0
                            if data_activity_dict[code].get('out_time'):
                                out_time = data_activity_dict[code]['out_time']
                            else:
                                out_time = 0
                            if in_time and out_time:
                                out_time_fmt = datetime.strptime(out_time, "%Y-%m-%d %H:%M:%S")
                                in_time_fmt = datetime.strptime(in_time, "%Y-%m-%d %H:%M:%S")
                                data_activity_dict[code]['duration'] = int((out_time_fmt - in_time_fmt).seconds / 60)
                            else:
                                data_activity_dict[code]['duration'] = 0

                    vp['data_activity'] = data_activity_dict
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print("Kesalahan {}".format(e), exc_type, fname, exc_tb.tb_lineno)
                    vp['data_activity'] = dict()
                    vp['plan_activity'] = []

                # Get Data Performance
                try:
                    performance_date = vp['date'].split(" ")
                    performance_date = performance_date[0]
                    data_performance = self.get_statistic_performance_by_user_id(
                        job_function='sales', user_ids=[vp['user_id']], start_date=performance_date,
                        end_date=performance_date, plan_id=vp['id']
                    )
                    # vp['data_performance'] = data_performance

                    # TODO Get Data Total Distance
                    select = "*"
                    where_distance = """WHERE user_id={0} AND tap_nfc_type='STOP' """.format(vp['user_id'])
                    where_distance += """AND visit_plan_id={} """.format(vp['id'])
                    where_distance += """AND (tap_nfc_date >= '{0} 00:00:00' AND tap_nfc_date <= '{1} 23:59:59') """.format(
                        performance_date, performance_date)
                    order = 'ORDER BY create_date ASC'
                    data_distance = self.sales_activity_model.get_all_activity(self.cursor, select=select,
                                                                               where=where_distance, order=order)
                    total_distance = 0
                    if data_distance:
                        for rec_distance in data_distance:
                            total_distance += rec_distance['total_distance']
                    data_performance['total_distance'] = total_distance

                    vp['data_performance'] = data_performance
                except Exception as e:
                    print(e)
                    vp['data_performance'] = dict()
                if vp['destination_order'] is not None:
                    vp['destination_order'] = json.loads(vp['destination_order'])
                if vp['destination'] is not None:
                    vp['destination'] = json.loads(vp['destination'])
                    idx = 0
                    for rec in vp['destination']:
                        try:
                            customer = self.customer_model.get_customer_by_id(
                                self.cursor, rec['customer_code'],
                                select="name, email, phone, address, lng, lat, nfcid, contacts, business_activity")[0]
                            vp['destination'][idx]['customer_name'] = customer['name']
                            vp['destination'][idx]['customer_email'] = customer['email']
                            vp['destination'][idx]['phone'] = customer['phone']
                            vp['destination'][idx]['address'] = customer['address']
                            vp['destination'][idx]['lng'] = customer['lng']
                            vp['destination'][idx]['lat'] = customer['lat']
                            vp['destination'][idx]['nfcid'] = customer['nfcid']
                            if customer['contacts'] is not None:
                                vp['destination'][idx]['contacts'] = json.loads(customer['contacts'])
                            else:
                                vp['destination'][idx]['contacts'] = None
                            if customer['business_activity'] is not None:
                                vp['destination'][idx]['business_activity'] = json.loads(customer['business_activity'])
                            else:
                                vp['destination'][idx]['business_activity'] = None
                            try:
                                summary = self.visit_plan_summary_model.get_visit_plan_summary_by_plan_id_customer_code(
                                    self.cursor, vp['id'], rec['customer_code']
                                )
                                if len(summary) == 0:
                                    vp['destination'][idx]['summary'] = None
                                else:
                                    summary = summary[0]
                                    del summary['visit_images']
                                    del summary['competitor_images']
                                    if summary['create_date'] is not None:
                                        summary['create_date'] = str(summary['create_date'])
                                    if summary['update_date'] is not None:
                                        summary['update_date'] = str(summary['update_date'])
                                    vp['destination'][idx]['summary'] = summary
                            except:
                                vp['destination'][idx]['summary'] = None
                        except:
                            vp['destination'][idx]['customer_name'] = None
                            vp['destination'][idx]['customer_email'] = None
                            vp['destination'][idx]['phone'] = None
                            vp['destination'][idx]['address'] = None
                            vp['destination'][idx]['lng'] = None
                            vp['destination'][idx]['lat'] = None
                            vp['destination'][idx]['nfcid'] = None
                            vp['destination'][idx]['contacts'] = None
                            vp['destination'][idx]['business_activity'] = None
                            vp['destination'][idx]['summary'] = None
                        list_customer.append(rec['customer_code'])
                        idx += 1
                if vp['destination_new'] is not None:
                    vp['destination_new'] = json.loads(vp['destination_new'])
                    idx = 0
                    for rec_new in vp['destination_new']:
                        try:
                            customer = self.customer_model.get_customer_by_id(
                                self.cursor, rec_new['customer_code'],
                                select="name, email, phone, address, lng, lat, nfcid, contacts, business_activity")[0]
                            vp['destination_new'][idx]['customer_name'] = customer['name']
                            vp['destination_new'][idx]['customer_email'] = customer['email']
                            vp['destination_new'][idx]['phone'] = customer['phone']
                            vp['destination_new'][idx]['address'] = customer['address']
                            vp['destination_new'][idx]['lng'] = customer['lng']
                            vp['destination_new'][idx]['lat'] = customer['lat']
                            vp['destination_new'][idx]['nfcid'] = customer['nfcid']
                            if customer['contacts'] is not None:
                                vp['destination_new'][idx]['contacts'] = json.loads(customer['contacts'])
                            else:
                                vp['destination_new'][idx]['contacts'] = None
                            if customer['business_activity'] is not None:
                                vp['destination_new'][idx]['business_activity'] = json.loads(
                                    customer['business_activity'])
                            else:
                                vp['destination_new'][idx]['business_activity'] = None
                            try:
                                summary = self.visit_plan_summary_model.get_visit_plan_summary_by_plan_id_customer_code(
                                    self.cursor, vp['id'], rec_new['customer_code']
                                )
                                if len(summary) == 0:
                                    vp['destination_new'][idx]['summary'] = None
                                else:
                                    summary = summary[0]
                                    del summary['visit_images']
                                    del summary['competitor_images']
                                    if summary['create_date'] is not None:
                                        summary['create_date'] = str(summary['create_date'])
                                    if summary['update_date'] is not None:
                                        summary['update_date'] = str(summary['update_date'])
                                    vp['destination_new'][idx]['summary'] = summary
                            except:
                                vp['destination_new'][idx]['summary'] = None
                        except:
                            vp['destination_new'][idx]['customer_name'] = None
                            vp['destination_new'][idx]['customer_email'] = None
                            vp['destination_new'][idx]['phone'] = None
                            vp['destination_new'][idx]['address'] = None
                            vp['destination_new'][idx]['lng'] = None
                            vp['destination_new'][idx]['lat'] = None
                            vp['destination_new'][idx]['nfcid'] = None
                            vp['destination_new'][idx]['contacts'] = None
                            vp['destination_new'][idx]['business_activity'] = None
                            vp['destination_new'][idx]['summary'] = None
                        list_customer.append(rec_new['customer_code'])
                        idx += 1
                # vc['customer'] = list_customer
                vp['total_customer'] = len(set(list_customer))
                if vp['user_id'] is not None:
                    try:
                        vp['user'] = self.user_model.get_user_by_id(
                            self.cursor, vp['user_id'], select="username, employee_id, branch_id, division_id")[0]
                    except:
                        vp['user'] = {}
                    if vp['user']['employee_id'] is not None:
                        try:
                            vp['user']['name'] = self.employee_model.get_employee_by_id(
                                self.cursor, vp['user']['employee_id'], select="""name""")[0]['name']
                        except:
                            vp['user']['name'] = None
                    if vp['user']['branch_id'] is not None:
                        try:
                            vp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, vp['user']['branch_id'], select="""name""")[0]['name']
                        except:
                            vp['user']['branch_name'] = None
                    if vp['user']['division_id'] is not None:
                        try:
                            vp['user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, vp['user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            vp['user']['division_name'] = None
                    else:
                        vp['user']['division_name'] = None
                else:
                    vp['user'] = {}
                if vp['start_route_branch_id'] is not None:
                    try:
                        vp['start_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, vp['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        vp['start_route_branch'] = {}
                else:
                    vp['start_route_branch'] = {}
                if vp['end_route_branch_id'] is not None:
                    try:
                        vp['end_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, vp['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        vp['end_route_branch'] = {}
                else:
                    vp['end_route_branch'] = {}
                del vp['route']

                data.append(vp)
        output = BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Data Visit Plan')
        merge_format = workbook.add_format(
            {
                'bold': 1,
                'border': 0,
                'align': 'left',
                'valign': 'vcenter'
            }
        )
        merge_format_start_end = workbook.add_format(
            {
                'bold': 1,
                'border': 0,
                'align': 'left',
                'valign': 'vcenter',
                'bg_color': '#99ff66'
            }
        )
        header_format = workbook.add_format(
            {
                'bold': 1,
                'border': 0,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#bababa'
            }
        )
        highlight_format = workbook.add_format(
            {
                'bold': 0,
                'border': 0,
                'align': 'left',
                'valign': 'vcenter',
                'bg_color': '#f1f1f1'
            }
        )
        # Header sheet
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date'] and not data_filter['user_id']:
                worksheet.merge_range(
                    'A1:N1',
                    'VISIT PLAN (USER: ALL, TANGGAL: {0} s/d {1})'.format(
                        datetime.strptime(data_filter['start_date'], "%Y-%m-%d").strftime("%d-%m-%Y"),
                        datetime.strptime(data_filter['end_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                    ),
                    merge_format
                )
            elif data_filter['user_id'] and not data_filter['start_date']:
                worksheet.merge_range(
                    'A1:N1',
                    'VISIT PLAN (USER: {0}, TANGGAL: ALL)'.format(", ".join(x for x in data_filter['username'])),
                    merge_format
                )
            else:
                worksheet.merge_range(
                    'A1:N1',
                    'VISIT PLAN (USER: {0}, TANGGAL: {1} s/d {2})'.format(
                        ", ".join(x for x in data_filter['username']),
                        datetime.strptime(data_filter['start_date'], "%Y-%m-%d").strftime("%d-%m-%Y"),
                        datetime.strptime(data_filter['end_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                    ),
                    merge_format
                )
        else:
            worksheet.merge_range('A1:N1', 'VISIT PLAN (USER: ALL, TANGGAL: ALL)', merge_format)

        worksheet.write('A3', 'TANGGAL', header_format)
        worksheet.write('B3', 'SALES REP', header_format)
        worksheet.write('C3', 'BRANCH', header_format)
        worksheet.write('D3', 'DIVISION', header_format)
        worksheet.write('E3', 'BREAK TIME (Minutes)', header_format)
        worksheet.write('F3', 'VISITED', header_format)
        worksheet.write('G3', 'VISIT TIME (Minutes)', header_format)
        worksheet.write('H3', 'DRIVING TIME (Minutes)', header_format)
        worksheet.write('I3', 'PLAN', header_format)
        worksheet.write('J3', 'NEW', header_format)
        worksheet.write('K3', 'ALERT', header_format)
        worksheet.write('L3', 'PERMISSION', header_format)
        worksheet.write('M3', 'CANCEL', header_format)
        worksheet.write('N3', 'INVOICE', header_format)
        data_rows = 3
        for rec in data:
            # actual = len(rec['data_activity']) - 1
            # if actual < 0:
            #     actual = 0
            worksheet.write(data_rows, 0,
                            datetime.strptime(rec['date'], "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M:%S"),
                            highlight_format)
            worksheet.write(data_rows, 1, rec['user']['name'], highlight_format)
            worksheet.write(data_rows, 2, rec['user']['branch_name'], highlight_format)
            worksheet.write(data_rows, 3, rec['user']['division_name'], highlight_format)
            if len(rec['data_performance']) != 0:
                worksheet.write(data_rows, 4, rec['data_performance']['break_time'], highlight_format)
                worksheet.write(data_rows, 5, rec['data_performance']['visited'], highlight_format)
                worksheet.write(data_rows, 6, rec['data_performance']['visit_time'], highlight_format)
                worksheet.write(data_rows, 7, rec['data_performance']['driving_time'], highlight_format)
                worksheet.write(data_rows, 8, rec['data_performance']['plan'], highlight_format)
                worksheet.write(data_rows, 9, rec['data_performance']['new'], highlight_format)
                worksheet.write(data_rows, 10, rec['data_performance']['alert'], highlight_format)
                worksheet.write(data_rows, 11, rec['data_performance']['permission'], highlight_format)
                worksheet.write(data_rows, 12, rec['data_performance']['cancel'], highlight_format)
                worksheet.write(data_rows, 13, rec['data_performance']['invoice'], highlight_format)
            else:
                worksheet.write(data_rows, 4, 0, highlight_format)
                worksheet.write(data_rows, 5, 0, highlight_format)
                worksheet.write(data_rows, 6, 0, highlight_format)
                worksheet.write(data_rows, 7, 0, highlight_format)
                worksheet.write(data_rows, 8, 0, highlight_format)
                worksheet.write(data_rows, 9, 0, highlight_format)
                worksheet.write(data_rows, 10, 0, highlight_format)
                worksheet.write(data_rows, 11, 0, highlight_format)
                worksheet.write(data_rows, 12, 0, highlight_format)
                worksheet.write(data_rows, 13, 0, highlight_format)
            data_rows += 1
            if rec['plan_activity']:
                for pa in rec['plan_activity']:
                    if pa.get('start_time'):
                        worksheet.merge_range(
                            'A{0}:B{0}'.format(data_rows + 1),
                            "START: {0}".format(
                                pa['location_name'] if pa['location_name'] else "Other Location"
                            ),
                            merge_format_start_end
                        )
                        worksheet.merge_range(
                            'C{0}:J{0}'.format(data_rows + 1),
                            pa['location_address'] if pa['location_address'] else "",
                            merge_format_start_end
                        )
                        worksheet.merge_range(
                            'K{0}:N{0}'.format(data_rows + 1),
                            "TIME: {0}".format(
                                datetime.strptime(pa['start_time'], "%Y-%m-%d %H:%M:%S").strftime(
                                    "%d-%m-%Y %H:%M:%S") if pa['start_time'] else ""
                            ),
                            merge_format_start_end
                        )
            else:
                worksheet.merge_range(
                    'A{0}:B{0}'.format(data_rows + 1),
                    "START: {0}".format(
                        rec['start_route_branch']['name'] if rec['start_route_branch'].get('name') else ""
                    ),
                    merge_format_start_end
                )
                worksheet.merge_range(
                    'C{0}:J{0}'.format(data_rows + 1),
                    rec['start_route_branch']['address'] if rec['start_route_branch'].get('address') else "",
                    merge_format_start_end
                )
                worksheet.merge_range(
                    'K{0}:N{0}'.format(data_rows + 1),
                    "TIME: ",
                    merge_format_start_end
                )
            data_rows += 1
            if rec['destination'] or rec['destination_new']:
                # Title
                worksheet.merge_range('A{0}:B{0}'.format(data_rows + 1), "Customer Code", merge_format)
                worksheet.merge_range('C{0}:D{0}'.format(data_rows + 1), "Customer Name", merge_format)
                worksheet.merge_range('E{0}:H{0}'.format(data_rows + 1), "Address", merge_format)
                worksheet.merge_range('I{0}:J{0}'.format(data_rows + 1), "Check IN", merge_format)
                worksheet.merge_range('K{0}:L{0}'.format(data_rows + 1), "Check OUT", merge_format)
                worksheet.merge_range('M{0}:N{0}'.format(data_rows + 1), "Summary", merge_format)
                data_rows += 1
                if rec['destination']:
                    for data_rec in rec['destination']:
                        address = []
                        # Body
                        worksheet.merge_range('A{0}:B{0}'.format(data_rows + 1), data_rec['customer_code'])
                        worksheet.merge_range('C{0}:D{0}'.format(data_rows + 1), data_rec['customer_name'])
                        address.append(data_rec['address'])
                        if data_rec['summary']:
                            if data_rec['summary'].get('notes'):
                                worksheet.merge_range('M{0}:N{0}'.format(data_rows + 1), data_rec['summary']['notes'])
                            else:
                                worksheet.merge_range('M{0}:N{0}'.format(data_rows + 1), "")
                        else:
                            worksheet.merge_range('M{0}:N{0}'.format(data_rows + 1), "")
                        # if rec['data_activity'].get(data_rec['customer_code']):
                        #     if rec['data_activity'][data_rec['customer_code']].get("in_time"):
                        #         worksheet.merge_range('H{0}:I{0}'.format(data_rows+1), rec['data_activity'][data_rec['customer_code']]["in_time"])
                        #     else:
                        #         worksheet.merge_range('H{0}:I{0}'.format(data_rows+1), "")
                        #     if rec['data_activity'][data_rec['customer_code']].get("out_time"):
                        #         worksheet.merge_range('J{0}:K{0}'.format(data_rows+1), rec['data_activity'][data_rec['customer_code']]["out_time"])
                        #     else:
                        #         worksheet.merge_range('J{0}:K{0}'.format(data_rows+1), "")
                        # else:
                        #     worksheet.merge_range('H{0}:I{0}'.format(data_rows+1), "")
                        #     worksheet.merge_range('J{0}:K{0}'.format(data_rows+1), "")
                        if rec['plan_activity']:
                            in_time_list = []
                            out_time_list = []
                            for pa in rec['plan_activity']:
                                if pa['nfc_code'] == data_rec['customer_code']:
                                    # print(pa)
                                    if pa['in_time']:
                                        in_time_list.append(pa['in_time'])
                                    if pa['out_time']:
                                        out_time_list.append(pa['out_time'])
                                    if pa['in_location_custom']:
                                        address.append(pa['in_location_name'])
                                    if pa['out_location_custom']:
                                        address.append(pa['out_location_name'])
                            worksheet.merge_range('I{0}:J{0}'.format(data_rows + 1),
                                                  ", ".join([(datetime.strptime(x, "%Y-%m-%d %H:%M:%S").strftime(
                                                      "%d-%m-%Y %H:%M:%S") if x is not None else "") for x in
                                                             in_time_list]))
                            worksheet.merge_range('K{0}:L{0}'.format(data_rows + 1),
                                                  ", ".join([(datetime.strptime(x, "%Y-%m-%d %H:%M:%S").strftime(
                                                      "%d-%m-%Y %H:%M:%S") if x is not None else "") for x in
                                                             out_time_list]))
                        else:
                            worksheet.merge_range('I{0}:J{0}'.format(data_rows + 1), "")
                            worksheet.merge_range('K{0}:L{0}'.format(data_rows + 1), "")
                        # print(address)
                        worksheet.merge_range('E{0}:H{0}'.format(data_rows + 1),
                                              " | ".join([(x if x is not None else "") for x in address]))
                        data_rows += 1
                if rec['destination_new']:
                    for data_rec_new in rec['destination_new']:
                        address_new = []
                        # Body
                        worksheet.merge_range('A{0}:B{0}'.format(data_rows + 1), data_rec_new['customer_code'])
                        worksheet.merge_range('C{0}:D{0}'.format(data_rows + 1), data_rec_new['customer_name'])
                        address_new.append(data_rec_new['address'])
                        if data_rec_new['summary']:
                            if data_rec_new['summary'].get('notes'):
                                worksheet.merge_range('M{0}:N{0}'.format(data_rows + 1),
                                                      data_rec_new['summary']['notes'])
                            else:
                                worksheet.merge_range('M{0}:N{0}'.format(data_rows + 1), "")
                        else:
                            worksheet.merge_range('M{0}:N{0}'.format(data_rows + 1), "")
                        if rec['plan_activity']:
                            in_time_list = []
                            out_time_list = []
                            for pa_new in rec['plan_activity']:
                                if pa_new['nfc_code'] == data_rec_new['customer_code']:
                                    # print("DEBUG LOC")
                                    # print(pa_new)
                                    if pa_new['in_time']:
                                        in_time_list.append(pa_new['in_time'])
                                    if pa_new['out_time']:
                                        out_time_list.append(pa_new['out_time'])
                                    if pa_new['in_location_custom']:
                                        address_new.append(pa_new['in_location_address'])
                                    if pa_new['out_location_custom']:
                                        address_new.append(pa_new['out_location_address'])
                            worksheet.merge_range('I{0}:J{0}'.format(data_rows + 1),
                                                  ", ".join([(datetime.strptime(x, "%Y-%m-%d %H:%M:%S").strftime(
                                                      "%d-%m-%Y %H:%M:%S") if x is not None else "") for x in
                                                             in_time_list]))
                            worksheet.merge_range('K{0}:L{0}'.format(data_rows + 1),
                                                  ", ".join([(datetime.strptime(x, "%Y-%m-%d %H:%M:%S").strftime(
                                                      "%d-%m-%Y %H:%M:%S") if x is not None else "") for x in
                                                             out_time_list]))
                        else:
                            worksheet.merge_range('I{0}:J{0}'.format(data_rows + 1), "")
                            worksheet.merge_range('K{0}:L{0}'.format(data_rows + 1), "")
                        # print(address_new)
                        worksheet.merge_range('E{0}:H{0}'.format(data_rows + 1),
                                              " | ".join([(x if x is not None else "") for x in address_new]))

                        data_rows += 1

            if rec['plan_activity']:
                for pa in rec['plan_activity']:
                    if pa.get('stop_time'):
                        worksheet.merge_range(
                            'A{0}:B{0}'.format(data_rows + 1),
                            "END: {0}".format(
                                pa['location_name'] if pa['location_name'] else "Other Location"
                            ),
                            merge_format_start_end
                        )
                        worksheet.merge_range(
                            'C{0}:J{0}'.format(data_rows + 1),
                            pa['location_address'] if pa['location_address'] else "",
                            merge_format_start_end
                        )
                        worksheet.merge_range(
                            'K{0}:N{0}'.format(data_rows + 1),
                            "TIME: {0}".format(
                                datetime.strptime(pa['stop_time'], "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M:%S") if
                                pa['stop_time'] else ""
                            ),
                            merge_format_start_end
                        )
            else:
                worksheet.merge_range(
                    'A{0}:B{0}'.format(data_rows + 1),
                    "END: {0}".format(
                        rec['end_route_branch']['name'] if rec['end_route_branch'].get('name') else ""
                    ),
                    merge_format_start_end
                )
                worksheet.merge_range(
                    'C{0}:J{0}'.format(data_rows + 1),
                    rec['end_route_branch']['address'] if rec['end_route_branch'].get('address') else "",
                    merge_format_start_end
                )
                worksheet.merge_range(
                    'K{0}:N{0}'.format(data_rows + 1),
                    "TIME: ",
                    merge_format_start_end
                )
            data_rows += 1
        workbook.close()
        output.seek(0)

        result_data['data'] = data
        result_data['file'] = output

        return result_data

    def get_all_export_pdf_activity_data_by_visit_plan(
            self, page: int, limit: int, search: str, column: str, direction: str,
            branch_privilege: list, division_privilege: list, data_filter: list
    ):
        """
        Get List Of visit cycle
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: branch_privilige: list
        :param: division_privilige: list
        :return:
            Visit Cycle Object
        """
        result_data = {}
        cycle = {}
        data = []
        start = page * limit - limit
        order = ''
        where = """WHERE (vp.is_approval = 1 AND vp.is_deleted = 0) 
        AND (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        where_original = where
        if column:
            if column == 'start_branch':
                order = """ORDER BY b1.name {0}""".format(direction)
            elif column == 'end_branch':
                order = """ORDER BY b2.name {0}""".format(direction)
            elif column == 'username':
                order = """ORDER BY u.username {0}""".format(direction)
            elif column == 'user':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY br.name {0}""".format(direction)
            elif column == 'division':
                order = """ORDER BY dv.division_name {0}""".format(direction)
            elif column == 'date':
                order = """ORDER BY vp.{0} {1}, vp.create_date {1}""".format(column, direction)
            else:
                order = """ORDER BY vp.{0} {1}""".format(column, direction)
        select = "vp.*"
        select_count = "vp.id"
        join = """as vp LEFT JOIN `users` as u ON vp.user_id = u.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id
        LEFT JOIN `branches` as br ON u.branch_id = br.id
        LEFT JOIN `divisions` as dv ON u.division_id = dv.id
        LEFT JOIN `branches` as b1 ON vp.start_route_branch_id = b1.id
        LEFT JOIN `branches` as b2 ON vp.end_route_branch_id = b2.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR br.name LIKE '%{0}%' OR dv.division_name LIKE '%{0}%' 
            OR b1.name LIKE '%{0}%' OR b2.name LIKE '%{0}%' OR e.name LIKE '%{0}%') """.format(search)
        if data_filter:
            tmp_data_filter = data_filter[0]
            if tmp_data_filter['start_date']:
                where += """AND (vp.date >= '{0} 00:00:00' AND vp.date <= '{1} 23:59:59') """.format(
                    tmp_data_filter['start_date'], tmp_data_filter['end_date']
                )
            if tmp_data_filter['user_id']:
                where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['user_id']))
            if tmp_data_filter['branch_id']:
                where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['branch_id']))
            if tmp_data_filter['division_id']:
                where += """AND u.division_id IN ({0}) """.format(
                    ", ".join(str(x) for x in tmp_data_filter['division_id']))

        visit_plan_data = self.visit_plan_model.get_all_visit_plan(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        # count_filter = self.visit_plan_model.get_count_all_visit_plan(
        #     self.cursor, select=select_count, join=join, where=where
        # )
        # count = self.visit_plan_model.get_count_all_visit_plan(
        #     self.cursor, select=select_count, join=join, where=where_original
        # )
        if visit_plan_data:
            for vp in visit_plan_data:
                list_customer = []
                if vp['edit_data'] is not None:
                    vp['edit_data'] = json.loads(vp['edit_data'])
                if vp['date'] is not None:
                    vp['date'] = str(vp['date'])
                if vp['create_date'] is not None:
                    vp['create_date'] = str(vp['create_date'])
                if vp['update_date'] is not None:
                    vp['update_date'] = str(vp['update_date'])

                # Get Activity data
                data_activity_dict = dict()
                data_activity = []
                list_nfc_code = []

                plan_activity = []
                try:
                    # where = """WHERE (sa.id IN (SELECT MIN(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'START'
                    # GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MAX(id) FROM `sales_activity`
                    # WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, visit_plan_id, nfc_code) OR sa.id IN (SELECT MIN(id)
                    # FROM `sales_activity` WHERE `tap_nfc_type` = 'IN' GROUP BY user_id, visit_plan_id, nfc_code)
                    # OR sa.id IN (SELECT MAX(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'OUT'
                    # GROUP BY user_id, visit_plan_id, nfc_code)) AND (visit_plan_id = {0}) """.format(vp['id'])

                    # query without grouping
                    where = """ WHERE (
                            sa.id IN (SELECT MIN(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'START' GROUP BY user_id, visit_plan_id, nfc_code) OR
                            sa.id IN (SELECT MAX(id) FROM `sales_activity` WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, visit_plan_id, nfc_code) OR
                            sa.id IN (SELECT id FROM `sales_activity` WHERE `tap_nfc_type` = 'IN' ) OR
                            sa.id IN (SELECT id FROM `sales_activity` WHERE `tap_nfc_type` = 'OUT')
                        ) AND (visit_plan_id = {0}) """.format(vp['id'])
                    order = ""
                    select = "sa.*"
                    join = """AS sa"""
                    activity_data = self.sales_activity_model.get_all_activity(
                        self.cursor, select=select, join=join, where=where, order=order, start=0, limit=1000
                    )

                    # Process data for Plan Activity key-> plan_activity
                    if activity_data:
                        for ad in activity_data:
                            if ad['tap_nfc_date'] is not None:
                                ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                            if ad['create_date'] is not None:
                                ad['create_date'] = str(ad['create_date'])
                            if ad['update_date'] is not None:
                                ad['update_date'] = str(ad['update_date'])

                            ad['branch_name'] = None
                            ad['branch_location'] = None
                            if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                                if ad['nfc_code'] is not None:
                                    try:
                                        branch = self.branch_model.get_branches_by_id(self.cursor, ad['nfc_code'])[0]
                                        ad['branch_name'] = branch['name']
                                        ad['branch_location'] = branch['address']
                                    except:
                                        ad['branch_name'] = None
                                        ad['branch_location'] = None
                                if ad['route_breadcrumb'] is not None:
                                    ad['route_breadcrumb'] = json.loads(ad['route_breadcrumb'])

                            ad['customer_code'] = None
                            ad['customer_name'] = None
                            ad['customer_address'] = None
                            if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                                if ad['nfc_code'] is not None:
                                    ad['customer_code'] = ad['nfc_code']
                                    try:
                                        customer = \
                                            self.customer_model.get_customer_by_code(self.cursor, ad['nfc_code'])[0]
                                        ad['customer_name'] = customer['name']
                                        ad['customer_address'] = customer['address']
                                    except:
                                        ad['customer_name'] = None
                                        ad['customer_address'] = None
                                if ad['route_breadcrumb'] is not None:
                                    ad['route_breadcrumb'] = json.loads(ad['route_breadcrumb'])

                            if ad['user_id'] is not None:
                                try:
                                    ad['user'] = self.user_model.get_user_by_id(
                                        self.cursor, ad['user_id'],
                                        select="username, employee_id, branch_id, division_id"
                                    )[0]
                                    if ad['user']['employee_id'] is not None:
                                        try:
                                            ad['user']['name'] = self.employee_model.get_employee_by_id(
                                                self.cursor,
                                                ad['user']['employee_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['name'] = None
                                    if ad['user']['branch_id'] is not None:
                                        try:
                                            ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                self.cursor,
                                                ad['user']['branch_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['branch_name'] = None
                                    if ad['user']['division_id'] is not None:
                                        try:
                                            ad['user']['division_name'] = self.division_model.get_division_by_id(
                                                self.cursor, ad['user']['division_id'], select="division_name")[0][
                                                'division_name']
                                        except:
                                            ad['user']['division_name'] = None
                                except:
                                    ad['user'] = {}
                            else:
                                ad['user'] = {}

                            plan_activity.append(ad)

                    if plan_activity:
                        plan_activity_list = []
                        for rec in plan_activity:
                            plan_activity_dict = dict()
                            # print("======== Plan Activity {0}".format(rec))
                            if rec['tap_nfc_type'] == 'START':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = 0
                                plan_activity_dict['start_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['start_location_custom'] = False
                                    plan_activity_dict['start_location_name'] = rec['branch_name']
                                    plan_activity_dict['start_location_address'] = rec['branch_location']
                                else:
                                    # custom start
                                    plan_activity_dict['start_location_custom'] = True
                                    plan_activity_dict['start_location_name'] = None
                                    plan_activity_dict['start_location_address'] = rec['route_breadcrumb']['address']
                                plan_activity_dict['start_location'] = rec['route_breadcrumb']

                            if rec['tap_nfc_type'] == 'STOP':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = 0
                                plan_activity_dict['stop_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['stop_location_custom'] = False
                                    plan_activity_dict['stop_location_name'] = rec['branch_name']
                                    plan_activity_dict['stop_location_address'] = rec['branch_location']
                                else:
                                    # custom stop
                                    plan_activity_dict['stop_location_custom'] = True
                                    plan_activity_dict['stop_location_name'] = None
                                    plan_activity_dict['stop_location_address'] = rec['route_breadcrumb']['address']
                                plan_activity_dict['stop_location'] = rec['route_breadcrumb']

                            if rec['tap_nfc_type'] == 'IN':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = rec['distance']
                                plan_activity_dict['in_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['in_location_custom'] = False
                                    plan_activity_dict['in_location_name'] = rec['customer_name']
                                    plan_activity_dict['in_location_address'] = rec['customer_address']
                                else:
                                    # custom checkin
                                    plan_activity_dict['in_location_custom'] = True
                                    plan_activity_dict['in_location_name'] = rec['customer_name']
                                    plan_activity_dict['in_location_address'] = rec['route_breadcrumb']['address']

                            if rec['tap_nfc_type'] == 'OUT':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['out_time'] = rec['tap_nfc_date']

                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['out_location_custom'] = False
                                    plan_activity_dict['out_location_name'] = rec['customer_name']
                                    plan_activity_dict['out_location_address'] = rec['customer_address']
                                else:
                                    # custom checkout
                                    plan_activity_dict['out_location_custom'] = True
                                    plan_activity_dict['out_location_name'] = rec['customer_name']
                                    plan_activity_dict['out_location_address'] = rec['route_breadcrumb']['address']

                            plan_activity_list.append(plan_activity_dict)
                        plan_result = []
                        i = 0
                        for plan in plan_activity_list:
                            data_dict = dict()
                            if plan.get('start_time'):
                                data_dict['nfc_code'] = plan['nfc_code']
                                data_dict['start_time'] = plan['start_time']
                                data_dict['location_name'] = plan['start_location_name']
                                data_dict['location_address'] = plan['start_location_address']
                                data_dict['location_custom'] = plan['start_location_custom']
                                data_dict['distance'] = plan['distance']
                                data_dict['duration'] = 0

                            if plan.get('in_time'):
                                code = plan['nfc_code']
                                data_dict['nfc_code'] = code
                                data_dict['in_time'] = plan['in_time']
                                data_dict['distance'] = plan['distance']
                                data_dict['in_location_address'] = plan['in_location_address']
                                data_dict['in_location_name'] = plan['in_location_name']
                                data_dict['in_location_custom'] = plan['in_location_custom']
                                next_idx = i
                                next = next_idx + 1
                                if plan_activity_list[next]['nfc_code'] == code and plan_activity_list[next][
                                    'tap_nfc_type'] == 'OUT':
                                    # Tap Type STOP found
                                    data_dict['out_time'] = plan_activity_list[next]['out_time']
                                    data_dict['out_location_address'] = plan_activity_list[next]['out_location_address']
                                    data_dict['out_location_name'] = plan_activity_list[next]['out_location_name']
                                    data_dict['out_location_custom'] = plan_activity_list[next]['out_location_custom']

                                    # calculate duration
                                    out_time = datetime.strptime(data_dict['out_time'], "%Y-%m-%d %H:%M:%S")
                                    in_time = datetime.strptime(data_dict['in_time'], "%Y-%m-%d %H:%M:%S")
                                    if out_time > in_time:
                                        data_dict['duration'] = int((out_time - in_time).seconds / 60)
                                    else:
                                        data_dict['duration'] = 0
                                else:
                                    data_dict['out_time'] = None
                                    data_dict['out_location_address'] = None
                                    data_dict['out_location_name'] = None
                                    data_dict['out_location_custom'] = False
                                    data_dict['duration'] = 0

                            if plan.get('stop_time'):
                                data_dict['nfc_code'] = plan['nfc_code']
                                data_dict['stop_time'] = plan['stop_time']
                                data_dict['location_name'] = plan['stop_location_name']
                                data_dict['location_address'] = plan['stop_location_address']
                                data_dict['location_custom'] = plan['stop_location_custom']
                                data_dict['distance'] = plan['distance']
                                data_dict['duration'] = 0

                            if data_dict:
                                plan_result.append(data_dict)
                            i += 1

                        # calculate time range between activity
                        # and add key order
                        position = 0
                        if plan_result:
                            for plan in plan_result:
                                plan['order'] = position
                                if plan.get('start_time') and position == 0:
                                    plan['time_range'] = 0
                                else:
                                    if plan.get('in_time'):
                                        next_time = plan['in_time']
                                    elif plan.get('stop_time'):
                                        next_time = plan['stop_time']
                                    else:
                                        next_time = 0

                                    post = position
                                    index = post - 1
                                    if index >= 0:
                                        if plan_result[index].get('start_time'):
                                            prev_time = plan_result[index]['start_time']
                                        elif plan_result[index].get('out_time'):
                                            prev_time = plan_result[index]['out_time']
                                        else:
                                            prev_time = 0
                                    else:
                                        prev_time = 0

                                    if prev_time and next_time:
                                        prev_time_fmt = datetime.strptime(prev_time, "%Y-%m-%d %H:%M:%S")
                                        next_time_fmt = datetime.strptime(next_time, "%Y-%m-%d %H:%M:%S")
                                        if next_time_fmt > prev_time_fmt:
                                            plan['time_range'] = int((next_time_fmt - prev_time_fmt).seconds / 60)
                                        else:
                                            plan['time_range'] = 0
                                    else:
                                        plan['time_range'] = 0
                                position += 1
                            # print("result Plan Activity = {0}".format(plan_result))
                        vp['plan_activity'] = plan_result
                    else:
                        vp['plan_activity'] = []

                    # Process data for data Activity key-> data_activity
                    # previous process before ignore grouping
                    if activity_data:
                        for ad in activity_data:
                            if ad['tap_nfc_date'] is not None:
                                ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                            if ad['create_date'] is not None:
                                ad['create_date'] = str(ad['create_date'])
                            if ad['update_date'] is not None:
                                ad['update_date'] = str(ad['update_date'])
                            ad['branch_name'] = None
                            if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                                if ad['nfc_code'] is not None:
                                    try:
                                        ad['branch_name'] = self.branch_model.get_branches_by_id(
                                            self.cursor, ad['nfc_code'], select="""name"""
                                        )[0]['name']
                                    except:
                                        ad['branch_name'] = None
                                if ad['route_breadcrumb'] is not None:
                                    ad['route_breadcrumb'] = json.loads(json.dumps(ad['route_breadcrumb']))
                            ad['customer_code'] = None
                            if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                                if ad['nfc_code'] is not None:
                                    ad['customer_code'] = ad['nfc_code']
                            if ad['user_id'] is not None:
                                try:
                                    ad['user'] = self.user_model.get_user_by_id(
                                        self.cursor, ad['user_id'],
                                        select="username, employee_id, branch_id, division_id"
                                    )[0]
                                    if ad['user']['employee_id'] is not None:
                                        try:
                                            ad['user']['name'] = self.employee_model.get_employee_by_id(
                                                self.cursor,
                                                ad['user']['employee_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['name'] = None
                                    if ad['user']['branch_id'] is not None:
                                        try:
                                            ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                self.cursor,
                                                ad['user']['branch_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['branch_name'] = None
                                    if ad['user']['division_id'] is not None:
                                        try:
                                            ad['user']['division_name'] = self.division_model.get_division_by_id(
                                                self.cursor, ad['user']['division_id'], select="division_name")[0][
                                                'division_name']
                                        except:
                                            ad['user']['division_name'] = None
                                except:
                                    ad['user'] = {}
                            else:
                                ad['user'] = {}
                            if ad['nfc_code'] is not None:
                                data_activity_dict[ad['nfc_code']] = dict()
                                list_nfc_code.append(ad['nfc_code'])
                            data_activity.append(ad)
                    if data_activity:
                        for rec in data_activity:
                            if rec['tap_nfc_type'] == 'START':
                                data_activity_dict[rec['nfc_code']]['start_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = 0
                            if rec['tap_nfc_type'] == 'STOP':
                                data_activity_dict[rec['nfc_code']]['stop_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = 0
                            if rec['tap_nfc_type'] == 'IN':
                                data_activity_dict[rec['nfc_code']]['in_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = rec['distance']
                            if rec['tap_nfc_type'] == 'OUT':
                                data_activity_dict[rec['nfc_code']]['out_time'] = rec['tap_nfc_date']

                        # Calculation duration
                        unique_code = set(list_nfc_code)
                        for code in unique_code:
                            if data_activity_dict[code].get('in_time'):
                                in_time = data_activity_dict[code]['in_time']
                            else:
                                in_time = 0
                            if data_activity_dict[code].get('out_time'):
                                out_time = data_activity_dict[code]['out_time']
                            else:
                                out_time = 0
                            if in_time and out_time:
                                out_time_fmt = datetime.strptime(out_time, "%Y-%m-%d %H:%M:%S")
                                in_time_fmt = datetime.strptime(in_time, "%Y-%m-%d %H:%M:%S")
                                data_activity_dict[code]['duration'] = int((out_time_fmt - in_time_fmt).seconds / 60)
                            else:
                                data_activity_dict[code]['duration'] = 0

                    vp['data_activity'] = data_activity_dict
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print("Kesalahan {}".format(e), exc_type, fname, exc_tb.tb_lineno)
                    vp['data_activity'] = dict()
                    vp['plan_activity'] = []

                # Get Data Performance
                try:
                    performance_date = vp['date'].split(" ")
                    performance_date = performance_date[0]
                    data_performance = self.get_statistic_performance_by_user_id(
                        job_function='sales', user_ids=[vp['user_id']], start_date=performance_date,
                        end_date=performance_date, plan_id=vp['id']
                    )
                    # vp['data_performance'] = data_performance

                    # TODO Get Data Total Distance
                    select = "*"
                    where_distance = """WHERE user_id={0} AND tap_nfc_type='STOP' """.format(vp['user_id'])
                    where_distance += """AND visit_plan_id={} """.format(vp['id'])
                    where_distance += """AND (tap_nfc_date >= '{0} 00:00:00' AND tap_nfc_date <= '{1} 23:59:59') """.format(
                        performance_date, performance_date)
                    order = 'ORDER BY create_date ASC'
                    data_distance = self.sales_activity_model.get_all_activity(self.cursor, select=select,
                                                                               where=where_distance, order=order)
                    total_distance = 0
                    if data_distance:
                        for rec_distance in data_distance:
                            total_distance += rec_distance['total_distance']
                    data_performance['total_distance'] = total_distance

                    vp['data_performance'] = data_performance
                except Exception as e:
                    print(e)
                    vp['data_performance'] = dict()

                if vp['destination_order'] is not None:
                    vp['destination_order'] = json.loads(vp['destination_order'])
                if vp['destination'] is not None:
                    vp['destination'] = json.loads(vp['destination'])
                    idx = 0
                    for rec in vp['destination']:
                        try:
                            customer = self.customer_model.get_customer_by_id(
                                self.cursor, rec['customer_code'],
                                select="name, email, phone, address, lng, lat, nfcid, contacts, business_activity")[0]
                            vp['destination'][idx]['customer_name'] = customer['name']
                            vp['destination'][idx]['customer_email'] = customer['email']
                            vp['destination'][idx]['phone'] = customer['phone']
                            vp['destination'][idx]['address'] = customer['address']
                            vp['destination'][idx]['lng'] = customer['lng']
                            vp['destination'][idx]['lat'] = customer['lat']
                            vp['destination'][idx]['nfcid'] = customer['nfcid']
                            if customer['contacts'] is not None:
                                vp['destination'][idx]['contacts'] = json.loads(customer['contacts'])
                            else:
                                vp['destination'][idx]['contacts'] = None
                            if customer['business_activity'] is not None:
                                vp['destination'][idx]['business_activity'] = json.loads(customer['business_activity'])
                            else:
                                vp['destination'][idx]['business_activity'] = None
                            try:
                                summary = self.visit_plan_summary_model.get_visit_plan_summary_by_plan_id_customer_code(
                                    self.cursor, vp['id'], rec['customer_code']
                                )
                                if len(summary) == 0:
                                    vp['destination'][idx]['summary'] = None
                                else:
                                    summary = summary[0]
                                    del summary['visit_images']
                                    del summary['competitor_images']
                                    if summary['create_date'] is not None:
                                        summary['create_date'] = str(summary['create_date'])
                                    if summary['update_date'] is not None:
                                        summary['update_date'] = str(summary['update_date'])
                                    vp['destination'][idx]['summary'] = summary
                            except:
                                vp['destination'][idx]['summary'] = None
                        except:
                            vp['destination'][idx]['customer_name'] = None
                            vp['destination'][idx]['customer_email'] = None
                            vp['destination'][idx]['phone'] = None
                            vp['destination'][idx]['address'] = None
                            vp['destination'][idx]['lng'] = None
                            vp['destination'][idx]['lat'] = None
                            vp['destination'][idx]['nfcid'] = None
                            vp['destination'][idx]['contacts'] = None
                            vp['destination'][idx]['business_activity'] = None
                            vp['destination'][idx]['summary'] = None
                        list_customer.append(rec['customer_code'])
                        idx += 1
                if vp['destination_new'] is not None:
                    vp['destination_new'] = json.loads(vp['destination_new'])
                    idx = 0
                    for rec_new in vp['destination_new']:
                        try:
                            customer = self.customer_model.get_customer_by_id(
                                self.cursor, rec_new['customer_code'],
                                select="name, email, phone, address, lng, lat, nfcid, contacts, business_activity")[0]
                            vp['destination_new'][idx]['customer_name'] = customer['name']
                            vp['destination_new'][idx]['customer_email'] = customer['email']
                            vp['destination_new'][idx]['phone'] = customer['phone']
                            vp['destination_new'][idx]['address'] = customer['address']
                            vp['destination_new'][idx]['lng'] = customer['lng']
                            vp['destination_new'][idx]['lat'] = customer['lat']
                            vp['destination_new'][idx]['nfcid'] = customer['nfcid']
                            if customer['contacts'] is not None:
                                vp['destination_new'][idx]['contacts'] = json.loads(customer['contacts'])
                            else:
                                vp['destination_new'][idx]['contacts'] = None
                            if customer['business_activity'] is not None:
                                vp['destination_new'][idx]['business_activity'] = json.loads(
                                    customer['business_activity'])
                            else:
                                vp['destination_new'][idx]['business_activity'] = None
                            try:
                                summary = self.visit_plan_summary_model.get_visit_plan_summary_by_plan_id_customer_code(
                                    self.cursor, vp['id'], rec_new['customer_code']
                                )
                                if len(summary) == 0:
                                    vp['destination_new'][idx]['summary'] = None
                                else:
                                    summary = summary[0]
                                    del summary['visit_images']
                                    del summary['competitor_images']
                                    if summary['create_date'] is not None:
                                        summary['create_date'] = str(summary['create_date'])
                                    if summary['update_date'] is not None:
                                        summary['update_date'] = str(summary['update_date'])
                                    vp['destination_new'][idx]['summary'] = summary
                            except:
                                vp['destination_new'][idx]['summary'] = None
                        except:
                            vp['destination_new'][idx]['customer_name'] = None
                            vp['destination_new'][idx]['customer_email'] = None
                            vp['destination_new'][idx]['phone'] = None
                            vp['destination_new'][idx]['address'] = None
                            vp['destination_new'][idx]['lng'] = None
                            vp['destination_new'][idx]['lat'] = None
                            vp['destination_new'][idx]['nfcid'] = None
                            vp['destination_new'][idx]['contacts'] = None
                            vp['destination_new'][idx]['business_activity'] = None
                            vp['destination_new'][idx]['summary'] = None
                        list_customer.append(rec_new['customer_code'])
                        idx += 1
                # vc['customer'] = list_customer
                vp['total_customer'] = len(set(list_customer))
                if vp['user_id'] is not None:
                    try:
                        vp['user'] = self.user_model.get_user_by_id(
                            self.cursor, vp['user_id'], select="username, employee_id, branch_id, division_id")[0]
                    except:
                        vp['user'] = {}
                    if vp['user']['employee_id'] is not None:
                        try:
                            vp['user']['name'] = self.employee_model.get_employee_by_id(
                                self.cursor, vp['user']['employee_id'], select="""name""")[0]['name']
                        except:
                            vp['user']['name'] = None
                    if vp['user']['branch_id'] is not None:
                        try:
                            vp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, vp['user']['branch_id'], select="""name""")[0]['name']
                        except:
                            vp['user']['branch_name'] = None
                    if vp['user']['division_id'] is not None:
                        try:
                            vp['user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, vp['user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            vp['user']['division_name'] = None
                    else:
                        vp['user']['division_name'] = None
                else:
                    vp['user'] = {}
                if vp['start_route_branch_id'] is not None:
                    try:
                        vp['start_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, vp['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        vp['start_route_branch'] = {}
                else:
                    vp['start_route_branch'] = {}
                if vp['end_route_branch_id'] is not None:
                    try:
                        vp['end_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, vp['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        vp['end_route_branch'] = {}
                else:
                    vp['end_route_branch'] = {}
                del vp['route']

                data.append(vp)
        # output = BytesIO()
        # Header sheet
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date'] and not data_filter['user_id']:
                head_title = 'VISIT PLAN (USER: ALL, TANGGAL: {0} s/d {1})'.format(
                    datetime.strptime(data_filter['start_date'], "%Y-%m-%d").strftime("%d-%m-%Y"),
                    datetime.strptime(data_filter['end_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                )
            elif data_filter['user_id'] and not data_filter['start_date']:
                head_title = 'VISIT PLAN (USER: {0}, TANGGAL: ALL)'.format(
                    ", ".join(x for x in data_filter['username'])
                )
            else:
                head_title = 'VISIT PLAN (USER: {0}, TANGGAL: {1} s/d {2})'.format(
                    ", ".join(x for x in data_filter['username']),
                    datetime.strptime(data_filter['start_date'], "%Y-%m-%d").strftime("%d-%m-%Y"),
                    datetime.strptime(data_filter['end_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                )
        else:
            head_title = 'VISIT PLAN (USER: ALL, TANGGAL: ALL)'

        # head_table = OrderedDict()
        # head_table['tanggal'] = "TANGGAL"
        # head_table['sales'] = "SALES REP"
        # head_table['branch'] = "BRANCH"
        # head_table['division'] = "DIVISION"
        # head_table['break_time'] = "BREAK TIME (Minutes)"
        # head_table['visited'] = "VISITED"
        # head_table['visit_time'] = "VISIT TIME (Minutes)"
        # head_table['driving_time'] = "DRIVING TIME (Minutes)"
        # head_table['plan'] = "PLAN"
        # head_table['alert'] = "ALERT"
        # head_table['permission'] = "PERMISSION"
        # head_table['cancel'] = "CANCEL"
        # head_table['invoice'] = "INVOICE"
        # Title Customer
        # head_customer_table = OrderedDict()
        # head_customer_table['code'] = "Customer Code"
        # head_customer_table['name'] = "Customer Name"
        # head_customer_table['address'] = "Address"
        # head_customer_table['in'] = "Tap IN"
        # head_customer_table['out'] = "Tap OUT"
        body_table = []
        for rec in data:
            data_body = OrderedDict()
            data_body['tanggal'] = datetime.strptime(rec['date'], "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M:%S")
            data_body['sales'] = rec['user']['name']
            data_body['branch'] = rec['user']['branch_name']
            data_body['division'] = rec['user']['division_name']
            if len(rec['data_performance']) != 0:
                data_body['break_time'] = rec['data_performance']['break_time']
                data_body['visited'] = rec['data_performance']['visited']
                data_body['visit_time'] = rec['data_performance']['visit_time']
                data_body['driving_time'] = rec['data_performance']['driving_time']
                data_body['plan'] = rec['data_performance']['plan']
                data_body['new'] = rec['data_performance']['new']
                data_body['alert'] = rec['data_performance']['alert']
                data_body['permission'] = rec['data_performance']['permission']
                data_body['cancel'] = rec['data_performance']['cancel']
                data_body['invoice'] = rec['data_performance']['invoice']
            else:
                data_body['break_time'] = 0
                data_body['visited'] = 0
                data_body['visit_time'] = 0
                data_body['driving_time'] = 0
                data_body['plan'] = 0
                data_body['new'] = 0
                data_body['alert'] = 0
                data_body['permission'] = 0
                data_body['cancel'] = 0
                data_body['invoice'] = 0
            # Get start time in branch
            is_start_branch_exist = False
            if 'plan_activity' in rec:
                for pa in rec['plan_activity']:
                    if 'start_time' in pa:
                        data_body['start_branch'] = {
                            'code': rec['start_route_branch_id'],
                            'name': pa['location_name'] if pa['location_name'] else "Other Location",
                            'address': pa['location_address'] if pa['location_address'] else "",
                            'in': datetime.strptime(pa['start_time'], "%Y-%m-%d %H:%M:%S").strftime(
                                "%d-%m-%Y %H:%M:%S") if pa['start_time'] else "",
                            'out': ""
                        }
                        is_start_branch_exist = True

            if is_start_branch_exist is False:
                data_body['start_branch'] = {
                    'code': rec['start_route_branch_id'],
                    'name': rec['start_route_branch']['name'],
                    'address': rec['start_route_branch']['address'],
                    'in': "",
                    'out': ""
                }
            # Get stop time in branch
            is_end_branch_exist = False
            if rec['plan_activity']:
                for pa in rec['plan_activity']:
                    if 'stop_time' in pa:
                        data_body['end_branch'] = {
                            'code': rec['end_route_branch_id'],
                            'name': pa['location_name'] if pa['location_name'] else "Other Location",
                            'address': pa['location_address'] if pa['location_address'] else "",
                            'in': "",
                            'out': datetime.strptime(pa['stop_time'], "%Y-%m-%d %H:%M:%S").strftime(
                                "%d-%m-%Y %H:%M:%S") if pa['stop_time'] else ""
                        }
                        is_end_branch_exist = True
            if is_end_branch_exist is False:
                data_body['end_branch'] = {
                    'code': rec['end_route_branch_id'],
                    'name': rec['end_route_branch']['name'],
                    'address': rec['end_route_branch']['address'],
                    'in': "",
                    'out': ""
                }
            data_body['customer'] = []
            if rec['destination']:
                for data_rec in rec['destination']:
                    address = []
                    data_customer_body = OrderedDict()
                    # Body
                    data_customer_body['code'] = data_rec['customer_code']
                    data_customer_body['name'] = data_rec['customer_name']
                    address.append(data_rec['address'])
                    if data_rec['summary']:
                        if data_rec['summary'].get('notes'):
                            data_customer_body['summary'] = data_rec['summary']['notes']
                        else:
                            data_customer_body['summary'] = ""
                    else:
                        data_customer_body['summary'] = ""
                    in_time_list = []
                    out_time_list = []
                    if rec['plan_activity']:
                        for pa in rec['plan_activity']:
                            if pa['nfc_code'] == data_rec['customer_code']:
                                if 'in_time' in pa:
                                    in_time_list.append(pa['in_time'])
                                if 'out_time' in pa:
                                    out_time_list.append(pa['out_time'])
                                if 'in_location_custom' in pa:
                                    address.append(pa['in_location_name'])
                                if 'out_location_custom' in pa:
                                    address.append(pa['out_location_name'])
                    data_customer_body['address'] = " | ".join([(x if x is not None else "") for x in address])
                    data_customer_body['in'] = ", ".join([(datetime.strptime(x, "%Y-%m-%d %H:%M:%S").strftime(
                        "%d-%m-%Y %H:%M:%S") if x is not None else "") for x in in_time_list])
                    data_customer_body['out'] = ", ".join([(datetime.strptime(x, "%Y-%m-%d %H:%M:%S").strftime(
                        "%d-%m-%Y %H:%M:%S") if x is not None else "") for x in out_time_list])
                    data_body['customer'].append(data_customer_body)
            if rec['destination_new']:
                for data_rec_new in rec['destination_new']:
                    address = []
                    data_customer_body = OrderedDict()
                    # Body
                    data_customer_body['code'] = data_rec_new['customer_code']
                    address.append(data_rec_new['address'])
                    if data_rec_new['summary']:
                        if data_rec_new['summary'].get('notes'):
                            data_customer_body['summary'] = data_rec_new['summary']['notes']
                        else:
                            data_customer_body['summary'] = ""
                    else:
                        data_customer_body['summary'] = ""
                    in_time_list = []
                    out_time_list = []
                    if rec['plan_activity']:
                        for pa in rec['plan_activity']:
                            if pa['nfc_code'] == data_rec_new['customer_code']:
                                if 'in_time' in pa:
                                    in_time_list.append(pa['in_time'])
                                if 'out_time' in pa:
                                    out_time_list.append(pa['out_time'])
                                if 'in_location_custom' in pa:
                                    address.append(pa['in_location_name'])
                                if 'out_location_custom' in pa:
                                    address.append(pa['out_location_name'])
                    data_customer_body['address'] = " | ".join([(x if x is not None else "") for x in address])
                    data_customer_body['in'] = ", ".join([(datetime.strptime(x, "%Y-%m-%d %H:%M:%S").strftime(
                        "%d-%m-%Y %H:%M:%S") if x is not None else "") for x in in_time_list])
                    data_customer_body['out'] = ", ".join([(datetime.strptime(x, "%Y-%m-%d %H:%M:%S").strftime(
                        "%d-%m-%Y %H:%M:%S") if x is not None else "") for x in out_time_list])
                    data_body['customer'].append(data_customer_body)
            body_table.append(data_body)
        # rendered = render_template(
        #     'report_template.html', head_title=head_title, head_table=head_table,
        #     head_customer_table=head_customer_table, body_table=body_table, category="sales"
        # )
        rendered = render_template(
            'report_activity_template.html', head_title=head_title, body_table=body_table, category="sales"
        )
        output = pdfkit.from_string(rendered, False)
        # output.seek(0)

        result_data['data'] = data
        result_data['file'] = output

        return result_data

    def create_break_time(self, create_data: 'dict', user_id: 'int'):
        """
        Function for create new log activity

        :param create_data: dict
        :param user_id: int
        :return:
            Success or failure message
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.break_time_model.insert_into_db(
                self.cursor, user_id=user_id, visit_plan_id=create_data['visit_plan_id'],
                delivery_plan_id=create_data['delivery_plan_id'],
                break_time=create_data['break_time'], create_date=today, update_date=today
            )
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def create_idle_time(self, create_data: 'dict', user_id: 'int'):
        """
        Function for create new log activity

        :param create_data: dict
        :param user_id: int
        :return:
            Success or failure message
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.idle_time_model.insert_into_db(
                self.cursor, user_id=user_id, visit_plan_id=create_data['visit_plan_id'],
                delivery_plan_id=create_data['delivery_plan_id'],
                idle_time=create_data['idle_time'], create_date=today, update_date=today
            )
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def create_breadcrumb(self, create_data: 'dict', user_id: 'int'):
        """
        Function for create new log activity

        :param create_data: dict
        :param user_id: int
        :return:
            Success or failure message
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.sab_model.insert_into_db(
                self.cursor, user_id=user_id, visit_plan_id=create_data['visit_plan_id'],
                lat=create_data['lat'], lng=create_data['lng'], create_date=today, update_date=today
            )
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def get_all_breadcrumb_data(
            self, page: int, limit: int, search: str, column: str, direction: str, plan_id: int
    ):
        """
        Get List Of breadcrumb
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: plan_id: int
        :return:
            breadcrumb Object
        """
        cycle = {}
        data = []
        start = page * limit - limit
        order = ''
        where = """WHERE visit_plan_id = {} """.format(plan_id)
        where_original = where
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        select = "*"
        select_count = "id"
        join = """"""
        # if search:
        #     where += """""".format(search)
        breadcrumb_data = self.sab_model.get_all_activity_breadcrumb(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.sab_model.get_count_all_activity_breadcrumb(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.sab_model.get_count_all_activity_breadcrumb(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if breadcrumb_data:
            for bc in breadcrumb_data:
                data.append(bc)
        cycle['data'] = data
        cycle['total'] = count
        cycle['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if cycle['total_filter'] > page * limit:
            cycle['has_next'] = True
        else:
            cycle['has_next'] = False
        if limit <= page * count_filter - count_filter:
            cycle['has_prev'] = True
        else:
            cycle['has_prev'] = False
        return cycle

    def check_tap_activity(self, plan_id: 'int', user_id: 'int', customer_code: 'str'):
        """
        Function for create new log activity

        :param plan_id: int
        :param user_id: int
        :param customer_code: int
        :return:
            Success or failure message
        """
        # today = datetime.today()
        # today = today.strftime("%Y-%m-%d %H:%M:%S")
        start = 0
        limit = 1000
        select = "tap_nfc_type"
        where = """WHERE visit_plan_id = {0} AND user_id = {1} 
        AND nfc_code = '{2}'""".format(plan_id, user_id, customer_code)
        order = "ORDER BY tap_nfc_date DESC"

        result = self.sales_activity_model.get_all_activity(
            self.cursor, select=select, where=where, order=order, start=start, limit=limit
        )

        return result

    def check_tap_activity_by_visit_plan(self, plan_id: 'int', user_id: 'int'):
        """
        Function for create new log activity

        :param plan_id: int
        :param user_id: int
        :return:
            Success or failure message
        """
        # today = datetime.today()
        # today = today.strftime("%Y-%m-%d %H:%M:%S")
        start = 0
        limit = 1000
        select = "*"
        where = """WHERE visit_plan_id = {0} AND user_id = {1} """.format(plan_id, user_id)
        order = "ORDER BY tap_nfc_date DESC"

        result = self.sales_activity_model.get_all_activity(
            self.cursor, select=select, where=where, order=order, start=start, limit=limit
        )

        return result

    def get_statistic_performance_by_user_id(
            self, job_function: str, user_ids: list, start_date: str, end_date: str, plan_id: int
    ):
        """

        :param job_function:str
        :param user_ids: list
        :param start_date: str
        :param end_date: str
        :param plan_id: int
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

        if plan_id:
            if job_function == 'sales':
                where_al += """ AND al.visit_plan_id={0} """.format(plan_id)
            else:
                where_al += """ AND al.delivery_plan_id={0} """.format(plan_id)

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

        if plan_id:
            if job_function == "sales":
                where_al += """ AND al.visit_plan_id={0} """.format(plan_id)
            else:
                where_al += """ AND al.delivery_plan_id={0} """.format(plan_id)

        group = """GROUP BY al.create_by"""
        count_permission = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_al, order=order, group=group
        )
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

        if plan_id:
            where_vp += """ AND vp.id={0} """.format(plan_id)

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

        if plan_id:
            where_vp += """ AND vp.id={0} """.format(plan_id)

        group = """GROUP BY vp.user_id"""
        count_plan_new_dest = self.visit_plan_model.get_count_all_visit_plan_statistic(
            self.cursor, select=select, select_count=select_count_new_dest, join=join, where=where_vp, group=group
        )

        # TODO: Get Statistitic Actual Plan
        select = "u.id"
        select_from = """( SELECT act.* FROM (SELECT id, user_id, visit_plan_id, 
                REPLACE(nfc_code, " ", "") as nfc_code, tap_nfc_date, tap_nfc_type FROM sales_activity) as act 
                WHERE act.tap_nfc_type = 'IN' GROUP BY act.visit_plan_id, act.nfc_code, act.tap_nfc_type )"""
        select_count = ", COUNT(sa.id) as total"
        order = ''
        join = """as sa LEFT JOIN `users` as u ON sa.user_id = u.id """
        where_sa = """WHERE sa.user_id IN ({}) """.format(
            ", ".join(str(x) for x in user_ids)
        )
        if start_date and end_date:
            where_sa += """AND (sa.tap_nfc_date >= '{0} 00:00:00' AND sa.tap_nfc_date <= '{1} 23:59:59') """.format(
                start_date, end_date
            )
        else:
            where_sa += """AND (sa.tap_nfc_date LIKE '{}%')""".format(today)

        if plan_id:
            where_sa += """ AND sa.visit_plan_id={0} """.format(plan_id)

        group = """GROUP BY sa.user_id"""
        count_actual = self.sales_activity_model.get_count_all_activity_statistic(
            self.cursor, select=select, select_count=select_count, select_from=select_from, join=join,
            where=where_sa, order=order, group=group
        )

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

        if plan_id:
            where_sa += """ AND sa.visit_plan_id={0} """.format(plan_id)

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
        where_sa = """WHERE sa.user_id IN ({0}) AND sa.tap_nfc_type IN ('IN', 'OUT')""".format(
            ", ".join(str(x) for x in user_ids)
        )
        if start_date and end_date:
            where_sa += """AND (sa.tap_nfc_date >= '{0} 00:00:00' 
                            AND sa.tap_nfc_date <= '{1} 23:59:59') """.format(start_date, end_date)
        else:
            where_sa += """AND (sa.tap_nfc_date LIKE '{}%')""".format(today)

        if plan_id:
            where_sa += """ AND sa.visit_plan_id={0} """.format(plan_id)

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
            # print(df_visit_time_group.head(20))

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

        if plan_id:
            if job_function == "sales":
                where_bt += """ AND bt.visit_plan_id={0} """.format(plan_id)
            else:
                where_bt += """ AND bt.delivery_plan_id={0} """.format(plan_id)

        group = """GROUP BY bt.user_id"""
        break_time = self.break_time_model.get_count_all_break_time_statistic(
            self.cursor, select=select, join=join, where=where_bt, order=order, group=group
        )

        # TODO: Get statistic Permission Report Location for Sales
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

        if plan_id:
            if job_function == "sales":
                where_location += """ AND al.visit_plan_id={0} """.format(plan_id)
            else:
                where_location += """ AND al.delivery_plan_id={0} """.format(plan_id)

        count_location = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_location, order=order
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

        if plan_id:
            if job_function == "sales":
                where_nfc += """ AND al.visit_plan_id={0} """.format(plan_id)
            else:
                where_nfc += """ AND al.delivery_plan_id={0} """.format(plan_id)

        count_nfc_sales = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_nfc, order=order
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

        if plan_id:
            if job_function == "sales":
                where_print += """ AND al.visit_plan_id={0} """.format(plan_id)
            else:
                where_print += """ AND al.delivery_plan_id={0} """.format(plan_id)

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

        if plan_id:
            where_spm += """ AND spm.visit_plan_id={0} """.format(plan_id)

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

        if plan_id:
            where_spm_inv += """ AND spm.visit_plan_id={0} """.format(plan_id)

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

        if plan_id:
            where_spm_inv_wo += """ AND spm.visit_plan_id={0} """.format(plan_id)

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

        if plan_id:
            where_dp += """ AND dp.id={0} """.format(plan_id)

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

        if plan_id:
            where_dd += """ AND dd.delivery_plan_id={0} """.format(plan_id)

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

        if plan_id:
            where_dd += """ AND dd.delivery_plan_id={0} """.format(plan_id)

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
            data = {
                "plan": plan,
                "visited": actual,
                "new": new_destination,
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
            data_performance = data

        return data_performance


class LogisticActivityController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.logistic_activity_model = LogisticActivityModel()
        self.lab_model = LogisticActivityBreadcrumbModel()
        self.break_time_model = BreakTimeModel()
        self.idle_time_model = IdleTimeModel()
        self.user_model = UserModel()
        self.branch_model = BranchesModel()
        self.employee_model = EmployeeModel()
        self.division_model = DivisionModel()
        self.customer_model = CustomerModel()
        self.delivery_plan_model = DeliveryPlanModel()
        self.delivery_cycle_model = DeliveryCycleModel()
        self.delivery_model = DeliveryModel()
        self.permissions_model = PermissionsModel()
        self.packing_slip_model = PackingSlipModel()
        self.visit_plan_model = VisitPlanModel()
        self.sales_activity_model = SalesActivityModel()
        self.spm_model = SalesPaymentMobileModel()
        self.so_model = SalesOrderModel()
        self.ro_model = RequestOrderModel()

    def create(self, create_data: 'dict', user_id: 'int'):
        """
        Function for create new log activity

        :param create_data: dict
        :param user_id: int
        :return:
            Success or failure message
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.logistic_activity_model.insert_into_db(
                self.cursor, user_id=user_id, delivery_plan_id=create_data['delivery_plan_id'],
                nfc_code=create_data['nfc_code'], route_breadcrumb=create_data['route_breadcrumb'],
                distance=create_data['distance'], total_distance=create_data['total_distance'], tap_nfc_date=today,
                tap_nfc_type=create_data['tap_nfc_type'], create_date=today, update_date=today
            )
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        # TODO: update delivery plan to status finish
        if create_data['tap_nfc_type'] == "STOP":
            try:
                update_data = {
                    'id': create_data['delivery_plan_id'],
                    'status': True
                }
                update_delivery_plan = self.delivery_plan_model.update_by_id(self.cursor, update_data)
                mysql.connection.commit()
            except Exception as e:
                print(e)
                pass

        return result

    def get_all_activity_data(
            self, page: int, limit: int, search: str, column: str, direction: str, branch_privilege: list
    ):
        """
        Get List Of visit cycle
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: branch_privilige: list
        :param: division_privilige: list
        :return:
            Visit Cycle Object
        """
        activity = {}
        data = []
        start = page * limit - limit
        where = """WHERE (sa.id IN (SELECT MIN(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'START' 
        GROUP BY user_id, delivery_plan_id, nfc_code) OR sa.id IN (SELECT MAX(id) FROM `logistic_activity` 
        WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, delivery_plan_id, nfc_code) OR sa.id IN (SELECT MIN(id) 
        FROM `logistic_activity` WHERE `tap_nfc_type` = 'IN' GROUP BY user_id, delivery_plan_id, nfc_code) 
        OR sa.id IN (SELECT MAX(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'OUT' 
        GROUP BY user_id, delivery_plan_id, nfc_code)) AND (u.branch_id IN ({0})) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        where_original = where
        order = ''
        if column:
            if column == 'branch':
                order = """ORDER BY b.name {0}""".format(direction)
            elif column == 'division':
                order = """ORDER BY d.division_name {0}""".format(direction)
            elif column == 'user':
                order = """ORDER BY u.username {0}""".format(direction)
            else:
                order = """ORDER BY sa.{0} {1}""".format(column, direction)
        select = "sa.*"
        select_count = "sa.id"
        join = """as sa LEFT JOIN `users` as u ON sa.user_id = u.id 
        LEFT JOIN `branches` as b ON u.branch_id = b.id 
        LEFT JOIN `divisions` as d ON u.division_id = d.id 
        LEFT JOIN `employee` as e ON u.employee_id = e.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR e.name LIKE '%{0}%' 
            OR sa.tap_nfc_type LIKE '%{0}%') """.format(search)
        activity_data = self.logistic_activity_model.get_all_activity(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.logistic_activity_model.get_count_all_activity(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.logistic_activity_model.get_count_all_activity(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if activity_data:
            for ad in activity_data:
                if ad['tap_nfc_date'] is not None:
                    ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                if ad['create_date'] is not None:
                    ad['create_date'] = str(ad['create_date'])
                if ad['update_date'] is not None:
                    ad['update_date'] = str(ad['update_date'])
                ad['branch_name'] = None
                if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                    if ad['nfc_code'] is not None:
                        try:
                            ad['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, ad['nfc_code'], select="""name"""
                            )[0]['name']
                        except:
                            ad['branch_name'] = None
                ad['customer_code'] = None
                if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                    if ad['nfc_code'] is not None:
                        ad['customer_code'] = ad['nfc_code']
                if ad['user_id'] is not None:
                    try:
                        ad['user'] = self.user_model.get_user_by_id(
                            self.cursor, ad['user_id'], select="username, employee_id, branch_id, division_id"
                        )[0]
                        if ad['user']['employee_id'] is not None:
                            try:
                                ad['user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    ad['user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                ad['user']['name'] = None
                        if ad['user']['branch_id'] is not None:
                            try:
                                ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    ad['user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                ad['user']['branch_name'] = None
                    except:
                        ad['user'] = {}
                else:
                    ad['user'] = {}
                data.append(ad)
        activity['data'] = data
        activity['total'] = count
        activity['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if activity['total'] > page * limit:
            activity['has_next'] = True
        else:
            activity['has_next'] = False
        if limit <= page * count - count:
            activity['has_prev'] = True
        else:
            activity['has_prev'] = False
        return activity

    def get_all_activity_data_by_delivery_plan(
            self, page: int, limit: int, search: str, column: str, direction: str, branch_privilege: list,
            data_filter: list
    ):
        """
        Get List Of visit cycle
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: branch_privilige: list
        :param: division_privilige: list
        :return:
            Visit Cycle Object
        """
        cycle = {}
        data = []
        start = page * limit - limit
        order = ''
        where = """WHERE (dp.is_approval = 1 AND dp.is_deleted = 0) 
                AND (u.branch_id IN ({0})) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        where_original = where
        if column:
            if column == 'start_branch':
                order = """ORDER BY b1.name {0}""".format(direction)
            elif column == 'end_branch':
                order = """ORDER BY b2.name {0}""".format(direction)
            elif column == 'username':
                order = """ORDER BY u.username {0}""".format(direction)
            elif column == 'user':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY br.name {0}""".format(direction)
            else:
                order = """ORDER BY dp.{0} {1}""".format(column, direction)
        select = "dp.*"
        select_count = "dp.id"
        join = """as dp LEFT JOIN `users` as u ON dp.user_id = u.id 
                LEFT JOIN `employee` as e ON u.employee_id = e.id
                LEFT JOIN `branches` as br ON u.branch_id = br.id
                LEFT JOIN `branches` as b1 ON dp.start_route_branch_id = b1.id
                LEFT JOIN `branches` as b2 ON dp.end_route_branch_id = b2.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR br.name LIKE '%{0}%' OR b1.name LIKE '%{0}%' 
                    OR b2.name LIKE '%{0}%' OR e.name LIKE '%{0}%') """.format(search)
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date']:
                where += """AND (dp.date >= '{0} 00:00:00' AND dp.date <= '{1} 23:59:59') """.format(
                    data_filter['start_date'], data_filter['end_date']
                )
            if data_filter['user_id']:
                where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in data_filter['user_id']))
            if data_filter['branch_id']:
                where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['branch_id']))
        delivery_plan_data = self.delivery_plan_model.get_all_delivery_plan(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.delivery_plan_model.get_count_all_delivery_plan(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.delivery_plan_model.get_count_all_delivery_plan(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if delivery_plan_data:
            for vp in delivery_plan_data:
                # vp['plan_activity'] = []
                list_customer = []
                list_visited_customer = []
                list_new_customer = []
                list_unvisit_customer = []

                if vp['edit_data'] is not None:
                    vp['edit_data'] = json.loads(vp['edit_data'])
                if vp['date'] is not None:
                    vp['date'] = str(vp['date'])
                if vp['create_date'] is not None:
                    vp['create_date'] = str(vp['create_date'])
                if vp['update_date'] is not None:
                    vp['update_date'] = str(vp['update_date'])
                # Get Activity data
                data_activity_dict = dict()
                data_activity = []
                list_nfc_code = []

                plan_activity = []
                try:
                    # where = """WHERE (sa.id IN (SELECT MIN(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'START'
                    # GROUP BY user_id, delivery_plan_id, nfc_code) OR sa.id IN (SELECT MAX(id) FROM `logistic_activity`
                    # WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, delivery_plan_id, nfc_code) OR sa.id IN (SELECT MIN(id)
                    # FROM `logistic_activity` WHERE `tap_nfc_type` = 'IN' GROUP BY user_id, delivery_plan_id, nfc_code)
                    # OR sa.id IN (SELECT MAX(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'OUT'
                    # GROUP BY user_id, delivery_plan_id, nfc_code)) AND (delivery_plan_id = {0}) """.format(
                    #     vp['id'])

                    # query without grouping
                    where = """WHERE (
                            sa.id IN (SELECT MIN(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'START' GROUP BY user_id, delivery_plan_id, nfc_code) OR 
                            sa.id IN (SELECT MAX(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, delivery_plan_id, nfc_code) OR 
                            sa.id IN (SELECT id FROM `logistic_activity` WHERE `tap_nfc_type` = 'IN' ) OR 
                            sa.id IN (SELECT id FROM `logistic_activity` WHERE `tap_nfc_type` = 'OUT')
                        ) AND (delivery_plan_id = {0})""".format(vp['id'])

                    order = ""
                    select = "sa.*"
                    join = """AS sa"""
                    activity_data = self.logistic_activity_model.get_all_activity(
                        self.cursor, select=select, join=join, where=where, order=order, start=0, limit=1000
                    )

                    # Process data for Plan Activity key-> plan_activity
                    if activity_data:
                        for ad in activity_data:
                            if ad['tap_nfc_date'] is not None:
                                ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                            if ad['create_date'] is not None:
                                ad['create_date'] = str(ad['create_date'])
                            if ad['update_date'] is not None:
                                ad['update_date'] = str(ad['update_date'])

                            ad['branch_name'] = None
                            ad['branch_location'] = None
                            if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                                if ad['nfc_code'] is not None:
                                    try:
                                        branch = self.branch_model.get_branches_by_id(self.cursor, ad['nfc_code'])[0]
                                        ad['branch_name'] = branch['name']
                                        ad['branch_location'] = branch['address']
                                    except:
                                        ad['branch_name'] = None
                                        ad['branch_location'] = None
                                if ad['route_breadcrumb'] is not None:
                                    ad['route_breadcrumb'] = json.loads(ad['route_breadcrumb'])

                            ad['customer_code'] = None
                            ad['customer_name'] = None
                            ad['customer_address'] = None
                            if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                                if ad['nfc_code'] is not None:
                                    ad['customer_code'] = ad['nfc_code']
                                    try:
                                        customer = self.customer_model.get_customer_by_code(
                                            self.cursor, ad['nfc_code']
                                        )[0]
                                        ad['customer_name'] = customer['name']
                                        ad['customer_address'] = customer['address']
                                    except:
                                        ad['customer_name'] = None
                                        ad['customer_address'] = None
                                if ad['route_breadcrumb'] is not None:
                                    ad['route_breadcrumb'] = json.loads(ad['route_breadcrumb'])

                            if ad['user_id'] is not None:
                                try:
                                    ad['user'] = self.user_model.get_user_by_id(
                                        self.cursor, ad['user_id'],
                                        select="username, employee_id, branch_id, division_id"
                                    )[0]
                                    if ad['user']['employee_id'] is not None:
                                        try:
                                            ad['user']['name'] = self.employee_model.get_employee_by_id(
                                                self.cursor,
                                                ad['user']['employee_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['name'] = None
                                    if ad['user']['branch_id'] is not None:
                                        try:
                                            ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                self.cursor,
                                                ad['user']['branch_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['branch_name'] = None
                                    if ad['user']['division_id'] is not None:
                                        try:
                                            ad['user']['division_name'] = self.division_model.get_division_by_id(
                                                self.cursor, ad['user']['division_id'], select="division_name")[0][
                                                'division_name']
                                        except:
                                            ad['user']['division_name'] = None
                                except:
                                    ad['user'] = {}
                            else:
                                ad['user'] = {}

                            # check activity checkin on customer, not checkin on branch
                            if ad['nfc_code'] is not None and ad['customer_name'] is not None:
                                if len(list_visited_customer) > 0:
                                    if ad['nfc_code'] not in list_visited_customer:
                                        list_visited_customer.append(ad['nfc_code'])
                                else:
                                    list_visited_customer.append(ad['nfc_code'])

                            plan_activity.append(ad)

                    if plan_activity:
                        plan_activity_list = []
                        for rec in plan_activity:
                            plan_activity_dict = dict()
                            # print("======== Plan Activity {0}".format(rec))
                            if rec['tap_nfc_type'] == 'START':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = 0
                                plan_activity_dict['start_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['start_location_custom'] = False
                                    plan_activity_dict['start_location_name'] = rec['branch_name']
                                    plan_activity_dict['start_location_address'] = rec['branch_location']
                                else:
                                    # custom start
                                    plan_activity_dict['start_location_custom'] = True
                                    plan_activity_dict['start_location_name'] = None
                                    plan_activity_dict['start_location_address'] = rec['route_breadcrumb']['address']
                                plan_activity_dict['start_location'] = rec['route_breadcrumb']

                            if rec['tap_nfc_type'] == 'STOP':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = 0
                                plan_activity_dict['stop_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['stop_location_custom'] = False
                                    plan_activity_dict['stop_location_name'] = rec['branch_name']
                                    plan_activity_dict['stop_location_address'] = rec['branch_location']
                                else:
                                    # custom stop
                                    plan_activity_dict['stop_location_custom'] = True
                                    plan_activity_dict['stop_location_name'] = None
                                    plan_activity_dict['stop_location_address'] = rec['route_breadcrumb']['address']
                                plan_activity_dict['stop_location'] = rec['route_breadcrumb']

                            if rec['tap_nfc_type'] == 'IN':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = rec['distance']
                                plan_activity_dict['in_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['in_location_custom'] = False
                                    plan_activity_dict['in_location_name'] = rec['customer_name']
                                    plan_activity_dict['in_location_address'] = rec['customer_address']
                                else:
                                    # custom checkin
                                    plan_activity_dict['in_location_custom'] = True
                                    plan_activity_dict['in_location_name'] = rec['customer_name']
                                    plan_activity_dict['in_location_address'] = rec['route_breadcrumb']['address']

                            if rec['tap_nfc_type'] == 'OUT':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['out_time'] = rec['tap_nfc_date']

                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['out_location_custom'] = False
                                    plan_activity_dict['out_location_name'] = rec['customer_name']
                                    plan_activity_dict['out_location_address'] = rec['customer_address']
                                else:
                                    # custom checkout
                                    plan_activity_dict['out_location_custom'] = True
                                    plan_activity_dict['out_location_name'] = rec['customer_name']
                                    plan_activity_dict['out_location_address'] = rec['route_breadcrumb']['address']

                            plan_activity_list.append(plan_activity_dict)
                        plan_result = []
                        i = 0
                        for plan in plan_activity_list:
                            data_dict = dict()
                            if plan.get('start_time'):
                                data_dict['nfc_code'] = plan['nfc_code']
                                data_dict['start_time'] = plan['start_time']
                                data_dict['location_name'] = plan['start_location_name']
                                data_dict['location_address'] = plan['start_location_address']
                                data_dict['location_custom'] = plan['start_location_custom']
                                data_dict['distance'] = plan['distance']
                                data_dict['duration'] = 0

                            if plan.get('in_time'):
                                code = plan['nfc_code']
                                data_dict['nfc_code'] = code
                                data_dict['in_time'] = plan['in_time']
                                data_dict['distance'] = plan['distance']
                                data_dict['in_location_address'] = plan['in_location_address']
                                data_dict['in_location_name'] = plan['in_location_name']
                                data_dict['in_location_custom'] = plan['in_location_custom']
                                next_idx = i
                                next = next_idx + 1
                                if plan_activity_list[next]['nfc_code'] == code and plan_activity_list[next][
                                    'tap_nfc_type'] == 'OUT':
                                    # Tap Type STOP found
                                    data_dict['out_time'] = plan_activity_list[next]['out_time']
                                    data_dict['out_location_address'] = plan_activity_list[next]['out_location_address']
                                    data_dict['out_location_name'] = plan_activity_list[next]['out_location_name']
                                    data_dict['out_location_custom'] = plan_activity_list[next]['out_location_custom']

                                    # calculate duration
                                    out_time = datetime.strptime(data_dict['out_time'], "%Y-%m-%d %H:%M:%S")
                                    in_time = datetime.strptime(data_dict['in_time'], "%Y-%m-%d %H:%M:%S")
                                    if out_time > in_time:
                                        data_dict['duration'] = int((out_time - in_time).seconds / 60)
                                    else:
                                        data_dict['duration'] = 0
                                else:
                                    data_dict['out_time'] = None
                                    data_dict['out_location_address'] = None
                                    data_dict['out_location_name'] = None
                                    data_dict['out_location_custom'] = False
                                    data_dict['duration'] = 0

                            if plan.get('stop_time'):
                                data_dict['nfc_code'] = plan['nfc_code']
                                data_dict['stop_time'] = plan['stop_time']
                                data_dict['location_name'] = plan['stop_location_name']
                                data_dict['location_address'] = plan['stop_location_address']
                                data_dict['location_custom'] = plan['stop_location_custom']
                                data_dict['distance'] = plan['distance']
                                data_dict['duration'] = 0

                            if data_dict:
                                plan_result.append(data_dict)
                            i += 1

                        # calculate time range between activity
                        # and add key order
                        position = 0
                        if plan_result:
                            for plan in plan_result:
                                plan['order'] = position
                                if plan.get('start_time') and position == 0:
                                    plan['time_range'] = 0
                                else:
                                    if plan.get('in_time'):
                                        next_time = plan['in_time']
                                    elif plan.get('stop_time'):
                                        next_time = plan['stop_time']
                                    else:
                                        next_time = 0

                                    post = position
                                    index = post - 1
                                    if index >= 0:
                                        if plan_result[index].get('start_time'):
                                            prev_time = plan_result[index]['start_time']
                                        elif plan_result[index].get('out_time'):
                                            prev_time = plan_result[index]['out_time']
                                        else:
                                            prev_time = 0
                                    else:
                                        prev_time = 0

                                    if prev_time and next_time:
                                        prev_time_fmt = datetime.strptime(prev_time, "%Y-%m-%d %H:%M:%S")
                                        next_time_fmt = datetime.strptime(next_time, "%Y-%m-%d %H:%M:%S")
                                        if next_time_fmt > prev_time_fmt:
                                            plan['time_range'] = int((next_time_fmt - prev_time_fmt).seconds / 60)
                                        else:
                                            plan['time_range'] = 0
                                    else:
                                        plan['time_range'] = 0
                                position += 1
                            # print("result Plan Activity = {0}".format(plan_result))
                        vp['plan_activity'] = plan_result
                    else:
                        vp['plan_activity'] = []

                    # Process data for data Activity key-> data_activity
                    # previous process before ignore grouping
                    if activity_data:
                        for ad in activity_data:
                            if ad['tap_nfc_date'] is not None:
                                ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                            if ad['create_date'] is not None:
                                ad['create_date'] = str(ad['create_date'])
                            if ad['update_date'] is not None:
                                ad['update_date'] = str(ad['update_date'])
                            ad['branch_name'] = None
                            if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                                if ad['nfc_code'] is not None:
                                    try:
                                        ad['branch_name'] = self.branch_model.get_branches_by_id(
                                            self.cursor, ad['nfc_code'], select="""name"""
                                        )[0]['name']
                                    except:
                                        ad['branch_name'] = None
                            ad['customer_code'] = None
                            if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                                if ad['nfc_code'] is not None:
                                    ad['customer_code'] = ad['nfc_code']
                            if ad['user_id'] is not None:
                                try:
                                    ad['user'] = self.user_model.get_user_by_id(
                                        self.cursor, ad['user_id'],
                                        select="username, employee_id, branch_id, division_id"
                                    )[0]
                                    if ad['user']['employee_id'] is not None:
                                        try:
                                            ad['user']['name'] = self.employee_model.get_employee_by_id(
                                                self.cursor,
                                                ad['user']['employee_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['name'] = None
                                    if ad['user']['branch_id'] is not None:
                                        try:
                                            ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                self.cursor,
                                                ad['user']['branch_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['branch_name'] = None
                                    if ad['user']['division_id'] is not None:
                                        try:
                                            ad['user']['division_name'] = self.division_model.get_division_by_id(
                                                self.cursor, ad['user']['division_id'], select="division_name")[0][
                                                'division_name']
                                        except:
                                            ad['user']['division_name'] = None
                                except:
                                    ad['user'] = {}
                            else:
                                ad['user'] = {}
                            if ad['nfc_code'] is not None:
                                data_activity_dict[ad['nfc_code']] = dict()
                                list_nfc_code.append(ad['nfc_code'])
                            data_activity.append(ad)
                    if data_activity:
                        plan_activity_list = []
                        for rec in data_activity:
                            plan_activity_dict = dict()
                            if rec['tap_nfc_type'] == 'START':
                                data_activity_dict[rec['nfc_code']]['start_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = 0
                            if rec['tap_nfc_type'] == 'STOP':
                                data_activity_dict[rec['nfc_code']]['stop_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = 0
                            if rec['tap_nfc_type'] == 'IN':
                                data_activity_dict[rec['nfc_code']]['in_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = rec['distance']
                            if rec['tap_nfc_type'] == 'OUT':
                                data_activity_dict[rec['nfc_code']]['out_time'] = rec['tap_nfc_date']

                        # Calculation duration
                        unique_code = set(list_nfc_code)
                        for code in unique_code:
                            if data_activity_dict[code].get('in_time'):
                                in_time = data_activity_dict[code]['in_time']
                            else:
                                in_time = 0
                            if data_activity_dict[code].get('out_time'):
                                out_time = data_activity_dict[code]['out_time']
                            else:
                                out_time = 0
                            if in_time and out_time:
                                out_time_fmt = datetime.strptime(out_time, "%Y-%m-%d %H:%M:%S")
                                in_time_fmt = datetime.strptime(in_time, "%Y-%m-%d %H:%M:%S")
                                data_activity_dict[code]['duration'] = int((out_time_fmt - in_time_fmt).seconds / 60)
                            else:
                                data_activity_dict[code]['duration'] = 0

                    vp['data_activity'] = data_activity_dict
                except Exception as e:
                    print(e)
                    vp['data_activity'] = dict()
                    vp['plan_activity'] = []

                # Get Data Performance
                try:
                    performance_date = vp['date'].split(" ")
                    performance_date = performance_date[0]
                    data_performance = self.get_statistic_performance_by_user_id(
                        job_function='logistic', user_ids=[vp['user_id']], start_date=performance_date,
                        end_date=performance_date, plan_id=vp['id']
                    )

                    # vp['data_performance'] = data_performance

                    # TODO Get Data Total Distance
                    select = "*"
                    where_distance = """WHERE user_id={0} AND tap_nfc_type='STOP' """.format(vp['user_id'])
                    where_distance += """AND delivery_plan_id={} """.format(vp['id'])
                    where_distance += """AND (tap_nfc_date >= '{0} 00:00:00' AND tap_nfc_date <= '{1} 23:59:59') """.format(
                        performance_date, performance_date)
                    order = 'ORDER BY create_date ASC'
                    data_distance = self.logistic_activity_model.get_all_activity(self.cursor, select=select,
                                                                                  where=where_distance, order=order)
                    total_distance = 0
                    if data_distance:
                        for rec_distance in data_distance:
                            total_distance += rec_distance['total_distance']
                    data_performance['total_distance'] = total_distance

                    vp['data_performance'] = data_performance
                except Exception as e:
                    print(e)
                    vp['data_performance'] = dict()
                if vp['destination_order'] is not None:
                    vp['destination_order'] = json.loads(vp['destination_order'])
                if vp['destination'] is not None:
                    vp['destination'] = json.loads(vp['destination'])
                    idx = 0
                    for rec in vp['destination']:
                        try:
                            customer = self.customer_model.get_customer_by_id(
                                self.cursor, rec['customer_code'],
                                select="name, email, phone, address, lng, lat, nfcid, contacts, business_activity")[0]
                            vp['destination'][idx]['customer_name'] = customer['name']
                            vp['destination'][idx]['customer_email'] = customer['email']
                            vp['destination'][idx]['phone'] = customer['phone']
                            vp['destination'][idx]['address'] = customer['address']
                            vp['destination'][idx]['lng'] = customer['lng']
                            vp['destination'][idx]['lat'] = customer['lat']
                            vp['destination'][idx]['nfcid'] = customer['nfcid']
                            if customer['contacts'] is not None:
                                vp['destination'][idx]['contacts'] = json.loads(customer['contacts'])
                            else:
                                vp['destination'][idx]['contacts'] = None
                            if customer['business_activity'] is not None:
                                vp['destination'][idx]['business_activity'] = json.loads(customer['business_activity'])
                            else:
                                vp['destination'][idx]['business_activity'] = None
                        except:
                            vp['destination'][idx]['customer_name'] = None
                            vp['destination'][idx]['customer_email'] = None
                            vp['destination'][idx]['phone'] = None
                            vp['destination'][idx]['address'] = None
                            vp['destination'][idx]['lng'] = None
                            vp['destination'][idx]['lat'] = None
                            vp['destination'][idx]['nfcid'] = None
                            vp['destination'][idx]['contacts'] = None
                            vp['destination'][idx]['business_activity'] = None
                        list_customer.append(rec['customer_code'])
                        idx += 1

                if vp['destination_new'] is not None:
                    vp['destination_new'] = json.loads(vp['destination_new'])
                    for rec in vp['destination_new']:
                        list_new_customer.append(rec['customer_code'])

                # process unvisited customer
                list_all_customer = list_customer
                list_all_customer.extend(list_new_customer)
                if len(list_all_customer) >= len(list_visited_customer):
                    diff = list(set(list_all_customer) - set(list_visited_customer))
                    for code in diff:
                        data_cust = dict()
                        try:
                            customer = self.customer_model.get_customer_by_id(
                                self.cursor, code,
                                select="name, email, phone, address, lng, lat, nfcid, contacts, business_activity")[0]
                            data_cust['customer_name'] = customer['name']
                            data_cust['customer_email'] = customer['email']
                            data_cust['phone'] = customer['phone']
                            data_cust['address'] = customer['address']
                            data_cust['lng'] = customer['lng']
                            data_cust['lat'] = customer['lat']
                            data_cust['nfcid'] = customer['nfcid']
                            if customer['contacts'] is not None:
                                data_cust['contacts'] = json.loads(customer['contacts'])
                            else:
                                data_cust['contacts'] = None
                            if customer['business_activity'] is not None:
                                data_cust['business_activity'] = json.loads(customer['business_activity'])
                            else:
                                data_cust['business_activity'] = None
                        except:
                            data_cust['customer_name'] = None
                            data_cust['customer_email'] = None
                            data_cust['phone'] = None
                            data_cust['address'] = None
                            data_cust['lng'] = None
                            data_cust['lat'] = None
                            data_cust['nfcid'] = None
                            data_cust['contacts'] = None
                            data_cust['business_activity'] = None
                        list_unvisit_customer.append(data_cust)

                vp['unvisit_customer'] = list_unvisit_customer

                # vc['customer'] = list_customer
                vp['total_customer'] = len(set(list_customer))
                if vp['user_id'] is not None:
                    try:
                        vp['user'] = self.user_model.get_user_by_id(
                            self.cursor, vp['user_id'], select="username, employee_id, branch_id")[0]
                    except:
                        vp['user'] = {}
                    if vp['user']['employee_id'] is not None:
                        try:
                            vp['user']['name'] = self.employee_model.get_employee_by_id(
                                self.cursor, vp['user']['employee_id'], select="""name""")[0]['name']
                        except:
                            vp['user']['name'] = None
                    if vp['user']['branch_id'] is not None:
                        try:
                            vp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, vp['user']['branch_id'], select="""name""")[0]['name']
                        except:
                            vp['user']['branch_name'] = None
                else:
                    vp['user'] = {}
                if vp['start_route_branch_id'] is not None:
                    try:
                        vp['start_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, vp['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        vp['start_route_branch'] = {}
                else:
                    vp['start_route_branch'] = {}
                if vp['end_route_branch_id'] is not None:
                    try:
                        vp['end_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, vp['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        vp['end_route_branch'] = {}
                else:
                    vp['end_route_branch'] = {}
                del vp['route']
                # vp['total_invoice'] = 2
                # vp['invoice_ids'] = ["SO-PSCN000005850", "SO-PSCN000005776"]
                data.append(vp)
        cycle['data'] = data
        cycle['total'] = count
        cycle['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if cycle['total_filter'] > page * limit:
            cycle['has_next'] = True
        else:
            cycle['has_next'] = False
        if limit <= page * count_filter - count_filter:
            cycle['has_prev'] = True
        else:
            cycle['has_prev'] = False
        return cycle

    def get_all_export_activity_data_by_delivery_plan(
            self, page: int, limit: int, search: str, column: str, direction: str, branch_privilege: list,
            data_filter: list
    ):
        """
        Get List Of visit cycle
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: branch_privilige: list
        :param: division_privilige: list
        :return:
            Visit Cycle Object
        """
        result_data = {}
        cycle = {}
        data = []
        start = page * limit - limit
        order = ''
        where = """WHERE (dp.is_approval = 1 AND dp.is_deleted = 0) 
                AND (u.branch_id IN ({0})) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        where_original = where
        if column:
            if column == 'start_branch':
                order = """ORDER BY b1.name {0}""".format(direction)
            elif column == 'end_branch':
                order = """ORDER BY b2.name {0}""".format(direction)
            elif column == 'username':
                order = """ORDER BY u.username {0}""".format(direction)
            elif column == 'user':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY br.name {0}""".format(direction)
            else:
                order = """ORDER BY dp.{0} {1}""".format(column, direction)
        select = "dp.*"
        select_count = "dp.id"
        join = """as dp LEFT JOIN `users` as u ON dp.user_id = u.id 
                LEFT JOIN `employee` as e ON u.employee_id = e.id
                LEFT JOIN `branches` as br ON u.branch_id = br.id
                LEFT JOIN `branches` as b1 ON dp.start_route_branch_id = b1.id
                LEFT JOIN `branches` as b2 ON dp.end_route_branch_id = b2.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR br.name LIKE '%{0}%' OR b1.name LIKE '%{0}%' 
                    OR b2.name LIKE '%{0}%' OR e.name LIKE '%{0}%') """.format(search)
        if data_filter:
            tmp_data_filter = data_filter[0]
            if tmp_data_filter['start_date']:
                where += """AND (dp.date >= '{0} 00:00:00' AND dp.date <= '{1} 23:59:59') """.format(
                    tmp_data_filter['start_date'], tmp_data_filter['end_date']
                )
            if tmp_data_filter['user_id']:
                where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['user_id']))
            if tmp_data_filter['branch_id']:
                where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['branch_id']))
        delivery_plan_data = self.delivery_plan_model.get_all_delivery_plan(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.delivery_plan_model.get_count_all_delivery_plan(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.delivery_plan_model.get_count_all_delivery_plan(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if delivery_plan_data:
            for vp in delivery_plan_data:
                list_customer = []
                if vp['edit_data'] is not None:
                    vp['edit_data'] = json.loads(vp['edit_data'])
                if vp['date'] is not None:
                    vp['date'] = str(vp['date'])
                if vp['create_date'] is not None:
                    vp['create_date'] = str(vp['create_date'])
                if vp['update_date'] is not None:
                    vp['update_date'] = str(vp['update_date'])
                # Get Activity data
                data_activity_dict = dict()
                data_activity = []
                list_nfc_code = []

                plan_activity = []
                try:
                    # where = """WHERE (sa.id IN (SELECT MIN(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'START'
                    # GROUP BY user_id, delivery_plan_id, nfc_code) OR sa.id IN (SELECT MAX(id) FROM `logistic_activity`
                    # WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, delivery_plan_id, nfc_code) OR sa.id IN (SELECT MIN(id)
                    # FROM `logistic_activity` WHERE `tap_nfc_type` = 'IN' GROUP BY user_id, delivery_plan_id, nfc_code)
                    # OR sa.id IN (SELECT MAX(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'OUT'
                    # GROUP BY user_id, delivery_plan_id, nfc_code)) AND (delivery_plan_id = {0}) """.format(
                    #     vp['id'])

                    # query without grouping
                    where = """WHERE (
                            sa.id IN (SELECT MIN(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'START' GROUP BY user_id, delivery_plan_id, nfc_code) OR 
                            sa.id IN (SELECT MAX(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, delivery_plan_id, nfc_code) OR 
                            sa.id IN (SELECT id FROM `logistic_activity` WHERE `tap_nfc_type` = 'IN' ) OR 
                            sa.id IN (SELECT id FROM `logistic_activity` WHERE `tap_nfc_type` = 'OUT')
                        ) AND (delivery_plan_id = {0})""".format(vp['id'])

                    order = ""
                    select = "sa.*"
                    join = """AS sa"""
                    activity_data = self.logistic_activity_model.get_all_activity(
                        self.cursor, select=select, join=join, where=where, order=order, start=0, limit=1000
                    )

                    # Process data for Plan Activity key-> plan_activity
                    if activity_data:
                        for ad in activity_data:
                            if ad['tap_nfc_date'] is not None:
                                ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                            if ad['create_date'] is not None:
                                ad['create_date'] = str(ad['create_date'])
                            if ad['update_date'] is not None:
                                ad['update_date'] = str(ad['update_date'])

                            ad['branch_name'] = None
                            ad['branch_location'] = None
                            if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                                if ad['nfc_code'] is not None:
                                    try:
                                        branch = self.branch_model.get_branches_by_id(self.cursor, ad['nfc_code'])[0]
                                        ad['branch_name'] = branch['name']
                                        ad['branch_location'] = branch['address']
                                    except:
                                        ad['branch_name'] = None
                                        ad['branch_location'] = None
                                if ad['route_breadcrumb'] is not None:
                                    ad['route_breadcrumb'] = json.loads(ad['route_breadcrumb'])

                            ad['customer_code'] = None
                            ad['customer_name'] = None
                            ad['customer_address'] = None
                            if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                                if ad['nfc_code'] is not None:
                                    ad['customer_code'] = ad['nfc_code']
                                    try:
                                        customer = self.customer_model.get_customer_by_code(
                                            self.cursor, ad['nfc_code']
                                        )[0]
                                        ad['customer_name'] = customer['name']
                                        ad['customer_address'] = customer['address']
                                    except:
                                        ad['customer_name'] = None
                                        ad['customer_address'] = None
                                if ad['route_breadcrumb'] is not None:
                                    ad['route_breadcrumb'] = json.loads(ad['route_breadcrumb'])

                            if ad['user_id'] is not None:
                                try:
                                    ad['user'] = self.user_model.get_user_by_id(
                                        self.cursor, ad['user_id'],
                                        select="username, employee_id, branch_id, division_id"
                                    )[0]
                                    if ad['user']['employee_id'] is not None:
                                        try:
                                            ad['user']['name'] = self.employee_model.get_employee_by_id(
                                                self.cursor,
                                                ad['user']['employee_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['name'] = None
                                    if ad['user']['branch_id'] is not None:
                                        try:
                                            ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                self.cursor,
                                                ad['user']['branch_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['branch_name'] = None
                                    if ad['user']['division_id'] is not None:
                                        try:
                                            ad['user']['division_name'] = self.division_model.get_division_by_id(
                                                self.cursor, ad['user']['division_id'], select="division_name")[0][
                                                'division_name']
                                        except:
                                            ad['user']['division_name'] = None
                                except:
                                    ad['user'] = {}
                            else:
                                ad['user'] = {}
                            plan_activity.append(ad)

                    if plan_activity:
                        plan_activity_list = []
                        for rec in plan_activity:
                            plan_activity_dict = dict()
                            # print("======== Plan Activity {0}".format(rec))
                            if rec['tap_nfc_type'] == 'START':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = 0
                                plan_activity_dict['start_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['start_location_custom'] = False
                                    plan_activity_dict['start_location_name'] = rec['branch_name']
                                    plan_activity_dict['start_location_address'] = rec['branch_location']
                                else:
                                    # custom start
                                    plan_activity_dict['start_location_custom'] = True
                                    plan_activity_dict['start_location_name'] = None
                                    plan_activity_dict['start_location_address'] = rec['route_breadcrumb']['address']
                                plan_activity_dict['start_location'] = rec['route_breadcrumb']

                            if rec['tap_nfc_type'] == 'STOP':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = 0
                                plan_activity_dict['stop_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['stop_location_custom'] = False
                                    plan_activity_dict['stop_location_name'] = rec['branch_name']
                                    plan_activity_dict['stop_location_address'] = rec['branch_location']
                                else:
                                    # custom stop
                                    plan_activity_dict['stop_location_custom'] = True
                                    plan_activity_dict['stop_location_name'] = None
                                    plan_activity_dict['stop_location_address'] = rec['route_breadcrumb']['address']
                                plan_activity_dict['stop_location'] = rec['route_breadcrumb']

                            if rec['tap_nfc_type'] == 'IN':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = rec['distance']
                                plan_activity_dict['in_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['in_location_custom'] = False
                                    plan_activity_dict['in_location_name'] = rec['customer_name']
                                    plan_activity_dict['in_location_address'] = rec['customer_address']
                                else:
                                    # custom checkin
                                    plan_activity_dict['in_location_custom'] = True
                                    plan_activity_dict['in_location_name'] = rec['customer_name']
                                    plan_activity_dict['in_location_address'] = rec['route_breadcrumb']['address']

                            if rec['tap_nfc_type'] == 'OUT':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['out_time'] = rec['tap_nfc_date']

                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['out_location_custom'] = False
                                    plan_activity_dict['out_location_name'] = rec['customer_name']
                                    plan_activity_dict['out_location_address'] = rec['customer_address']
                                else:
                                    # custom checkout
                                    plan_activity_dict['out_location_custom'] = True
                                    plan_activity_dict['out_location_name'] = rec['customer_name']
                                    plan_activity_dict['out_location_address'] = rec['route_breadcrumb']['address']

                            plan_activity_list.append(plan_activity_dict)
                        plan_result = []
                        i = 0
                        for plan in plan_activity_list:
                            data_dict = dict()
                            if plan.get('start_time'):
                                data_dict['nfc_code'] = plan['nfc_code']
                                data_dict['start_time'] = plan['start_time']
                                data_dict['location_name'] = plan['start_location_name']
                                data_dict['location_address'] = plan['start_location_address']
                                data_dict['location_custom'] = plan['start_location_custom']
                                data_dict['distance'] = plan['distance']
                                data_dict['duration'] = 0

                            if plan.get('in_time'):
                                code = plan['nfc_code']
                                data_dict['nfc_code'] = code
                                data_dict['in_time'] = plan['in_time']
                                data_dict['distance'] = plan['distance']
                                data_dict['in_location_address'] = plan['in_location_address']
                                data_dict['in_location_name'] = plan['in_location_name']
                                data_dict['in_location_custom'] = plan['in_location_custom']
                                next_idx = i
                                next = next_idx + 1
                                if plan_activity_list[next]['nfc_code'] == code and plan_activity_list[next][
                                    'tap_nfc_type'] == 'OUT':
                                    # Tap Type STOP found
                                    data_dict['out_time'] = plan_activity_list[next]['out_time']
                                    data_dict['out_location_address'] = plan_activity_list[next]['out_location_address']
                                    data_dict['out_location_name'] = plan_activity_list[next]['out_location_name']
                                    data_dict['out_location_custom'] = plan_activity_list[next]['out_location_custom']

                                    # calculate duration
                                    out_time = datetime.strptime(data_dict['out_time'], "%Y-%m-%d %H:%M:%S")
                                    in_time = datetime.strptime(data_dict['in_time'], "%Y-%m-%d %H:%M:%S")
                                    if out_time > in_time:
                                        data_dict['duration'] = int((out_time - in_time).seconds / 60)
                                    else:
                                        data_dict['duration'] = 0
                                else:
                                    data_dict['out_time'] = None
                                    data_dict['out_location_address'] = None
                                    data_dict['out_location_name'] = None
                                    data_dict['out_location_custom'] = False
                                    data_dict['duration'] = 0

                            if plan.get('stop_time'):
                                data_dict['nfc_code'] = plan['nfc_code']
                                data_dict['stop_time'] = plan['stop_time']
                                data_dict['location_name'] = plan['stop_location_name']
                                data_dict['location_address'] = plan['stop_location_address']
                                data_dict['location_custom'] = plan['stop_location_custom']
                                data_dict['distance'] = plan['distance']
                                data_dict['duration'] = 0

                            if data_dict:
                                plan_result.append(data_dict)
                            i += 1

                        # calculate time range between activity
                        # and add key order
                        position = 0
                        if plan_result:
                            for plan in plan_result:
                                plan['order'] = position
                                if plan.get('start_time') and position == 0:
                                    plan['time_range'] = 0
                                else:
                                    if plan.get('in_time'):
                                        next_time = plan['in_time']
                                    elif plan.get('stop_time'):
                                        next_time = plan['stop_time']
                                    else:
                                        next_time = 0

                                    post = position
                                    index = post - 1
                                    if index >= 0:
                                        if plan_result[index].get('start_time'):
                                            prev_time = plan_result[index]['start_time']
                                        elif plan_result[index].get('out_time'):
                                            prev_time = plan_result[index]['out_time']
                                        else:
                                            prev_time = 0
                                    else:
                                        prev_time = 0

                                    if prev_time and next_time:
                                        prev_time_fmt = datetime.strptime(prev_time, "%Y-%m-%d %H:%M:%S")
                                        next_time_fmt = datetime.strptime(next_time, "%Y-%m-%d %H:%M:%S")
                                        if next_time_fmt > prev_time_fmt:
                                            plan['time_range'] = int((next_time_fmt - prev_time_fmt).seconds / 60)
                                        else:
                                            plan['time_range'] = 0
                                    else:
                                        plan['time_range'] = 0
                                position += 1
                            # print("result Plan Activity = {0}".format(plan_result))
                        vp['plan_activity'] = plan_result
                    else:
                        vp['plan_activity'] = []

                    # Process data for data Activity key-> data_activity
                    # previous process before ignore grouping
                    if activity_data:
                        for ad in activity_data:
                            if ad['tap_nfc_date'] is not None:
                                ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                            if ad['create_date'] is not None:
                                ad['create_date'] = str(ad['create_date'])
                            if ad['update_date'] is not None:
                                ad['update_date'] = str(ad['update_date'])
                            ad['branch_name'] = None
                            if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                                if ad['nfc_code'] is not None:
                                    try:
                                        ad['branch_name'] = self.branch_model.get_branches_by_id(
                                            self.cursor, ad['nfc_code'], select="""name"""
                                        )[0]['name']
                                    except:
                                        ad['branch_name'] = None
                            ad['customer_code'] = None
                            if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                                if ad['nfc_code'] is not None:
                                    ad['customer_code'] = ad['nfc_code']
                            if ad['user_id'] is not None:
                                try:
                                    ad['user'] = self.user_model.get_user_by_id(
                                        self.cursor, ad['user_id'],
                                        select="username, employee_id, branch_id, division_id"
                                    )[0]
                                    if ad['user']['employee_id'] is not None:
                                        try:
                                            ad['user']['name'] = self.employee_model.get_employee_by_id(
                                                self.cursor,
                                                ad['user']['employee_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['name'] = None
                                    if ad['user']['branch_id'] is not None:
                                        try:
                                            ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                self.cursor,
                                                ad['user']['branch_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['branch_name'] = None
                                    if ad['user']['division_id'] is not None:
                                        try:
                                            ad['user']['division_name'] = self.division_model.get_division_by_id(
                                                self.cursor, ad['user']['division_id'], select="division_name")[0][
                                                'division_name']
                                        except:
                                            ad['user']['division_name'] = None
                                except:
                                    ad['user'] = {}
                            else:
                                ad['user'] = {}
                            if ad['nfc_code'] is not None:
                                data_activity_dict[ad['nfc_code']] = dict()
                                list_nfc_code.append(ad['nfc_code'])
                            data_activity.append(ad)
                    if data_activity:
                        plan_activity_list = []
                        for rec in data_activity:
                            plan_activity_dict = dict()
                            if rec['tap_nfc_type'] == 'START':
                                data_activity_dict[rec['nfc_code']]['start_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = 0
                            if rec['tap_nfc_type'] == 'STOP':
                                data_activity_dict[rec['nfc_code']]['stop_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = 0
                            if rec['tap_nfc_type'] == 'IN':
                                data_activity_dict[rec['nfc_code']]['in_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = rec['distance']
                            if rec['tap_nfc_type'] == 'OUT':
                                data_activity_dict[rec['nfc_code']]['out_time'] = rec['tap_nfc_date']

                        # Calculation duration
                        unique_code = set(list_nfc_code)
                        for code in unique_code:
                            if data_activity_dict[code].get('in_time'):
                                in_time = data_activity_dict[code]['in_time']
                            else:
                                in_time = 0
                            if data_activity_dict[code].get('out_time'):
                                out_time = data_activity_dict[code]['out_time']
                            else:
                                out_time = 0
                            if in_time and out_time:
                                out_time_fmt = datetime.strptime(out_time, "%Y-%m-%d %H:%M:%S")
                                in_time_fmt = datetime.strptime(in_time, "%Y-%m-%d %H:%M:%S")
                                data_activity_dict[code]['duration'] = int((out_time_fmt - in_time_fmt).seconds / 60)
                            else:
                                data_activity_dict[code]['duration'] = 0

                    vp['data_activity'] = data_activity_dict
                except Exception as e:
                    print(e)
                    vp['data_activity'] = dict()
                    vp['plan_activity'] = []

                # Get Data Performance
                try:
                    performance_date = vp['date'].split(" ")
                    performance_date = performance_date[0]
                    data_performance = self.get_statistic_performance_by_user_id(
                        job_function='logistic', user_ids=[vp['user_id']], start_date=performance_date,
                        end_date=performance_date, plan_id=vp['id']
                    )

                    # vp['data_performance'] = data_performance

                    # TODO Get Data Total Distance
                    select = "*"
                    where_distance = """WHERE user_id={0} AND tap_nfc_type='STOP' """.format(vp['user_id'])
                    where_distance += """AND delivery_plan_id={} """.format(vp['id'])
                    where_distance += """AND (tap_nfc_date >= '{0} 00:00:00' AND tap_nfc_date <= '{1} 23:59:59') """.format(
                        performance_date, performance_date)
                    order = 'ORDER BY create_date ASC'
                    data_distance = self.logistic_activity_model.get_all_activity(self.cursor, select=select,
                                                                                  where=where_distance, order=order)
                    total_distance = 0
                    if data_distance:
                        for rec_distance in data_distance:
                            total_distance += rec_distance['total_distance']
                    data_performance['total_distance'] = total_distance

                    vp['data_performance'] = data_performance
                except Exception as e:
                    print(e)
                    vp['data_performance'] = dict()
                if vp['destination_order'] is not None:
                    vp['destination_order'] = json.loads(vp['destination_order'])
                if vp['destination'] is not None:
                    vp['destination'] = json.loads(vp['destination'])
                    idx = 0
                    for rec in vp['destination']:
                        try:
                            customer = self.customer_model.get_customer_by_id(
                                self.cursor, rec['customer_code'],
                                select="name, email, phone, address, lng, lat, nfcid, contacts, business_activity")[0]
                            vp['destination'][idx]['customer_name'] = customer['name']
                            vp['destination'][idx]['customer_email'] = customer['email']
                            vp['destination'][idx]['phone'] = customer['phone']
                            vp['destination'][idx]['address'] = customer['address']
                            vp['destination'][idx]['lng'] = customer['lng']
                            vp['destination'][idx]['lat'] = customer['lat']
                            vp['destination'][idx]['nfcid'] = customer['nfcid']
                            if customer['contacts'] is not None:
                                vp['destination'][idx]['contacts'] = json.loads(customer['contacts'])
                            else:
                                vp['destination'][idx]['contacts'] = None
                            if customer['business_activity'] is not None:
                                vp['destination'][idx]['business_activity'] = json.loads(customer['business_activity'])
                            else:
                                vp['destination'][idx]['business_activity'] = None
                            try:
                                summary = self.visit_plan_summary_model.get_visit_plan_summary_by_plan_id_customer_code(
                                    self.cursor, vp['id'], rec['customer_code']
                                )
                                if len(summary) == 0:
                                    vp['destination'][idx]['summary'] = None
                                else:
                                    summary = summary[0]
                                    del summary['visit_images']
                                    del summary['competitor_images']
                                    if summary['create_date'] is not None:
                                        summary['create_date'] = str(summary['create_date'])
                                    if summary['update_date'] is not None:
                                        summary['update_date'] = str(summary['update_date'])
                                    vp['destination'][idx]['summary'] = summary
                            except:
                                vp['destination'][idx]['summary'] = None
                        except:
                            vp['destination'][idx]['customer_name'] = None
                            vp['destination'][idx]['customer_email'] = None
                            vp['destination'][idx]['phone'] = None
                            vp['destination'][idx]['address'] = None
                            vp['destination'][idx]['lng'] = None
                            vp['destination'][idx]['lat'] = None
                            vp['destination'][idx]['nfcid'] = None
                            vp['destination'][idx]['contacts'] = None
                            vp['destination'][idx]['business_activity'] = None
                            vp['destination'][idx]['summary'] = None
                        list_customer.append(rec['customer_code'])
                        idx += 1
                # vc['customer'] = list_customer
                vp['total_customer'] = len(set(list_customer))
                if vp['user_id'] is not None:
                    try:
                        vp['user'] = self.user_model.get_user_by_id(
                            self.cursor, vp['user_id'], select="username, employee_id, branch_id")[0]
                    except:
                        vp['user'] = {}
                    if vp['user']['employee_id'] is not None:
                        try:
                            vp['user']['name'] = self.employee_model.get_employee_by_id(
                                self.cursor, vp['user']['employee_id'], select="""name""")[0]['name']
                        except:
                            vp['user']['name'] = None
                    if vp['user']['branch_id'] is not None:
                        try:
                            vp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, vp['user']['branch_id'], select="""name""")[0]['name']
                        except:
                            vp['user']['branch_name'] = None
                else:
                    vp['user'] = {}
                if vp['start_route_branch_id'] is not None:
                    try:
                        vp['start_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, vp['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        vp['start_route_branch'] = {}
                else:
                    vp['start_route_branch'] = {}
                if vp['end_route_branch_id'] is not None:
                    try:
                        vp['end_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, vp['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        vp['end_route_branch'] = {}
                else:
                    vp['end_route_branch'] = {}
                del vp['route']
                # vp['total_invoice'] = 2
                # vp['invoice_ids'] = ["SO-PSCN000005850", "SO-PSCN000005776"]
                data.append(vp)
        output = BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Data Delivery Plan')
        merge_format = workbook.add_format(
            {
                'bold': 1,
                'border': 0,
                'align': 'left',
                'valign': 'vcenter'
            }
        )
        merge_format_start_end = workbook.add_format(
            {
                'bold': 1,
                'border': 0,
                'align': 'left',
                'valign': 'vcenter',
                'bg_color': '#99ff66'
            }
        )

        header_format = workbook.add_format(
            {
                'bold': 1,
                'border': 0,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#bababa'
            }
        )
        highlight_format = workbook.add_format(
            {
                'bold': 0,
                'border': 0,
                'align': 'left',
                'valign': 'vcenter',
                'bg_color': '#f1f1f1'
            }
        )
        # Header sheet
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date'] and not data_filter['user_id']:
                worksheet.merge_range(
                    'A1:L1',
                    'DELIVERY PLAN (USER: ALL, TANGGAL: {0} s/d {1})'.format(
                        data_filter['start_date'], data_filter['end_date']
                    ),
                    merge_format
                )
            elif data_filter['user_id'] and not data_filter['start_date']:
                worksheet.merge_range(
                    'A1:L1',
                    'DELIVERY PLAN (USER: {0}, TANGGAL: ALL)'.format(", ".join(x for x in data_filter['username'])),
                    merge_format
                )
            else:
                worksheet.merge_range(
                    'A1:L1',
                    'DELIVERY PLAN (USER: {0}, TANGGAL: {1} s/d {2})'.format(
                        ", ".join(x for x in data_filter['username']), data_filter['start_date'],
                        data_filter['end_date']
                    ),
                    merge_format
                )
        else:
            worksheet.merge_range('A1:L1', 'DELIVERY PLAN (USER: ALL, TANGGAL: ALL)', merge_format)

        worksheet.write('A3', 'TANGGAL', header_format)
        worksheet.write('B3', 'DRIVER', header_format)
        worksheet.write('C3', 'BRANCH', header_format)
        worksheet.write('D3', 'BREAK TIME (Minutes)', header_format)
        worksheet.write('E3', 'VISITED', header_format)
        worksheet.write('F3', 'VISIT TIME (Minutes)', header_format)
        worksheet.write('G3', 'DRIVING TIME (Minutes)', header_format)
        worksheet.write('H3', 'PLAN', header_format)
        worksheet.write('I3', 'ALERT', header_format)
        worksheet.write('J3', 'PERMISSION', header_format)
        worksheet.write('K3', 'CANCEL', header_format)
        worksheet.write('L3', 'PACKING SLIP', header_format)
        data_rows = 3
        for rec in data:
            actual = len(rec['data_activity']) - 1
            if actual < 0:
                actual = 0
            worksheet.write(data_rows, 0, rec['date'], highlight_format)
            worksheet.write(data_rows, 1, rec['user']['name'], highlight_format)
            worksheet.write(data_rows, 2, rec['user']['branch_name'], highlight_format)
            if len(rec['data_performance']) is not 0:
                worksheet.write(data_rows, 3, rec['data_performance']['break_time'], highlight_format)
                worksheet.write(data_rows, 4, rec['data_performance']['visited'], highlight_format)
                worksheet.write(data_rows, 5, rec['data_performance']['visit_time'], highlight_format)
                worksheet.write(data_rows, 6, rec['data_performance']['driving_time'], highlight_format)
                worksheet.write(data_rows, 7, rec['data_performance']['plan'], highlight_format)
                worksheet.write(data_rows, 8, rec['data_performance']['alert'], highlight_format)
                worksheet.write(data_rows, 9, rec['data_performance']['permission'], highlight_format)
                worksheet.write(data_rows, 10, rec['data_performance']['cancel'], highlight_format)
                worksheet.write(data_rows, 11, rec['data_performance']['packing_slip'], highlight_format)
            else:
                worksheet.write(data_rows, 3, 0, highlight_format)
                worksheet.write(data_rows, 4, 0, highlight_format)
                worksheet.write(data_rows, 5, 0, highlight_format)
                worksheet.write(data_rows, 6, 0, highlight_format)
                worksheet.write(data_rows, 7, 0, highlight_format)
                worksheet.write(data_rows, 8, 0, highlight_format)
                worksheet.write(data_rows, 9, 0, highlight_format)
                worksheet.write(data_rows, 10, 0, highlight_format)
                worksheet.write(data_rows, 11, 0, highlight_format)
            data_rows += 1
            if rec['plan_activity']:
                for pa in rec['plan_activity']:
                    if pa.get('start_time'):
                        worksheet.merge_range(
                            'A{0}:B{0}'.format(data_rows + 1),
                            "START: {0}".format(
                                pa['location_name'] if pa['location_name'] else "Other Location"
                            ),
                            merge_format_start_end
                        )
                        worksheet.merge_range(
                            'C{0}:H{0}'.format(data_rows + 1),
                            pa['location_address'] if pa['location_address'] else "",
                            merge_format_start_end
                        )
                        worksheet.merge_range(
                            'I{0}:L{0}'.format(data_rows + 1),
                            "TIME: {0}".format(
                                pa['start_time'] if pa['start_time'] else ""
                            ),
                            merge_format_start_end
                        )
            else:
                worksheet.merge_range(
                    'A{0}:B{0}'.format(data_rows + 1),
                    "START: {0}".format(
                        rec['start_route_branch']['name'] if rec['start_route_branch'].get('name') else ""
                    ),
                    merge_format_start_end
                )
                worksheet.merge_range(
                    'C{0}:H{0}'.format(data_rows + 1),
                    rec['start_route_branch']['address'] if rec['start_route_branch'].get('address') else "",
                    merge_format_start_end
                )
                worksheet.merge_range(
                    'I{0}:L{0}'.format(data_rows + 1),
                    "TIME: ",
                    merge_format_start_end
                )
            data_rows += 1
            if rec['destination']:
                # Title
                worksheet.merge_range('A{0}:B{0}'.format(data_rows + 1), "Customer Code", merge_format)
                worksheet.merge_range('C{0}:D{0}'.format(data_rows + 1), "Customer Name", merge_format)
                worksheet.merge_range('E{0}:F{0}'.format(data_rows + 1), "Address", merge_format)
                worksheet.merge_range('G{0}:H{0}'.format(data_rows + 1), "Check IN", merge_format)
                worksheet.merge_range('I{0}:J{0}'.format(data_rows + 1), "Check OUT", merge_format)
                worksheet.merge_range('K{0}:L{0}'.format(data_rows + 1), "Summary", merge_format)
                data_rows += 1
                for data_rec in rec['destination']:
                    address = []
                    # Body
                    worksheet.merge_range('A{0}:B{0}'.format(data_rows + 1), data_rec['customer_code'])
                    worksheet.merge_range('C{0}:E{0}'.format(data_rows + 1), data_rec['customer_name'])
                    address.append(data_rec['address'])
                    if data_rec['summary']:
                        if data_rec['summary'].get('notes'):
                            worksheet.merge_range('K{0}:L{0}'.format(data_rows + 1), data_rec['summary']['notes'])
                        else:
                            worksheet.merge_range('K{0}:L{0}'.format(data_rows + 1), "")
                    else:
                        worksheet.merge_range('K{0}:L{0}'.format(data_rows + 1), "")
                    # if rec['data_activity'].get(data_rec['customer_code']):
                    #     if rec['data_activity'][data_rec['customer_code']].get("in_time"):
                    #         worksheet.merge_range('I{0}:J{0}'.format(data_rows + 1),
                    #                               rec['data_activity'][data_rec['customer_code']]["in_time"])
                    #     else:
                    #         worksheet.merge_range('I{0}:J{0}'.format(data_rows + 1), "")
                    #     if rec['data_activity'][data_rec['customer_code']].get("out_time"):
                    #         worksheet.merge_range('K{0}:L{0}'.format(data_rows + 1),
                    #                               rec['data_activity'][data_rec['customer_code']]["out_time"])
                    #     else:
                    #         worksheet.merge_range('K{0}:L{0}'.format(data_rows + 1), "")
                    # else:
                    #     worksheet.merge_range('I{0}:J{0}'.format(data_rows + 1), "")
                    #     worksheet.merge_range('K{0}:L{0}'.format(data_rows + 1), "")
                    if rec['plan_activity']:
                        in_time_list = []
                        out_time_list = []
                        for pa in rec['plan_activity']:
                            if pa['nfc_code'] == data_rec['customer_code']:
                                # print(pa)
                                if pa['in_time']:
                                    in_time_list.append(pa['in_time'])
                                if pa['out_time']:
                                    out_time_list.append(pa['out_time'])
                                if pa['in_location_custom']:
                                    address.append(pa['in_location_name'])
                                if pa['out_location_custom']:
                                    address.append(pa['out_location_name'])
                        worksheet.merge_range('G{0}:H{0}'.format(data_rows + 1), ", ".join(in_time_list))
                        worksheet.merge_range('I{0}:J{0}'.format(data_rows + 1), ", ".join(out_time_list))
                    else:
                        worksheet.merge_range('G{0}:H{0}'.format(data_rows + 1), "")
                        worksheet.merge_range('I{0}:J{0}'.format(data_rows + 1), "")
                    worksheet.merge_range('E{0}:F{0}'.format(data_rows + 1), " | ".join(address))
                    data_rows += 1

            if rec['plan_activity']:
                for pa in rec['plan_activity']:
                    if pa.get('stop_time'):
                        worksheet.merge_range(
                            'A{0}:B{0}'.format(data_rows + 1),
                            "END: {0}".format(
                                pa['location_name'] if pa['location_name'] else "Other Location"
                            ),
                            merge_format_start_end
                        )
                        worksheet.merge_range(
                            'C{0}:H{0}'.format(data_rows + 1),
                            pa['location_address'] if pa['location_address'] else "",
                            merge_format_start_end
                        )
                        worksheet.merge_range(
                            'I{0}:L{0}'.format(data_rows + 1),
                            "TIME: {0}".format(
                                pa['stop_time'] if pa['stop_time'] else ""
                            ),
                            merge_format_start_end
                        )
            else:
                worksheet.merge_range(
                    'A{0}:B{0}'.format(data_rows + 1),
                    "END: {0}".format(
                        rec['end_route_branch']['name'] if rec['end_route_branch'].get('name') else ""
                    ),
                    merge_format_start_end
                )
                worksheet.merge_range(
                    'C{0}:H{0}'.format(data_rows + 1),
                    rec['end_route_branch']['address'] if rec['end_route_branch'].get('address') else "",
                    merge_format_start_end
                )
                worksheet.merge_range(
                    'I{0}:L{0}'.format(data_rows + 1),
                    "TIME: ",
                    merge_format_start_end
                )
            data_rows += 1
        workbook.close()
        output.seek(0)

        result_data['data'] = data
        result_data['file'] = output

        return result_data

    def get_all_export_pdf_activity_data_by_delivery_plan(
            self, page: int, limit: int, search: str, column: str, direction: str, branch_privilege: list,
            data_filter: list
    ):
        """
        Get List Of visit cycle
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: branch_privilige: list
        :param: division_privilige: list
        :return:
            Visit Cycle Object
        """
        result_data = {}
        cycle = {}
        data = []
        start = page * limit - limit
        order = ''
        where = """WHERE (dp.is_approval = 1 AND dp.is_deleted = 0) 
                AND (u.branch_id IN ({0})) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        where_original = where
        if column:
            if column == 'start_branch':
                order = """ORDER BY b1.name {0}""".format(direction)
            elif column == 'end_branch':
                order = """ORDER BY b2.name {0}""".format(direction)
            elif column == 'username':
                order = """ORDER BY u.username {0}""".format(direction)
            elif column == 'user':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY br.name {0}""".format(direction)
            else:
                order = """ORDER BY dp.{0} {1}""".format(column, direction)
        select = "dp.*"
        select_count = "dp.id"
        join = """as dp LEFT JOIN `users` as u ON dp.user_id = u.id 
                LEFT JOIN `employee` as e ON u.employee_id = e.id
                LEFT JOIN `branches` as br ON u.branch_id = br.id
                LEFT JOIN `branches` as b1 ON dp.start_route_branch_id = b1.id
                LEFT JOIN `branches` as b2 ON dp.end_route_branch_id = b2.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR br.name LIKE '%{0}%' OR b1.name LIKE '%{0}%' 
                    OR b2.name LIKE '%{0}%' OR e.name LIKE '%{0}%') """.format(search)
        if data_filter:
            tmp_data_filter = data_filter[0]
            if tmp_data_filter['start_date']:
                where += """AND (dp.date >= '{0} 00:00:00' AND dp.date <= '{1} 23:59:59') """.format(
                    tmp_data_filter['start_date'], tmp_data_filter['end_date']
                )
            if tmp_data_filter['user_id']:
                where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['user_id']))
            if tmp_data_filter['branch_id']:
                where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['branch_id']))
        delivery_plan_data = self.delivery_plan_model.get_all_delivery_plan(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.delivery_plan_model.get_count_all_delivery_plan(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.delivery_plan_model.get_count_all_delivery_plan(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if delivery_plan_data:
            for vp in delivery_plan_data:
                list_customer = []
                if vp['edit_data'] is not None:
                    vp['edit_data'] = json.loads(vp['edit_data'])
                if vp['date'] is not None:
                    vp['date'] = str(vp['date'])
                if vp['create_date'] is not None:
                    vp['create_date'] = str(vp['create_date'])
                if vp['update_date'] is not None:
                    vp['update_date'] = str(vp['update_date'])
                # Get Activity data
                data_activity_dict = dict()
                data_activity = []
                list_nfc_code = []

                plan_activity = []
                try:
                    # where = """WHERE (sa.id IN (SELECT MIN(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'START'
                    # GROUP BY user_id, delivery_plan_id, nfc_code) OR sa.id IN (SELECT MAX(id) FROM `logistic_activity`
                    # WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, delivery_plan_id, nfc_code) OR sa.id IN (SELECT MIN(id)
                    # FROM `logistic_activity` WHERE `tap_nfc_type` = 'IN' GROUP BY user_id, delivery_plan_id, nfc_code)
                    # OR sa.id IN (SELECT MAX(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'OUT'
                    # GROUP BY user_id, delivery_plan_id, nfc_code)) AND (delivery_plan_id = {0}) """.format(
                    #     vp['id'])

                    # query without grouping
                    where = """WHERE (
                            sa.id IN (SELECT MIN(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'START' GROUP BY user_id, delivery_plan_id, nfc_code) OR 
                            sa.id IN (SELECT MAX(id) FROM `logistic_activity` WHERE `tap_nfc_type` = 'STOP' GROUP BY user_id, delivery_plan_id, nfc_code) OR 
                            sa.id IN (SELECT id FROM `logistic_activity` WHERE `tap_nfc_type` = 'IN' ) OR 
                            sa.id IN (SELECT id FROM `logistic_activity` WHERE `tap_nfc_type` = 'OUT')
                        ) AND (delivery_plan_id = {0})""".format(vp['id'])

                    order = ""
                    select = "sa.*"
                    join = """AS sa"""
                    activity_data = self.logistic_activity_model.get_all_activity(
                        self.cursor, select=select, join=join, where=where, order=order, start=0, limit=1000
                    )

                    # Process data for Plan Activity key-> plan_activity
                    if activity_data:
                        for ad in activity_data:
                            if ad['tap_nfc_date'] is not None:
                                ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                            if ad['create_date'] is not None:
                                ad['create_date'] = str(ad['create_date'])
                            if ad['update_date'] is not None:
                                ad['update_date'] = str(ad['update_date'])

                            ad['branch_name'] = None
                            ad['branch_location'] = None
                            if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                                if ad['nfc_code'] is not None:
                                    try:
                                        branch = self.branch_model.get_branches_by_id(self.cursor, ad['nfc_code'])[0]
                                        ad['branch_name'] = branch['name']
                                        ad['branch_location'] = branch['address']
                                    except:
                                        ad['branch_name'] = None
                                        ad['branch_location'] = None
                                if ad['route_breadcrumb'] is not None:
                                    ad['route_breadcrumb'] = json.loads(ad['route_breadcrumb'])

                            ad['customer_code'] = None
                            ad['customer_name'] = None
                            ad['customer_address'] = None
                            if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                                if ad['nfc_code'] is not None:
                                    ad['customer_code'] = ad['nfc_code']
                                    try:
                                        customer = self.customer_model.get_customer_by_code(
                                            self.cursor, ad['nfc_code']
                                        )[0]
                                        ad['customer_name'] = customer['name']
                                        ad['customer_address'] = customer['address']
                                    except:
                                        ad['customer_name'] = None
                                        ad['customer_address'] = None
                                if ad['route_breadcrumb'] is not None:
                                    ad['route_breadcrumb'] = json.loads(ad['route_breadcrumb'])

                            if ad['user_id'] is not None:
                                try:
                                    ad['user'] = self.user_model.get_user_by_id(
                                        self.cursor, ad['user_id'],
                                        select="username, employee_id, branch_id, division_id"
                                    )[0]
                                    if ad['user']['employee_id'] is not None:
                                        try:
                                            ad['user']['name'] = self.employee_model.get_employee_by_id(
                                                self.cursor,
                                                ad['user']['employee_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['name'] = None
                                    if ad['user']['branch_id'] is not None:
                                        try:
                                            ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                self.cursor,
                                                ad['user']['branch_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['branch_name'] = None
                                    if ad['user']['division_id'] is not None:
                                        try:
                                            ad['user']['division_name'] = self.division_model.get_division_by_id(
                                                self.cursor, ad['user']['division_id'], select="division_name")[0][
                                                'division_name']
                                        except:
                                            ad['user']['division_name'] = None
                                except:
                                    ad['user'] = {}
                            else:
                                ad['user'] = {}
                            plan_activity.append(ad)

                    if plan_activity:
                        plan_activity_list = []
                        for rec in plan_activity:
                            plan_activity_dict = dict()
                            # print("======== Plan Activity {0}".format(rec))
                            if rec['tap_nfc_type'] == 'START':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = 0
                                plan_activity_dict['start_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['start_location_custom'] = False
                                    plan_activity_dict['start_location_name'] = rec['branch_name']
                                    plan_activity_dict['start_location_address'] = rec['branch_location']
                                else:
                                    # custom start
                                    plan_activity_dict['start_location_custom'] = True
                                    plan_activity_dict['start_location_name'] = None
                                    plan_activity_dict['start_location_address'] = rec['route_breadcrumb']['address']
                                plan_activity_dict['start_location'] = rec['route_breadcrumb']

                            if rec['tap_nfc_type'] == 'STOP':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = 0
                                plan_activity_dict['stop_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['stop_location_custom'] = False
                                    plan_activity_dict['stop_location_name'] = rec['branch_name']
                                    plan_activity_dict['stop_location_address'] = rec['branch_location']
                                else:
                                    # custom stop
                                    plan_activity_dict['stop_location_custom'] = True
                                    plan_activity_dict['stop_location_name'] = None
                                    plan_activity_dict['stop_location_address'] = rec['route_breadcrumb']['address']
                                plan_activity_dict['stop_location'] = rec['route_breadcrumb']

                            if rec['tap_nfc_type'] == 'IN':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['distance'] = rec['distance']
                                plan_activity_dict['in_time'] = rec['tap_nfc_date']
                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['in_location_custom'] = False
                                    plan_activity_dict['in_location_name'] = rec['customer_name']
                                    plan_activity_dict['in_location_address'] = rec['customer_address']
                                else:
                                    # custom checkin
                                    plan_activity_dict['in_location_custom'] = True
                                    plan_activity_dict['in_location_name'] = rec['customer_name']
                                    plan_activity_dict['in_location_address'] = rec['route_breadcrumb']['address']

                            if rec['tap_nfc_type'] == 'OUT':
                                plan_activity_dict['tap_nfc_type'] = rec['tap_nfc_type']
                                plan_activity_dict['nfc_code'] = rec['nfc_code']
                                plan_activity_dict['out_time'] = rec['tap_nfc_date']

                                if rec['route_breadcrumb'] is None:
                                    plan_activity_dict['out_location_custom'] = False
                                    plan_activity_dict['out_location_name'] = rec['customer_name']
                                    plan_activity_dict['out_location_address'] = rec['customer_address']
                                else:
                                    # custom checkout
                                    plan_activity_dict['out_location_custom'] = True
                                    plan_activity_dict['out_location_name'] = rec['customer_name']
                                    plan_activity_dict['out_location_address'] = rec['route_breadcrumb']['address']

                            plan_activity_list.append(plan_activity_dict)
                        plan_result = []
                        i = 0
                        for plan in plan_activity_list:
                            data_dict = dict()
                            if plan.get('start_time'):
                                data_dict['nfc_code'] = plan['nfc_code']
                                data_dict['start_time'] = plan['start_time']
                                data_dict['location_name'] = plan['start_location_name']
                                data_dict['location_address'] = plan['start_location_address']
                                data_dict['location_custom'] = plan['start_location_custom']
                                data_dict['distance'] = plan['distance']
                                data_dict['duration'] = 0

                            if plan.get('in_time'):
                                code = plan['nfc_code']
                                data_dict['nfc_code'] = code
                                data_dict['in_time'] = plan['in_time']
                                data_dict['distance'] = plan['distance']
                                data_dict['in_location_address'] = plan['in_location_address']
                                data_dict['in_location_name'] = plan['in_location_name']
                                data_dict['in_location_custom'] = plan['in_location_custom']
                                next_idx = i
                                next = next_idx + 1
                                if plan_activity_list[next]['nfc_code'] == code and plan_activity_list[next][
                                    'tap_nfc_type'] == 'OUT':
                                    # Tap Type STOP found
                                    data_dict['out_time'] = plan_activity_list[next]['out_time']
                                    data_dict['out_location_address'] = plan_activity_list[next]['out_location_address']
                                    data_dict['out_location_name'] = plan_activity_list[next]['out_location_name']
                                    data_dict['out_location_custom'] = plan_activity_list[next]['out_location_custom']

                                    # calculate duration
                                    out_time = datetime.strptime(data_dict['out_time'], "%Y-%m-%d %H:%M:%S")
                                    in_time = datetime.strptime(data_dict['in_time'], "%Y-%m-%d %H:%M:%S")
                                    if out_time > in_time:
                                        data_dict['duration'] = int((out_time - in_time).seconds / 60)
                                    else:
                                        data_dict['duration'] = 0
                                else:
                                    data_dict['out_time'] = None
                                    data_dict['out_location_address'] = None
                                    data_dict['out_location_name'] = None
                                    data_dict['out_location_custom'] = False
                                    data_dict['duration'] = 0

                            if plan.get('stop_time'):
                                data_dict['nfc_code'] = plan['nfc_code']
                                data_dict['stop_time'] = plan['stop_time']
                                data_dict['location_name'] = plan['stop_location_name']
                                data_dict['location_address'] = plan['stop_location_address']
                                data_dict['location_custom'] = plan['stop_location_custom']
                                data_dict['distance'] = plan['distance']
                                data_dict['duration'] = 0

                            if data_dict:
                                plan_result.append(data_dict)
                            i += 1

                        # calculate time range between activity
                        # and add key order
                        position = 0
                        if plan_result:
                            for plan in plan_result:
                                plan['order'] = position
                                if plan.get('start_time') and position == 0:
                                    plan['time_range'] = 0
                                else:
                                    if plan.get('in_time'):
                                        next_time = plan['in_time']
                                    elif plan.get('stop_time'):
                                        next_time = plan['stop_time']
                                    else:
                                        next_time = 0

                                    post = position
                                    index = post - 1
                                    if index >= 0:
                                        if plan_result[index].get('start_time'):
                                            prev_time = plan_result[index]['start_time']
                                        elif plan_result[index].get('out_time'):
                                            prev_time = plan_result[index]['out_time']
                                        else:
                                            prev_time = 0
                                    else:
                                        prev_time = 0

                                    if prev_time and next_time:
                                        prev_time_fmt = datetime.strptime(prev_time, "%Y-%m-%d %H:%M:%S")
                                        next_time_fmt = datetime.strptime(next_time, "%Y-%m-%d %H:%M:%S")
                                        if next_time_fmt > prev_time_fmt:
                                            plan['time_range'] = int((next_time_fmt - prev_time_fmt).seconds / 60)
                                        else:
                                            plan['time_range'] = 0
                                    else:
                                        plan['time_range'] = 0
                                position += 1
                            # print("result Plan Activity = {0}".format(plan_result))
                        vp['plan_activity'] = plan_result
                    else:
                        vp['plan_activity'] = []

                    # Process data for data Activity key-> data_activity
                    # previous process before ignore grouping
                    if activity_data:
                        for ad in activity_data:
                            if ad['tap_nfc_date'] is not None:
                                ad['tap_nfc_date'] = str(ad['tap_nfc_date'])
                            if ad['create_date'] is not None:
                                ad['create_date'] = str(ad['create_date'])
                            if ad['update_date'] is not None:
                                ad['update_date'] = str(ad['update_date'])
                            ad['branch_name'] = None
                            if ad['tap_nfc_type'] == 'START' or ad['tap_nfc_type'] == 'STOP':
                                if ad['nfc_code'] is not None:
                                    try:
                                        ad['branch_name'] = self.branch_model.get_branches_by_id(
                                            self.cursor, ad['nfc_code'], select="""name"""
                                        )[0]['name']
                                    except:
                                        ad['branch_name'] = None
                            ad['customer_code'] = None
                            if ad['tap_nfc_type'] == 'IN' or ad['tap_nfc_type'] == 'OUT':
                                if ad['nfc_code'] is not None:
                                    ad['customer_code'] = ad['nfc_code']
                            if ad['user_id'] is not None:
                                try:
                                    ad['user'] = self.user_model.get_user_by_id(
                                        self.cursor, ad['user_id'],
                                        select="username, employee_id, branch_id, division_id"
                                    )[0]
                                    if ad['user']['employee_id'] is not None:
                                        try:
                                            ad['user']['name'] = self.employee_model.get_employee_by_id(
                                                self.cursor,
                                                ad['user']['employee_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['name'] = None
                                    if ad['user']['branch_id'] is not None:
                                        try:
                                            ad['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                                self.cursor,
                                                ad['user']['branch_id'],
                                                select="""name""")[0]['name']
                                        except:
                                            ad['user']['branch_name'] = None
                                    if ad['user']['division_id'] is not None:
                                        try:
                                            ad['user']['division_name'] = self.division_model.get_division_by_id(
                                                self.cursor, ad['user']['division_id'], select="division_name")[0][
                                                'division_name']
                                        except:
                                            ad['user']['division_name'] = None
                                except:
                                    ad['user'] = {}
                            else:
                                ad['user'] = {}
                            if ad['nfc_code'] is not None:
                                data_activity_dict[ad['nfc_code']] = dict()
                                list_nfc_code.append(ad['nfc_code'])
                            data_activity.append(ad)
                    if data_activity:
                        plan_activity_list = []
                        for rec in data_activity:
                            plan_activity_dict = dict()
                            if rec['tap_nfc_type'] == 'START':
                                data_activity_dict[rec['nfc_code']]['start_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = 0
                            if rec['tap_nfc_type'] == 'STOP':
                                data_activity_dict[rec['nfc_code']]['stop_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = 0
                            if rec['tap_nfc_type'] == 'IN':
                                data_activity_dict[rec['nfc_code']]['in_time'] = rec['tap_nfc_date']
                                data_activity_dict[rec['nfc_code']]['distance'] = rec['distance']
                            if rec['tap_nfc_type'] == 'OUT':
                                data_activity_dict[rec['nfc_code']]['out_time'] = rec['tap_nfc_date']

                        # Calculation duration
                        unique_code = set(list_nfc_code)
                        for code in unique_code:
                            if data_activity_dict[code].get('in_time'):
                                in_time = data_activity_dict[code]['in_time']
                            else:
                                in_time = 0
                            if data_activity_dict[code].get('out_time'):
                                out_time = data_activity_dict[code]['out_time']
                            else:
                                out_time = 0
                            if in_time and out_time:
                                out_time_fmt = datetime.strptime(out_time, "%Y-%m-%d %H:%M:%S")
                                in_time_fmt = datetime.strptime(in_time, "%Y-%m-%d %H:%M:%S")
                                data_activity_dict[code]['duration'] = int((out_time_fmt - in_time_fmt).seconds / 60)
                            else:
                                data_activity_dict[code]['duration'] = 0

                    vp['data_activity'] = data_activity_dict
                except Exception as e:
                    print(e)
                    vp['data_activity'] = dict()
                    vp['plan_activity'] = []

                # Get Data Performance
                try:
                    performance_date = vp['date'].split(" ")
                    performance_date = performance_date[0]
                    data_performance = self.get_statistic_performance_by_user_id(
                        job_function='logistic', user_ids=[vp['user_id']], start_date=performance_date,
                        end_date=performance_date, plan_id=vp['id']
                    )

                    # vp['data_performance'] = data_performance

                    # TODO Get Data Total Distance
                    select = "*"
                    where_distance = """WHERE user_id={0} AND tap_nfc_type='STOP' """.format(vp['user_id'])
                    where_distance += """AND delivery_plan_id={} """.format(vp['id'])
                    where_distance += """AND (tap_nfc_date >= '{0} 00:00:00' AND tap_nfc_date <= '{1} 23:59:59') """.format(
                        performance_date, performance_date)
                    order = 'ORDER BY create_date ASC'
                    data_distance = self.logistic_activity_model.get_all_activity(self.cursor, select=select,
                                                                                  where=where_distance, order=order)
                    total_distance = 0
                    if data_distance:
                        for rec_distance in data_distance:
                            total_distance += rec_distance['total_distance']
                    data_performance['total_distance'] = total_distance

                    vp['data_performance'] = data_performance
                except Exception as e:
                    print(e)
                    vp['data_performance'] = dict()
                if vp['destination_order'] is not None:
                    vp['destination_order'] = json.loads(vp['destination_order'])
                if vp['destination'] is not None:
                    vp['destination'] = json.loads(vp['destination'])
                    idx = 0
                    for rec in vp['destination']:
                        try:
                            customer = self.customer_model.get_customer_by_id(
                                self.cursor, rec['customer_code'],
                                select="name, email, phone, address, lng, lat, nfcid, contacts, business_activity")[0]
                            vp['destination'][idx]['customer_name'] = customer['name']
                            vp['destination'][idx]['customer_email'] = customer['email']
                            vp['destination'][idx]['phone'] = customer['phone']
                            vp['destination'][idx]['address'] = customer['address']
                            vp['destination'][idx]['lng'] = customer['lng']
                            vp['destination'][idx]['lat'] = customer['lat']
                            vp['destination'][idx]['nfcid'] = customer['nfcid']
                            if customer['contacts'] is not None:
                                vp['destination'][idx]['contacts'] = json.loads(customer['contacts'])
                            else:
                                vp['destination'][idx]['contacts'] = None
                            if customer['business_activity'] is not None:
                                vp['destination'][idx]['business_activity'] = json.loads(customer['business_activity'])
                            else:
                                vp['destination'][idx]['business_activity'] = None
                            try:
                                summary = self.visit_plan_summary_model.get_visit_plan_summary_by_plan_id_customer_code(
                                    self.cursor, vp['id'], rec['customer_code']
                                )
                                if len(summary) == 0:
                                    vp['destination'][idx]['summary'] = None
                                else:
                                    summary = summary[0]
                                    del summary['visit_images']
                                    del summary['competitor_images']
                                    if summary['create_date'] is not None:
                                        summary['create_date'] = str(summary['create_date'])
                                    if summary['update_date'] is not None:
                                        summary['update_date'] = str(summary['update_date'])
                                    vp['destination'][idx]['summary'] = summary
                            except:
                                vp['destination'][idx]['summary'] = None
                        except:
                            vp['destination'][idx]['customer_name'] = None
                            vp['destination'][idx]['customer_email'] = None
                            vp['destination'][idx]['phone'] = None
                            vp['destination'][idx]['address'] = None
                            vp['destination'][idx]['lng'] = None
                            vp['destination'][idx]['lat'] = None
                            vp['destination'][idx]['nfcid'] = None
                            vp['destination'][idx]['contacts'] = None
                            vp['destination'][idx]['business_activity'] = None
                            vp['destination'][idx]['summary'] = None
                        list_customer.append(rec['customer_code'])
                        idx += 1
                # vc['customer'] = list_customer
                vp['total_customer'] = len(set(list_customer))
                if vp['user_id'] is not None:
                    try:
                        vp['user'] = self.user_model.get_user_by_id(
                            self.cursor, vp['user_id'], select="username, employee_id, branch_id")[0]
                    except:
                        vp['user'] = {}
                    if vp['user']['employee_id'] is not None:
                        try:
                            vp['user']['name'] = self.employee_model.get_employee_by_id(
                                self.cursor, vp['user']['employee_id'], select="""name""")[0]['name']
                        except:
                            vp['user']['name'] = None
                    if vp['user']['branch_id'] is not None:
                        try:
                            vp['user']['branch_name'] = self.branch_model.get_branches_by_id(
                                self.cursor, vp['user']['branch_id'], select="""name""")[0]['name']
                        except:
                            vp['user']['branch_name'] = None
                else:
                    vp['user'] = {}
                if vp['start_route_branch_id'] is not None:
                    try:
                        vp['start_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, vp['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        vp['start_route_branch'] = {}
                else:
                    vp['start_route_branch'] = {}
                if vp['end_route_branch_id'] is not None:
                    try:
                        vp['end_route_branch'] = self.branch_model.get_branches_by_id(
                            self.cursor, vp['start_route_branch_id'], select="name, phone, address, email, lng, lat")[0]
                    except:
                        vp['end_route_branch'] = {}
                else:
                    vp['end_route_branch'] = {}
                del vp['route']
                # vp['total_invoice'] = 2
                # vp['invoice_ids'] = ["SO-PSCN000005850", "SO-PSCN000005776"]
                data.append(vp)

        if data_filter:
            data_filter = data_filter[0]
            if data_filter['start_date'] and not data_filter['user_id']:
                head_title = 'DELIVERY PLAN (USER: ALL, TANGGAL: {0} s/d {1})'.format(
                    data_filter['start_date'], data_filter['end_date']
                )
            elif data_filter['user_id'] and not data_filter['start_date']:
                head_title = 'DELIVERY PLAN (USER: {0}, TANGGAL: ALL)'.format(
                    ", ".join(x for x in data_filter['username'])
                )
            else:
                head_title = 'DELIVERY PLAN (USER: {0}, TANGGAL: {1} s/d {2})'.format(
                    ", ".join(x for x in data_filter['username']), data_filter['start_date'],
                    data_filter['end_date']
                )
        else:
            head_title = 'DELIVERY PLAN (USER: ALL, TANGGAL: ALL)'

        # head_table = OrderedDict()
        # head_table['tanggal'] = "TANGGAL"
        # head_table['sales'] = "SALES REP"
        # head_table['branch'] = "BRANCH"
        # head_table['division'] = "DIVISION"
        # head_table['break_time'] = "BREAK TIME (Minutes)"
        # head_table['visited'] = "VISITED"
        # head_table['visit_time'] = "VISIT TIME (Minutes)"
        # head_table['driving_time'] = "DRIVING TIME (Minutes)"
        # head_table['plan'] = "PLAN"
        # head_table['alert'] = "ALERT"
        # head_table['permission'] = "PERMISSION"
        # head_table['cancel'] = "CANCEL"
        # head_table['invoice'] = "INVOICE"
        # Title Customer
        # head_customer_table = OrderedDict()
        # head_customer_table['code'] = "Customer Code"
        # head_customer_table['name'] = "Customer Name"
        # head_customer_table['address'] = "Address"
        # head_customer_table['in'] = "Tap IN"
        # head_customer_table['out'] = "Tap OUT"
        body_table = []
        for rec in data:
            data_body = OrderedDict()
            data_body['tanggal'] = rec['date']
            data_body['driver'] = rec['user']['name']
            data_body['branch'] = rec['user']['branch_name']
            if len(rec['data_performance']) is not 0:
                data_body['break_time'] = rec['data_performance']['break_time']
                data_body['visited'] = rec['data_performance']['visited']
                data_body['visit_time'] = rec['data_performance']['visit_time']
                data_body['driving_time'] = rec['data_performance']['driving_time']
                data_body['plan'] = rec['data_performance']['plan']
                data_body['alert'] = rec['data_performance']['alert']
                data_body['permission'] = rec['data_performance']['permission']
                data_body['cancel'] = rec['data_performance']['cancel']
                data_body['invoice'] = rec['data_performance']['packing_slip']  # Get start time in branch
            else:
                data_body['break_time'] = 0
                data_body['visited'] = 0
                data_body['visit_time'] = 0
                data_body['driving_time'] = 0
                data_body['plan'] = 0
                data_body['alert'] = 0
                data_body['permission'] = 0
                data_body['cancel'] = 0
                data_body['invoice'] = 0
            if rec['plan_activity']:
                for pa in rec['plan_activity']:
                    if pa.get('start_time'):
                        data_body['start_branch'] = {
                            'code': rec['start_route_branch_id'],
                            'name': pa['location_name'] if pa['location_name'] else "Other Location",
                            'address': pa['location_address'] if pa['location_address'] else "",
                            'in': pa['start_time'] if pa['start_time'] else "",
                            'out': ""
                        }
            else:
                if (rec['start_route_branch_id'] is not None) and (len(rec['start_route_branch']) is not 0):
                    data_body['start_branch'] = {
                        'code': rec['start_route_branch_id'],
                        'name': rec['start_route_branch']['name'],
                        'address': rec['start_route_branch']['address'],
                        'in': "",
                        'out': ""
                    }
                else:
                    data_body['start_branch'] = {
                        'code': None,
                        'name': "Unknown",
                        'address': "Unknown",
                        'in': "",
                        'out': ""
                    }
            # Get stop time in branch
            if rec['plan_activity']:
                for pa in rec['plan_activity']:
                    if pa.get('stop_time'):
                        data_body['end_branch'] = {
                            'code': rec['end_route_branch_id'],
                            'name': pa['location_name'] if pa['location_name'] else "Other Location",
                            'address': pa['location_address'] if pa['location_address'] else "",
                            'in': "",
                            'out': pa['stop_time'] if pa['stop_time'] else ""
                        }
                    else:
                        data_body['end_branch'] = {
                            'code': rec['end_route_branch_id'],
                            'name': "Other Location",
                            'address': "",
                            'in': "",
                            'out': ""
                        }
            else:
                data_body['end_branch'] = {
                    'code': rec['end_route_branch_id'],
                    'name': rec['end_route_branch']['name'],
                    'address': rec['end_route_branch']['address'],
                    'in': "",
                    'out': ""
                }
                # if (rec['end_route_branch_id'] is not None) and (len(rec['end_route_branch']) is not 0):
                #     data_body['end_branch'] = {
                #         'code': rec['end_route_branch_id'],
                #         'name': rec['end_route_branch']['name'],
                #         'address': rec['end_route_branch']['address'],
                #         'in': "",
                #         'out': ""
                #     }
                # else:
                #     data_body['end_branch'] = {
                #         'code': None,
                #         'name': "Unknown",
                #         'address': "Unknown",
                #         'in': "",
                #         'out': ""
                #     }
            data_body['customer'] = []
            if rec['destination']:
                for data_rec in rec['destination']:
                    address = []
                    data_customer_body = OrderedDict()
                    # Body
                    data_customer_body['code'] = data_rec['customer_code']
                    data_customer_body['name'] = data_rec['customer_name']
                    address.append(data_rec['address'])
                    if data_rec['summary']:
                        if data_rec['summary'].get('notes'):
                            data_customer_body['summary'] = data_rec['summary']['notes']
                        else:
                            data_customer_body['summary'] = ""
                    else:
                        data_customer_body['summary'] = ""
                    # if rec['data_activity'].get(data_rec['customer_code']):
                    #     if rec['data_activity'][data_rec['customer_code']].get("in_time"):
                    #         data_customer_body['in'] = rec['data_activity'][data_rec['customer_code']]["in_time"]
                    #     else:
                    #         data_customer_body['in'] = ""
                    #     if rec['data_activity'][data_rec['customer_code']].get("out_time"):
                    #         data_customer_body['out'] = rec['data_activity'][data_rec['customer_code']]["out_time"]
                    #     else:
                    #         data_customer_body['out'] = ""
                    # else:
                    #     data_customer_body['in'] = ""
                    #     data_customer_body['out'] = ""

                    in_time_list = []
                    out_time_list = []
                    if rec['plan_activity']:
                        for pa in rec['plan_activity']:
                            if pa['nfc_code'] == data_rec['customer_code']:
                                if pa['in_time']:
                                    in_time_list.append(pa['in_time'])
                                if pa['out_time']:
                                    out_time_list.append(pa['out_time'])
                                if pa['in_location_custom']:
                                    address.append(pa['in_location_name'])
                                if pa['out_location_custom']:
                                    address.append(pa['out_location_name'])
                    data_customer_body['address'] = " | ".join(address)
                    data_customer_body['in'] = ", ".join(in_time_list)
                    data_customer_body['out'] = ", ".join(out_time_list)
                    data_body['customer'].append(data_customer_body)
            body_table.append(data_body)
        # rendered = render_template(
        #     'report_template.html', head_title=head_title, head_table=head_table,
        #     head_customer_table=head_customer_table, body_table=body_table, category="sales"
        # )
        rendered = render_template(
            'report_activity_template.html', head_title=head_title, body_table=body_table, category="logistic"
        )
        output = pdfkit.from_string(rendered, False)

        result_data['data'] = data
        result_data['file'] = output

        return result_data

    def create_break_time(self, create_data: 'dict', user_id: 'int'):
        """
        Function for create new log activity

        :param create_data: dict
        :param user_id: int
        :return:
            Success or failure message
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.break_time_model.insert_into_db(
                self.cursor, user_id=user_id, visit_plan_id=create_data['visit_plan_id'],
                delivery_plan_id=create_data['delivery_plan_id'], break_time=create_data['break_time'],
                create_date=today, update_date=today
            )
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def create_idle_time(self, create_data: 'dict', user_id: 'int'):
        """
        Function for create new log activity

        :param create_data: dict
        :param user_id: int
        :return:
            Success or failure message
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.idle_time_model.insert_into_db(
                self.cursor, user_id=user_id, visit_plan_id=create_data['visit_plan_id'],
                delivery_plan_id=create_data['delivery_plan_id'],
                idle_time=create_data['idle_time'], create_date=today, update_date=today
            )
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def create_breadcrumb(self, create_data: 'dict', user_id: 'int'):
        """
        Function for create new log activity

        :param create_data: dict
        :param user_id: int
        :return:
            Success or failure message
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.lab_model.insert_into_db(
                self.cursor, user_id=user_id, delivery_plan_id=create_data['delivery_plan_id'],
                lat=create_data['lat'], lng=create_data['lng'], create_date=today, update_date=today
            )
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def get_all_breadcrumb_data(
            self, page: int, limit: int, search: str, column: str, direction: str, plan_id: int
    ):
        """
        Get List Of breadcrumb
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: plan_id: int
        :return:
            breadcrumb Object
        """
        cycle = {}
        data = []
        start = page * limit - limit
        order = ''
        where = """WHERE delivery_plan_id = {} """.format(plan_id)
        where_original = where
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        select = "*"
        select_count = "id"
        join = """"""
        # if search:
        #     where += """""".format(search)
        breadcrumb_data = self.lab_model.get_all_activity_breadcrumb(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.lab_model.get_count_all_activity_breadcrumb(
            self.cursor, select=select_count, join=join, where=where
        )
        count = self.lab_model.get_count_all_activity_breadcrumb(
            self.cursor, select=select_count, join=join, where=where_original
        )
        if breadcrumb_data:
            for bc in breadcrumb_data:
                data.append(bc)
        cycle['data'] = data
        cycle['total'] = count
        cycle['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if cycle['total_filter'] > page * limit:
            cycle['has_next'] = True
        else:
            cycle['has_next'] = False
        if limit <= page * count_filter - count_filter:
            cycle['has_prev'] = True
        else:
            cycle['has_prev'] = False
        return cycle

    def check_tap_activity(self, plan_id: 'int', user_id: 'int', customer_code: 'str'):
        """
        Function for create new log activity

        :param plan_id: int
        :param user_id: int
        :param customer_code: int
        :return:
            Success or failure message
        """
        # today = datetime.today()
        # today = today.strftime("%Y-%m-%d %H:%M:%S")
        start = 0
        limit = 1000
        select = "tap_nfc_type"
        where = """WHERE delivery_plan_id = {0} AND user_id = {1} 
        AND nfc_code = '{2}'""".format(plan_id, user_id, customer_code)
        order = "ORDER BY tap_nfc_date DESC"

        result = self.logistic_activity_model.get_all_activity(
            self.cursor, select=select, where=where, order=order, start=start, limit=limit
        )

        return result

    def check_tap_activity_by_delivery_plan(self, plan_id: 'int', user_id: 'int'):
        """
        Function for create new log activity

        :param plan_id: int
        :param user_id: int
        :return:
            Success or failure message
        """
        # today = datetime.today()
        # today = today.strftime("%Y-%m-%d %H:%M:%S")
        start = 0
        limit = 1000
        select = "*"
        where = """WHERE delivery_plan_id = {0} AND user_id = {1} """.format(plan_id, user_id)
        order = "ORDER BY tap_nfc_date DESC"

        result = self.logistic_activity_model.get_all_activity(
            self.cursor, select=select, where=where, order=order, start=start, limit=limit
        )

        return result

    def get_statistic_performance_by_user_id(
            self, job_function: str, user_ids: list, start_date: str, end_date: str, plan_id: int
    ):
        """

        :param job_function:str
        :param user_ids: list
        :param start_date: str
        :param end_date: str
        :param plan_id: int
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

        if plan_id:
            if job_function == 'sales':
                where_al += """ AND al.visit_plan_id={0} """.format(plan_id)
            else:
                where_al += """ AND al.delivery_plan_id={0} """.format(plan_id)

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

        if plan_id:
            if job_function == "sales":
                where_al += """ AND al.visit_plan_id={0} """.format(plan_id)
            else:
                where_al += """ AND al.delivery_plan_id={0} """.format(plan_id)

        group = """GROUP BY al.create_by"""
        count_permission = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_al, order=order, group=group
        )

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

        if plan_id:
            where_dp += """ AND dp.id={0} """.format(plan_id)

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

        if plan_id:
            where_dp += """ AND dp.id={0} """.format(plan_id)

        group = """GROUP BY dp.user_id"""
        count_plan_new_dest = self.delivery_plan_model.get_count_all_delivery_plan_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_dp, group=group
        )

        ## TODO: Get Statistitic Actual Plan
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
        #
        # if plan_id:
        #     where_dd += """ AND dd.delivery_plan_id={0} """.format(plan_id)
        #
        # group = """GROUP BY dd.user_id"""
        # count_actual = self.delivery_model.get_count_all_delivery_statistic(
        #     self.cursor, select=select, select_count=select_count, join=join, where=where_dd, group=group
        # )

        # TODO: Get Statistitic Actual Plan
        select = "u.id"
        select_from = """( SELECT act.* FROM (SELECT id, user_id, delivery_plan_id, 
                        REPLACE(nfc_code, " ", "") as nfc_code, tap_nfc_date, tap_nfc_type FROM logistic_activity) as act 
                        WHERE act.tap_nfc_type = 'IN' GROUP BY act.delivery_plan_id, act.nfc_code, act.tap_nfc_type )"""
        select_count = ", COUNT(la.id) as total"
        order = ''
        join = """as la LEFT JOIN `users` as u ON la.user_id = u.id """
        where_la = """WHERE la.user_id IN ({}) """.format(
            ", ".join(str(x) for x in user_ids)
        )
        if start_date and end_date:
            where_la += """AND (la.tap_nfc_date >= '{0} 00:00:00' AND la.tap_nfc_date <= '{1} 23:59:59') """.format(
                start_date, end_date
            )
        else:
            where_la += """AND (la.tap_nfc_date LIKE '{}%')""".format(today)

        if plan_id:
            where_la += """ AND la.delivery_plan_id={0} """.format(plan_id)

        group = """GROUP BY la.user_id"""
        count_actual = self.logistic_activity_model.get_count_all_activity_statistic(
            self.cursor, select=select, select_count=select_count, select_from=select_from, join=join,
            where=where_la, order=order, group=group
        )

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

        if plan_id:
            where_la += """ AND la.delivery_plan_id={0} """.format(plan_id)

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

        if plan_id:
            where_la += """ AND la.delivery_plan_id={0} """.format(plan_id)

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

        if plan_id:
            if job_function == "sales":
                where_bt += """ AND bt.visit_plan_id={0} """.format(plan_id)
            else:
                where_bt += """ AND bt.delivery_plan_id={0} """.format(plan_id)

        group = """GROUP BY bt.user_id"""
        break_time = self.break_time_model.get_count_all_break_time_statistic(
            self.cursor, select=select, join=join, where=where_bt, order=order, group=group
        )

        # TODO: Get statistic Permission Report Location for Logistic
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

        if plan_id:
            if job_function == "sales":
                where_location += """ AND al.visit_plan_id={0} """.format(plan_id)
            else:
                where_location += """ AND al.delivery_plan_id={0} """.format(plan_id)

        count_location = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_location, order=order
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

        if plan_id:
            if job_function == "sales":
                where_nfc += """ AND al.visit_plan_id={0} """.format(plan_id)
            else:
                where_nfc += """ AND al.delivery_plan_id={0} """.format(plan_id)

        count_nfc_sales = self.permissions_model.get_count_all_permission_alert_statistic(
            self.cursor, select=select, select_count=select_count, join=join, where=where_nfc, order=order
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

        if plan_id:
            if job_function == "sales":
                where_print += """ AND al.visit_plan_id={0} """.format(plan_id)
            else:
                where_print += """ AND al.delivery_plan_id={0} """.format(plan_id)

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

        if plan_id:
            where_spm += """ AND spm.visit_plan_id={0} """.format(plan_id)

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

        if plan_id:
            where_spm_inv += """ AND spm.visit_plan_id={0} """.format(plan_id)

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

        if plan_id:
            where_spm_inv_wo += """ AND spm.visit_plan_id={0} """.format(plan_id)

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

        if plan_id:
            where_dp += """ AND dp.id={0} """.format(plan_id)

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

        if plan_id:
            where_dd += """ AND dd.delivery_plan_id={0} """.format(plan_id)

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

        if plan_id:
            where_dd += """ AND dd.delivery_plan_id={0} """.format(plan_id)

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
            if cancel < 0:
                cancel = 0
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
            data_performance = data

        return data_performance
