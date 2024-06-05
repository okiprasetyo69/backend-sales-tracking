import re
import json
import xlsxwriter
import pdfkit

from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template
from collections import OrderedDict

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql
from rest.models import PermissionsModel, UserModel, BranchesModel, EmployeeModel, CustomerModel, DivisionModel

__author__ = 'Junior'


class PermissionsController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.permissions_model = PermissionsModel()
        self.user_model = UserModel()
        self.branch_model = BranchesModel()
        self.employee_model = EmployeeModel()
        self.customer_model = CustomerModel()
        self.division_model = DivisionModel()

    def create(self, create_data: 'dict', user_id: 'int'):
        """
        Function for create new division

        :param create_data: dict
        :param user_id: int
        :return:
            Division Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        print("==========================Debug===============")
        print(create_data['description'])
        if create_data['type'] == 'routes':
            create_data['subject'] = "Change Routes"
            create_data['customer_code'] = create_data['customer_code']
        elif create_data['type'] == 'break_time':
            create_data['subject'] = "Extend Break Time"
            description = json.loads(create_data['description'])
            create_data['description'] = {
                'time': description['time'] * 60
            }
            # create_data['customer_code'] = create_data['customer_code']
            create_data['customer_code'] = None
        elif create_data['type'] == 'other':
            create_data['subject'] = "Other"
            # create_data['customer_code'] = create_data['customer_code']
            create_data['customer_code'] = None
        elif create_data['type'] == 'report':
            description = create_data['description']
            if description['type'] == "nfc":
                create_data['subject'] = "Report NFC"
            if description['type'] == "location":
                create_data['subject'] = "Report Location"
            if description['type'] == "closed":
                create_data['subject'] = "Report Toko Tutup"
            if description['type'] == "print":
                create_data['subject'] = "Report Print"
            if description['type'] == "other":
                create_data['subject'] = "Report Other"
            create_data['customer_code'] = create_data['customer_code']
        elif create_data['type'] == 'visit_time':
            create_data['subject'] = "Extend Visit Time"
            description = json.loads(create_data['description'])
            create_data['description'] = {
                'time': description['time'] * 60
            }
            create_data['customer_code'] = create_data['customer_code']
        elif create_data['type'] == 'alert':
            create_data['subject'] = "Alert"
            create_data['customer_code'] = None
        elif create_data['type'] == 'print':
            create_data['subject'] = "Request Print"
            create_data['customer_code'] = create_data['customer_code']
        else:
            create_data['subject'] = None
            create_data['customer_code'] = None
        if create_data.get('visit_plan_id'):
            create_data['delivery_plan_id'] = None
        if create_data.get('delivery_plan_id'):
            create_data['visit_plan_id'] = None
        try:
            result = self.permissions_model.insert_into_db(
                self.cursor, subject=create_data['subject'], customer_code=create_data['customer_code'],
                visit_plan_id=create_data['visit_plan_id'], delivery_plan_id=create_data['delivery_plan_id'],
                date=today, type=create_data['type'], description=create_data['description'],
                notes=create_data['notes'], create_by=user_id
            )
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return last_insert_id

    def get_permission_alert_by_id(self, _id: int):
        """
        Get permision and alert Information Data

        :param _id: int
        :return:
            division Object
        """
        result = self.permissions_model.get_permission_alert_by_id(self.cursor, _id)

        if len(result) == 0:
            raise BadRequest("This division not exist", 500, 1, data=[])
        else:
            result = result[0]
            if result['create_by'] is not None:
                try:
                    result['create_user'] = self.user_model.get_user_by_id(
                        self.cursor, result['create_by'], select="username, employee_id, branch_id"
                    )[0]
                except:
                    result['create_user'] = {}
                if result['create_user']['employee_id'] is not None:
                    try:
                        result['create_user']['name'] = self.employee_model.get_employee_by_id(
                            self.cursor,
                            result['create_user']['employee_id'],
                            select="""name""")[0]['name']
                    except:
                        result['create_user']['name'] = None
                if result['create_user']['branch_id'] is not None:
                    try:
                        result['create_user']['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor,
                            result['create_user']['branch_id'],
                            select="""name""")[0]['name']
                    except:
                        result['create_user']['branch_name'] = None
            else:
                result['create_user'] = {}
            if result['approval_by'] is not None:
                try:
                    result['approval_user'] = self.user_model.get_user_by_id(
                        self.cursor, result['approval_by'], select="username, employee_id, branch_id"
                    )[0]
                except:
                    result['approval_user'] = {}
                if result['approval_user']['employee_id'] is not None:
                    try:
                        result['approval_user']['name'] = self.employee_model.get_employee_by_id(
                            self.cursor,
                            result['approval_user']['employee_id'],
                            select="""name""")[0]['name']
                    except:
                        result['approval_user']['name'] = None
                if result['approval_user']['branch_id'] is not None:
                    try:
                        result['approval_user']['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor,
                            result['approval_user']['branch_id'],
                            select="""name""")[0]['name']
                    except:
                        result['approval_user']['branch_name'] = None
            else:
                result['approval_user'] = {}
            if result['reject_by'] is not None:
                try:

                    result['reject_user'] = self.user_model.get_user_by_id(
                        self.cursor, result['reject_by'], select="username, employee_id, branch_id"
                    )[0]
                except:
                    result['reject_user'] = {}
                if result['reject_user']['employee_id'] is not None:
                    try:
                        result['reject_user']['name'] = self.employee_model.get_employee_by_id(
                            self.cursor,
                            result['reject_user']['employee_id'],
                            select="""name""")[0]['name']
                    except:
                        result['reject_user']['name'] = None
                if result['reject_user']['branch_id'] is not None:
                    try:
                        result['reject_user']['branch_name'] = self.branch_model.get_branches_by_id(
                            self.cursor,
                            result['reject_user']['branch_id'],
                            select="""name""")[0]['name']
                    except:
                        result['reject_user']['branch_name'] = None
            else:
                result['reject_user'] = {}
            if result['description'] is not None:
                result['description'] = json.loads(result['description'])
                if result['type'] == 'break_time':
                    result['description']['time'] = result['description']['time'] / 60
                elif result['type'] == 'visit_time':
                    result['description']['time'] = result['description']['time'] / 60
            if result['date'] is not None:
                result['date'] = str(result['date'])
        return result

    def update_permission_alert(self, update_data: 'dict', _id: 'int'):
        """
        Update permissions and alert
        :param update_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.permissions_model.update_by_id(self.cursor, update_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_all_permission_alert_data(
            self, page: int, limit: int, search: str, column: str, direction: str, tipe: str, category: str,
            log: bool, user_id: int, job_category: str, branch_privilege: list, division_privilege: list,
            data_filter: list
    ):
        """
        Get List Of Permissions and Alert
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: tipe: str
        :param: category: str
        :param: log: bool
        :param: user_id: int
        :param: division_privilege: list
        :param: data_filter: list
        :return:
            list division Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")

        result = {}
        data = []
        start = page * limit - limit
        order = ''
        if tipe == 'management':
            select_count = "pa.id"
            select = "pa.*"
            if job_category == 'sales':
                where = """WHERE u.branch_id IN ({0}) AND u.division_id IN ({1}) AND pa.date LIKE '{2}%' """.format(
                    ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege), today
                )
            elif job_category == 'logistic':
                where = """WHERE u.branch_id IN ({0}) AND pa.date LIKE '{1}%' """.format(
                    ", ".join(str(x) for x in branch_privilege), today
                )
            else:
                where = """WHERE u.branch_id IN ({0}) AND pa.date LIKE '{1}%' """.format(
                    ", ".join(str(x) for x in branch_privilege), today
                )

            if job_category == 'sales':
                where += "AND pa.visit_plan_id IS NOT NULL "
            elif job_category == 'logistic':
                where += "AND pa.delivery_plan_id IS NOT NULL "

            if category == "request":
                where += """AND (pa.type != 'alert' AND pa.is_approved = 0 AND pa.is_rejected = 0) """
            if category == "approved":
                where += """AND (pa.type != 'alert' AND (pa.is_approved = 1 OR pa.is_rejected = 1)) """
            join = """as pa LEFT JOIN `users` as u ON pa.create_by = u.id """
            order = "ORDER BY pa.date DESC"
            permission_data = self.permissions_model.get_all_permission_alert(
                self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
            )
            count_filter = self.permissions_model.get_count_all_permission_alert(
                self.cursor, select=select_count, join=join, where=where
            )
            count = self.permissions_model.get_count_all_permission_alert(
                self.cursor, select=select_count, join=join, where=where
            )
            if permission_data:
                for dt in permission_data:
                    if dt['create_by'] is not None:
                        try:
                            dt['create_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['create_by'], select="username, employee_id, branch_id"
                            )[0]
                        except:
                            dt['create_user'] = {}
                        if dt['create_user']['employee_id'] is not None:
                            try:
                                dt['create_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['create_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['create_user']['name'] = None
                        if dt['create_user']['branch_id'] is not None:
                            try:
                                dt['create_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['create_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['create_user']['branch_name'] = None
                    else:
                        dt['create_user'] = {}
                    if dt['approval_by'] is not None:
                        try:
                            dt['approval_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['approval_by'], select="username, employee_id, branch_id"
                            )[0]
                        except:
                            dt['approval_user'] = {}
                        if dt['approval_user']['employee_id'] is not None:
                            try:
                                dt['approval_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['approval_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['approval_user']['name'] = None
                        if dt['approval_user']['branch_id'] is not None:
                            try:
                                dt['approval_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['approval_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['approval_user']['branch_name'] = None
                    else:
                        dt['approval_user'] = {}
                    if dt['reject_by'] is not None:
                        try:

                            dt['reject_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['reject_by'], select="username, employee_id, branch_id"
                            )[0]
                        except:
                            dt['reject_user'] = {}
                        if dt['reject_user']['employee_id'] is not None:
                            try:
                                dt['reject_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['reject_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['reject_user']['name'] = None
                        if dt['reject_user']['branch_id'] is not None:
                            try:
                                dt['reject_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['reject_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['reject_user']['branch_name'] = None
                    else:
                        dt['reject_user'] = {}
                    if dt['customer_code'] is not None:
                        try:
                            dt['customer'] = self.customer_model.get_customer_by_id(
                                self.cursor, dt['customer_code'], select="code, name, address, lng, lat"
                            )[0]
                        except:
                            dt['customer'] = None
                    else:
                        dt['customer'] = None
                    if dt['description'] is not None:
                        dt['description'] = json.loads(dt['description'])
                        if dt['type'] == 'break_time':
                            dt['description']['time'] = dt['description']['time'] / 60
                        elif dt['type'] == 'visit_time':
                            dt['description']['time'] = dt['description']['time'] / 60
                    if dt['date'] is not None:
                        dt['date'] = str(dt['date'])
                    data.append(dt)

            result['data'] = data
            result['total'] = count
            result['total_filter'] = count_filter

        else:
            where = ''
            if tipe == 'web':
                select_count = "pa.id"
                select = "pa.*"
                if job_category == 'logistic':
                    where += """WHERE (u.branch_id IN ({0})) """.format(
                        ", ".join(str(x) for x in branch_privilege)
                    )
                else:
                    where += """WHERE (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
                        ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
                    )

                if category == "permission":
                    where += "AND pa.type != 'alert' "
                    # if log:
                    #     where += "AND (pa.type != 'alert' AND (pa.is_approved = 1 OR pa.is_rejected = 1)) "
                    # else:
                    #     where += """AND (pa.type != 'alert' AND pa.is_approved = 0 AND pa.is_rejected = 0)"""
                elif category == "alert":
                    where += "AND pa.type = 'alert' "

                if job_category == 'sales':
                    where += "AND pa.visit_plan_id IS NOT NULL "
                elif job_category == 'logistic':
                    where += "AND pa.delivery_plan_id IS NOT NULL "

                if data_filter:
                    data_filter = data_filter[0]
                    if data_filter['start_date']:
                        where += """AND (pa.date >= '{0} 00:00:00' AND pa.date <= '{1} 23:59:59') """.format(
                            data_filter['start_date'], data_filter['end_date']
                        )
                    if data_filter['user_id']:
                        where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in data_filter['user_id']))
                    if data_filter['branch_id']:
                        where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['branch_id']))
                    if job_category != 'logistic':
                        if data_filter['division_id']:
                            where += """AND u.division_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['division_id']))

                join = """as pa LEFT JOIN `users` as u ON pa.create_by = u.id 
                LEFT JOIN `branches` as b ON u.branch_id = b.id 
                LEFT JOIN `divisions` as d ON u.division_id = d.id """

                if column:
                    if column == 'branch':
                        order = """ORDER BY b.name {1}""".format(column, direction)
                    elif column == 'division':
                        order = """ORDER BY d.division_name {1}""".format(column, direction)
                    else:
                        order = """ORDER BY pa.{0} {1}""".format(column, direction)
            else:
                select_count = "id"
                select = "*"
                join = ''
                where += "WHERE `create_by` = {0} AND `date` LIKE '{1}%' ".format(user_id, today)
                order += "ORDER BY date DESC"
                start = 0
                limit = 1000
                if column:
                    order = """ORDER BY {0} {1}""".format(column, direction)

            if search:
                if tipe == 'web':
                    where += """AND (pa.subject LIKE '%{0}%' OR pa.notes LIKE '%{0}%' 
                    OR b.name LIKE '%{0}%' OR d.division_name LIKE '%{0}%') """.format(search)
                else:
                    where += """AND notes LIKE '%{0}%' """.format(search)

            permission_data = self.permissions_model.get_all_permission_alert(
                self.cursor, select=select, where=where, join=join, order=order, start=start, limit=limit
            )
            count_filter = self.permissions_model.get_count_all_permission_alert(
                self.cursor, select=select_count, where=where, join=join
            )
            count = self.permissions_model.get_count_all_permission_alert(
                self.cursor, select=select_count, where=where, join=join
            )
            if permission_data:
                for dt in permission_data:
                    if dt['create_by'] is not None:
                        try:
                            dt['create_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['create_by'], select="username, employee_id, branch_id, division_id"
                            )[0]
                        except:
                            dt['create_user'] = {}
                        if dt['create_user']['employee_id'] is not None:
                            try:
                                dt['create_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['create_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['create_user']['name'] = None
                        if dt['create_user']['branch_id'] is not None:
                            try:
                                dt['create_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['create_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['create_user']['branch_name'] = None
                        if job_category == 'sales':
                            if dt['create_user']['division_id'] is not None:
                                try:
                                    dt['create_user']['division_name'] = self.division_model.get_division_by_id(
                                        self.cursor, dt['create_user']['division_id'], select="division_name")[0][
                                        'division_name']
                                except:
                                    dt['create_user']['division_name'] = None
                    else:
                        dt['create_user'] = {}
                    if dt['approval_by'] is not None:
                        try:
                            dt['approval_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['approval_by'], select="username, employee_id, branch_id"
                            )[0]
                        except:
                            dt['approval_user'] = {}
                        if dt['approval_user']['employee_id'] is not None:
                            try:
                                dt['approval_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['approval_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['approval_user']['name'] = None
                        if dt['approval_user']['branch_id'] is not None:
                            try:
                                dt['approval_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['approval_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['approval_user']['branch_name'] = None
                    else:
                        dt['approval_user'] = {}
                    if dt['reject_by'] is not None:
                        try:

                            dt['reject_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['reject_by'], select="username, employee_id, branch_id"
                            )[0]
                        except:
                            dt['reject_user'] = {}
                        if dt['reject_user']['employee_id'] is not None:
                            try:
                                dt['reject_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['reject_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['reject_user']['name'] = None
                        if dt['reject_user']['branch_id'] is not None:
                            try:
                                dt['reject_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['reject_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['reject_user']['branch_name'] = None
                    else:
                        dt['reject_user'] = {}
                    if dt['customer_code'] is not None:
                        try:
                            dt['customer'] = self.customer_model.get_customer_by_id(
                                self.cursor, dt['customer_code'], select="code, name, address, lng, lat"
                            )[0]
                        except:
                            dt['customer'] = None
                    else:
                        dt['customer'] = None
                    if dt['description'] is not None:
                        dt['description'] = json.loads(dt['description'])
                        if dt['type'] == 'break_time':
                            dt['description']['time'] = dt['description']['time'] / 60
                        elif dt['type'] == 'visit_time':
                            dt['description']['time'] = dt['description']['time'] / 60
                    if dt['date'] is not None:
                        dt['date'] = str(dt['date'])
                    data.append(dt)
            result['data'] = data
            result['total'] = count
            result['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if result['total_filter'] > page * limit:
            result['has_next'] = True
        else:
            result['has_next'] = False
        if limit <= page * count - count:
            result['has_prev'] = True
        else:
            result['has_prev'] = False
        return result

    def get_all_export_permission_alert_data(
            self, page: int, limit: int, search: str, column: str, direction: str, tipe: str, category: str,
            log: bool, user_id: int, job_category: str, branch_privilege: list, division_privilege: list,
            data_filter: list
    ):
        """
        Get List Of Permissions and Alert
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: tipe: str
        :param: category: str
        :param: log: bool
        :param: user_id: int
        :param: division_privilege: list
        :param: data_filter: list
        :return:
            list division Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")

        result = {}
        data = []
        start = page * limit - limit
        order = ''
        if tipe == 'management':
            select_count = "pa.id"
            select = "pa.*"
            if job_category == 'sales':
                where = """WHERE u.branch_id IN ({0}) AND u.division_id IN ({1}) AND pa.date LIKE '{2}%' """.format(
                    ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege), today
                )
            elif job_category == 'logistic':
                where = """WHERE u.branch_id IN ({0}) AND pa.date LIKE '{1}%' """.format(
                    ", ".join(str(x) for x in branch_privilege), today
                )
            else:
                where = """WHERE u.branch_id IN ({0}) AND pa.date LIKE '{1}%' """.format(
                    ", ".join(str(x) for x in branch_privilege), today
                )

            if job_category == 'sales':
                where += "AND pa.visit_plan_id IS NOT NULL "
            elif job_category == 'logistic':
                where += "AND pa.delivery_plan_id IS NOT NULL "

            if category == "request":
                where += """AND (pa.type != 'alert' AND pa.is_approved = 0 AND pa.is_rejected = 0) """
            if category == "approved":
                where += """AND (pa.type != 'alert' AND (pa.is_approved = 1 OR pa.is_rejected = 1)) """
            join = """as pa LEFT JOIN `users` as u ON pa.create_by = u.id """
            order = "ORDER BY pa.date DESC"
            permission_data = self.permissions_model.get_all_permission_alert(
                self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
            )
            count_filter = self.permissions_model.get_count_all_permission_alert(
                self.cursor, select=select_count, join=join, where=where
            )
            count = self.permissions_model.get_count_all_permission_alert(
                self.cursor, select=select_count, join=join, where=where
            )
            if permission_data:
                for dt in permission_data:
                    if dt['create_by'] is not None:
                        try:
                            dt['create_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['create_by'], select="username, employee_id, branch_id"
                            )[0]
                        except:
                            dt['create_user'] = {}
                        if dt['create_user']['employee_id'] is not None:
                            try:
                                dt['create_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['create_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['create_user']['name'] = None
                        if dt['create_user']['branch_id'] is not None:
                            try:
                                dt['create_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['create_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['create_user']['branch_name'] = None
                    else:
                        dt['create_user'] = {}
                    if dt['approval_by'] is not None:
                        try:
                            dt['approval_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['approval_by'], select="username, employee_id, branch_id"
                            )[0]
                        except:
                            dt['approval_user'] = {}
                        if dt['approval_user']['employee_id'] is not None:
                            try:
                                dt['approval_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['approval_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['approval_user']['name'] = None
                        if dt['approval_user']['branch_id'] is not None:
                            try:
                                dt['approval_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['approval_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['approval_user']['branch_name'] = None
                    else:
                        dt['approval_user'] = {}
                    if dt['reject_by'] is not None:
                        try:

                            dt['reject_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['reject_by'], select="username, employee_id, branch_id"
                            )[0]
                        except:
                            dt['reject_user'] = {}
                        if dt['reject_user']['employee_id'] is not None:
                            try:
                                dt['reject_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['reject_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['reject_user']['name'] = None
                        if dt['reject_user']['branch_id'] is not None:
                            try:
                                dt['reject_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['reject_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['reject_user']['branch_name'] = None
                    else:
                        dt['reject_user'] = {}
                    if dt['customer_code'] is not None:
                        try:
                            dt['customer'] = self.customer_model.get_customer_by_id(
                                self.cursor, dt['customer_code'], select="code, name, address, lng, lat"
                            )[0]
                        except:
                            dt['customer'] = None
                    else:
                        dt['customer'] = None
                    if dt['description'] is not None:
                        dt['description'] = json.loads(dt['description'])
                        if dt['type'] == 'break_time':
                            dt['description']['time'] = dt['description']['time'] / 60
                        elif dt['type'] == 'visit_time':
                            dt['description']['time'] = dt['description']['time'] / 60
                    if dt['date'] is not None:
                        dt['date'] = str(dt['date'])
                    data.append(dt)

            result['data'] = data
            result['total'] = count
            result['total_filter'] = count_filter

        else:
            where = ''
            if tipe == 'web':
                select_count = "pa.id"
                select = "pa.*"
                if job_category == 'logistic':
                    where += """WHERE (u.branch_id IN ({0})) """.format(
                        ", ".join(str(x) for x in branch_privilege)
                    )
                else:
                    where += """WHERE (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
                        ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
                    )

                if category == "permission":
                    where += "AND pa.type != 'alert' "
                    # if log:
                    #     where += "AND (pa.type != 'alert' AND (pa.is_approved = 1 OR pa.is_rejected = 1)) "
                    # else:
                    #     where += """AND (pa.type != 'alert' AND pa.is_approved = 0 AND pa.is_rejected = 0)"""
                elif category == "alert":
                    where += "AND pa.type = 'alert' "

                if job_category == 'sales':
                    where += "AND pa.visit_plan_id IS NOT NULL "
                elif job_category == 'logistic':
                    where += "AND pa.delivery_plan_id IS NOT NULL "

                if data_filter:
                    tmp_data_filter = data_filter[0]
                    if tmp_data_filter['start_date']:
                        where += """AND (pa.date >= '{0} 00:00:00' AND pa.date <= '{1} 23:59:59') """.format(
                            tmp_data_filter['start_date'], tmp_data_filter['end_date']
                        )
                    if tmp_data_filter['user_id']:
                        where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['user_id']))
                    if tmp_data_filter['branch_id']:
                        where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['branch_id']))
                    if job_category != 'logistic':
                        if tmp_data_filter['division_id']:
                            where += """AND u.division_id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['division_id']))

                join = """as pa LEFT JOIN `users` as u ON pa.create_by = u.id 
                LEFT JOIN `branches` as b ON u.branch_id = b.id 
                LEFT JOIN `divisions` as d ON u.division_id = d.id """

                if column:
                    if column == 'branch':
                        order = """ORDER BY b.name {1}""".format(column, direction)
                    elif column == 'division':
                        order = """ORDER BY d.division_name {1}""".format(column, direction)
                    else:
                        order = """ORDER BY pa.{0} {1}""".format(column, direction)
            else:
                select_count = "id"
                select = "*"
                join = ''
                where += "WHERE `create_by` = {0} AND `date` LIKE '{1}%' ".format(user_id, today)
                order += "ORDER BY date DESC"
                start = 0
                limit = 1000
                if column:
                    order = """ORDER BY {0} {1}""".format(column, direction)

            if search:
                if tipe == 'web':
                    where += """AND (pa.subject LIKE '%{0}%' OR pa.notes LIKE '%{0}%' 
                    OR b.name LIKE '%{0}%' OR d.division_name LIKE '%{0}%') """.format(search)
                else:
                    where += """AND notes LIKE '%{0}%' """.format(search)

            permission_data = self.permissions_model.get_all_permission_alert(
                self.cursor, select=select, where=where, join=join, order=order, start=start, limit=limit
            )
            if permission_data:
                for dt in permission_data:
                    if dt['create_by'] is not None:
                        try:
                            dt['create_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['create_by'], select="username, employee_id, branch_id, division_id"
                            )[0]
                        except:
                            dt['create_user'] = {}
                        if dt['create_user']['employee_id'] is not None:
                            try:
                                dt['create_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['create_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['create_user']['name'] = None
                        if dt['create_user']['branch_id'] is not None:
                            try:
                                dt['create_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['create_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['create_user']['branch_name'] = None
                        if job_category == 'sales':
                            if dt['create_user']['division_id'] is not None:
                                try:
                                    dt['create_user']['division_name'] = self.division_model.get_division_by_id(
                                        self.cursor, dt['create_user']['division_id'], select="division_name")[0][
                                        'division_name']
                                except:
                                    dt['create_user']['division_name'] = None
                    else:
                        dt['create_user'] = {}
                    if dt['approval_by'] is not None:
                        try:
                            dt['approval_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['approval_by'], select="username, employee_id, branch_id"
                            )[0]
                        except:
                            dt['approval_user'] = {}
                        if dt['approval_user']['employee_id'] is not None:
                            try:
                                dt['approval_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['approval_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['approval_user']['name'] = None
                        if dt['approval_user']['branch_id'] is not None:
                            try:
                                dt['approval_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['approval_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['approval_user']['branch_name'] = None
                    else:
                        dt['approval_user'] = {}
                    if dt['reject_by'] is not None:
                        try:

                            dt['reject_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['reject_by'], select="username, employee_id, branch_id"
                            )[0]
                        except:
                            dt['reject_user'] = {}
                        if dt['reject_user']['employee_id'] is not None:
                            try:
                                dt['reject_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['reject_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['reject_user']['name'] = None
                        if dt['reject_user']['branch_id'] is not None:
                            try:
                                dt['reject_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['reject_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['reject_user']['branch_name'] = None
                    else:
                        dt['reject_user'] = {}
                    if dt['customer_code'] is not None:
                        try:
                            dt['customer'] = self.customer_model.get_customer_by_id(
                                self.cursor, dt['customer_code'], select="code, name, address, lng, lat"
                            )[0]
                        except:
                            dt['customer'] = None
                    else:
                        dt['customer'] = None
                    if dt['description'] is not None:
                        dt['description'] = json.loads(dt['description'])
                        if dt['type'] == 'break_time':
                            dt['description']['time'] = dt['description']['time'] / 60
                        elif dt['type'] == 'visit_time':
                            dt['description']['time'] = dt['description']['time'] / 60
                    if dt['date'] is not None:
                        dt['date'] = str(dt['date'])
                    data.append(dt)
            output = BytesIO()

            workbook = xlsxwriter.Workbook(output)
            if category == "permission":
                worksheet = workbook.add_worksheet('Data Permission')
            else:
                worksheet = workbook.add_worksheet('Data Alert')
            merge_format = workbook.add_format(
                {
                    'bold': 1,
                    'border': 0,
                    'align': 'left',
                    'valign': 'vcenter'
                }
            )
            # Header sheet
            if data_filter:
                data_filter = data_filter[0]
                if data_filter['start_date'] and not data_filter['user_id']:
                    if category == "permission":
                        worksheet.merge_range(
                            'A1:F1',
                            'PERMISSION (USER: ALL, TANGGAL: {0} s/d {1})'.format(
                                data_filter['start_date'], data_filter['end_date']
                            ),
                            merge_format
                        )
                    else:
                        worksheet.merge_range(
                            'A1:F1',
                            'ALERT (USER: ALL, TANGGAL: {0} s/d {1})'.format(
                                data_filter['start_date'], data_filter['end_date']
                            ),
                            merge_format
                        )
                elif data_filter['user_id'] and not data_filter['start_date']:
                    if category == "permission":
                        worksheet.merge_range(
                            'A1:F1',
                            'PERMISSION (USER: {0}, TANGGAL: ALL)'.format(", ".join(x for x in data_filter['username'])),
                            merge_format
                        )
                    else:
                        worksheet.merge_range(
                            'A1:F1',
                            'ALERT (USER: {0}, TANGGAL: ALL)'.format(", ".join(x for x in data_filter['username'])),
                            merge_format
                        )

                else:
                    if category == "permission":
                        worksheet.merge_range(
                            'A1:F1',
                            'PERMISSION (USER: {0}, TANGGAL: {1} s/d {2})'.format(
                                ", ".join(x for x in data_filter['username']), data_filter['start_date'], data_filter['end_date']
                            ),
                            merge_format
                        )
                    else:
                        worksheet.merge_range(
                            'A1:F1',
                            'ALERT (USER: {0}, TANGGAL: {1} s/d {2})'.format(
                                ", ".join(x for x in data_filter['username']), data_filter['start_date'], data_filter['end_date']
                            ),
                            merge_format
                        )
            else:
                if category == "permission":
                    worksheet.merge_range('A1:F1', 'PERMISSION (USER: ALL, TANGGAL: ALL)', merge_format)
                else:
                    worksheet.merge_range('A1:F1', 'ALERT (USER: ALL, TANGGAL: ALL)', merge_format)
            if category == "permission":
                if job_category == 'sales':
                    worksheet.write('A3', 'USER', merge_format)
                    worksheet.write('B3', 'TANGGAL', merge_format)
                    worksheet.write('C3', 'BRANCH', merge_format)
                    worksheet.write('D3', 'DIVISION', merge_format)
                    worksheet.write('E3', 'PERMISSION TYPE', merge_format)
                    worksheet.write('F3', 'DESCRIPTION', merge_format)
                    worksheet.write('G3', 'STATUS', merge_format)
                    worksheet.write('H3', 'APPROVAL/REJECT BY', merge_format)

                    data_rows = 3
                    for rec in data:
                        status_permission = "Pending"
                        if rec['is_approved'] == 1:
                            status_permission = "Approved"
                        if rec['is_rejected'] == 1:
                            status_permission = "Rejected"
                        approval_by = ""
                        if rec['approval_user']:
                            approval_by = rec['approval_user']['name']
                        if rec['reject_user']:
                            approval_by = rec['reject_user']['name']
                        worksheet.write(data_rows, 0, rec['create_user']['name'])
                        worksheet.write(data_rows, 1, rec['date'])
                        worksheet.write(data_rows, 2, rec['create_user']['branch_name'])
                        worksheet.write(data_rows, 3, rec['create_user']['division_name'])
                        worksheet.write(data_rows, 4, rec['type'].replace("_", " ").title())
                        worksheet.write(data_rows, 5, rec['notes'])
                        worksheet.write(data_rows, 6, status_permission)
                        worksheet.write(data_rows, 7, approval_by)
                        data_rows += 1
                else:
                    worksheet.write('A3', 'USER', merge_format)
                    worksheet.write('B3', 'TANGGAL', merge_format)
                    worksheet.write('C3', 'BRANCH', merge_format)
                    worksheet.write('D3', 'PERMISSION TYPE', merge_format)
                    worksheet.write('E3', 'DESCRIPTION', merge_format)
                    worksheet.write('F3', 'STATUS', merge_format)
                    worksheet.write('G3', 'APPROVAL/REJECT BY', merge_format)

                    data_rows = 3
                    for rec in data:
                        status_permission = "Pending"
                        if rec['is_approved'] == 1:
                            status_permission = "Approved"
                        if rec['is_rejected'] == 1:
                            status_permission = "Rejected"
                        approval_by = ""
                        if rec['approval_user']:
                            approval_by = rec['approval_user']['name']
                        if rec['reject_user']:
                            approval_by = rec['reject_user']['name']
                        worksheet.write(data_rows, 0, rec['create_user']['name'])
                        worksheet.write(data_rows, 1, rec['date'])
                        worksheet.write(data_rows, 2, rec['create_user']['branch_name'])
                        worksheet.write(data_rows, 3, rec['type'].replace("_", " ").title())
                        worksheet.write(data_rows, 4, rec['notes'])
                        worksheet.write(data_rows, 5, status_permission)
                        worksheet.write(data_rows, 6, approval_by)
                        data_rows += 1
            else:
                if job_category == 'sales':
                    worksheet.write('A3', 'USER', merge_format)
                    worksheet.write('B3', 'TANGGAL', merge_format)
                    worksheet.write('C3', 'BRANCH', merge_format)
                    worksheet.write('D3', 'DIVISION', merge_format)
                    worksheet.write('E3', 'DESCRIPTION', merge_format)

                    data_rows = 3
                    for rec in data:
                        worksheet.write(data_rows, 0, rec['create_user']['name'])
                        worksheet.write(data_rows, 1, rec['date'])
                        worksheet.write(data_rows, 2, rec['create_user']['branch_name'])
                        worksheet.write(data_rows, 3, rec['create_user']['division_name'])
                        worksheet.write(data_rows, 4, rec['notes'])
                        data_rows += 1
                else:
                    worksheet.write('A3', 'USER', merge_format)
                    worksheet.write('B3', 'TANGGAL', merge_format)
                    worksheet.write('C3', 'BRANCH', merge_format)
                    worksheet.write('D3', 'DESCRIPTION', merge_format)

                    data_rows = 3
                    for rec in data:
                        worksheet.write(data_rows, 0, rec['create_user']['name'])
                        worksheet.write(data_rows, 1, rec['date'])
                        worksheet.write(data_rows, 2, rec['create_user']['branch_name'])
                        worksheet.write(data_rows, 3, rec['notes'])
                        data_rows += 1

            workbook.close()
            output.seek(0)

            result['data'] = data
            result['file'] = output

        return result

    def get_all_export_pdf_permission_alert_data(
            self, page: int, limit: int, search: str, column: str, direction: str, tipe: str, category: str,
            log: bool, user_id: int, job_category: str, branch_privilege: list, division_privilege: list,
            data_filter: list
    ):
        """
        Get List Of Permissions and Alert
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: tipe: str
        :param: category: str
        :param: log: bool
        :param: user_id: int
        :param: division_privilege: list
        :param: data_filter: list
        :return:
            list division Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")

        result = {}
        data = []
        start = page * limit - limit
        order = ''
        if tipe == 'management':
            select_count = "pa.id"
            select = "pa.*"
            if job_category == 'sales':
                where = """WHERE u.branch_id IN ({0}) AND u.division_id IN ({1}) AND pa.date LIKE '{2}%' """.format(
                    ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege), today
                )
            elif job_category == 'logistic':
                where = """WHERE u.branch_id IN ({0}) AND pa.date LIKE '{1}%' """.format(
                    ", ".join(str(x) for x in branch_privilege), today
                )
            else:
                where = """WHERE u.branch_id IN ({0}) AND pa.date LIKE '{1}%' """.format(
                    ", ".join(str(x) for x in branch_privilege), today
                )

            if job_category == 'sales':
                where += "AND pa.visit_plan_id IS NOT NULL "
            elif job_category == 'logistic':
                where += "AND pa.delivery_plan_id IS NOT NULL "

            if category == "request":
                where += """AND (pa.type != 'alert' AND pa.is_approved = 0 AND pa.is_rejected = 0) """
            if category == "approved":
                where += """AND (pa.type != 'alert' AND (pa.is_approved = 1 OR pa.is_rejected = 1)) """
            join = """as pa LEFT JOIN `users` as u ON pa.create_by = u.id """
            order = "ORDER BY pa.date DESC"
            permission_data = self.permissions_model.get_all_permission_alert(
                self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
            )
            count_filter = self.permissions_model.get_count_all_permission_alert(
                self.cursor, select=select_count, join=join, where=where
            )
            count = self.permissions_model.get_count_all_permission_alert(
                self.cursor, select=select_count, join=join, where=where
            )
            if permission_data:
                for dt in permission_data:
                    if dt['create_by'] is not None:
                        try:
                            dt['create_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['create_by'], select="username, employee_id, branch_id"
                            )[0]
                        except:
                            dt['create_user'] = {}
                        if dt['create_user']['employee_id'] is not None:
                            try:
                                dt['create_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['create_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['create_user']['name'] = None
                        if dt['create_user']['branch_id'] is not None:
                            try:
                                dt['create_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['create_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['create_user']['branch_name'] = None
                    else:
                        dt['create_user'] = {}
                    if dt['approval_by'] is not None:
                        try:
                            dt['approval_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['approval_by'], select="username, employee_id, branch_id"
                            )[0]
                        except:
                            dt['approval_user'] = {}
                        if dt['approval_user']['employee_id'] is not None:
                            try:
                                dt['approval_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['approval_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['approval_user']['name'] = None
                        if dt['approval_user']['branch_id'] is not None:
                            try:
                                dt['approval_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['approval_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['approval_user']['branch_name'] = None
                    else:
                        dt['approval_user'] = {}
                    if dt['reject_by'] is not None:
                        try:

                            dt['reject_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['reject_by'], select="username, employee_id, branch_id"
                            )[0]
                        except:
                            dt['reject_user'] = {}
                        if dt['reject_user']['employee_id'] is not None:
                            try:
                                dt['reject_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['reject_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['reject_user']['name'] = None
                        if dt['reject_user']['branch_id'] is not None:
                            try:
                                dt['reject_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['reject_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['reject_user']['branch_name'] = None
                    else:
                        dt['reject_user'] = {}
                    if dt['customer_code'] is not None:
                        try:
                            dt['customer'] = self.customer_model.get_customer_by_id(
                                self.cursor, dt['customer_code'], select="code, name, address, lng, lat"
                            )[0]
                        except:
                            dt['customer'] = None
                    else:
                        dt['customer'] = None
                    if dt['description'] is not None:
                        dt['description'] = json.loads(dt['description'])
                        if dt['type'] == 'break_time':
                            dt['description']['time'] = dt['description']['time'] / 60
                        elif dt['type'] == 'visit_time':
                            dt['description']['time'] = dt['description']['time'] / 60
                    if dt['date'] is not None:
                        dt['date'] = str(dt['date'])
                    data.append(dt)

            result['data'] = data
            result['total'] = count
            result['total_filter'] = count_filter

        else:
            where = ''
            if tipe == 'web':
                select_count = "pa.id"
                select = "pa.*"
                if job_category == 'logistic':
                    where += """WHERE (u.branch_id IN ({0})) """.format(
                        ", ".join(str(x) for x in branch_privilege)
                    )
                else:
                    where += """WHERE (u.branch_id IN ({0}) AND u.division_id IN ({1})) """.format(
                        ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
                    )

                if category == "permission":
                    where += "AND pa.type != 'alert' "
                    # if log:
                    #     where += "AND (pa.type != 'alert' AND (pa.is_approved = 1 OR pa.is_rejected = 1)) "
                    # else:
                    #     where += """AND (pa.type != 'alert' AND pa.is_approved = 0 AND pa.is_rejected = 0)"""
                elif category == "alert":
                    where += "AND pa.type = 'alert' "

                if job_category == 'sales':
                    where += "AND pa.visit_plan_id IS NOT NULL "
                elif job_category == 'logistic':
                    where += "AND pa.delivery_plan_id IS NOT NULL "

                if data_filter:
                    tmp_data_filter = data_filter[0]
                    if tmp_data_filter['start_date']:
                        where += """AND (pa.date >= '{0} 00:00:00' AND pa.date <= '{1} 23:59:59') """.format(
                            tmp_data_filter['start_date'], tmp_data_filter['end_date']
                        )
                    if tmp_data_filter['user_id']:
                        where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['user_id']))
                    if tmp_data_filter['branch_id']:
                        where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['branch_id']))
                    if job_category != 'logistic':
                        if tmp_data_filter['division_id']:
                            where += """AND u.division_id IN ({0}) """.format(", ".join(str(x) for x in tmp_data_filter['division_id']))

                join = """as pa LEFT JOIN `users` as u ON pa.create_by = u.id 
                LEFT JOIN `branches` as b ON u.branch_id = b.id 
                LEFT JOIN `divisions` as d ON u.division_id = d.id """

                if column:
                    if column == 'branch':
                        order = """ORDER BY b.name {1}""".format(column, direction)
                    elif column == 'division':
                        order = """ORDER BY d.division_name {1}""".format(column, direction)
                    else:
                        order = """ORDER BY pa.{0} {1}""".format(column, direction)
            else:
                select_count = "id"
                select = "*"
                join = ''
                where += "WHERE `create_by` = {0} AND `date` LIKE '{1}%' ".format(user_id, today)
                order += "ORDER BY date DESC"
                start = 0
                limit = 1000
                if column:
                    order = """ORDER BY {0} {1}""".format(column, direction)

            if search:
                if tipe == 'web':
                    where += """AND (pa.subject LIKE '%{0}%' OR pa.notes LIKE '%{0}%' 
                    OR b.name LIKE '%{0}%' OR d.division_name LIKE '%{0}%') """.format(search)
                else:
                    where += """AND notes LIKE '%{0}%' """.format(search)

            permission_data = self.permissions_model.get_all_permission_alert(
                self.cursor, select=select, where=where, join=join, order=order, start=start, limit=limit
            )
            if permission_data:
                for dt in permission_data:
                    if dt['create_by'] is not None:
                        try:
                            dt['create_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['create_by'], select="username, employee_id, branch_id, division_id"
                            )[0]
                        except:
                            dt['create_user'] = {}
                        if dt['create_user']['employee_id'] is not None:
                            try:
                                dt['create_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['create_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['create_user']['name'] = None
                        if dt['create_user']['branch_id'] is not None:
                            try:
                                dt['create_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['create_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['create_user']['branch_name'] = None
                        if job_category == 'sales':
                            if dt['create_user']['division_id'] is not None:
                                try:
                                    dt['create_user']['division_name'] = self.division_model.get_division_by_id(
                                        self.cursor, dt['create_user']['division_id'], select="division_name")[0][
                                        'division_name']
                                except:
                                    dt['create_user']['division_name'] = None
                    else:
                        dt['create_user'] = {}
                    if dt['approval_by'] is not None:
                        try:
                            dt['approval_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['approval_by'], select="username, employee_id, branch_id"
                            )[0]
                        except:
                            dt['approval_user'] = {}
                        if dt['approval_user']['employee_id'] is not None:
                            try:
                                dt['approval_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['approval_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['approval_user']['name'] = None
                        if dt['approval_user']['branch_id'] is not None:
                            try:
                                dt['approval_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['approval_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['approval_user']['branch_name'] = None
                    else:
                        dt['approval_user'] = {}
                    if dt['reject_by'] is not None:
                        try:

                            dt['reject_user'] = self.user_model.get_user_by_id(
                                self.cursor, dt['reject_by'], select="username, employee_id, branch_id"
                            )[0]
                        except:
                            dt['reject_user'] = {}
                        if dt['reject_user']['employee_id'] is not None:
                            try:
                                dt['reject_user']['name'] = self.employee_model.get_employee_by_id(
                                    self.cursor,
                                    dt['reject_user']['employee_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['reject_user']['name'] = None
                        if dt['reject_user']['branch_id'] is not None:
                            try:
                                dt['reject_user']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor,
                                    dt['reject_user']['branch_id'],
                                    select="""name""")[0]['name']
                            except:
                                dt['reject_user']['branch_name'] = None
                    else:
                        dt['reject_user'] = {}
                    if dt['customer_code'] is not None:
                        try:
                            dt['customer'] = self.customer_model.get_customer_by_id(
                                self.cursor, dt['customer_code'], select="code, name, address, lng, lat"
                            )[0]
                        except:
                            dt['customer'] = None
                    else:
                        dt['customer'] = None
                    if dt['description'] is not None:
                        dt['description'] = json.loads(dt['description'])
                        if dt['type'] == 'break_time':
                            dt['description']['time'] = dt['description']['time'] / 60
                        elif dt['type'] == 'visit_time':
                            dt['description']['time'] = dt['description']['time'] / 60
                    if dt['date'] is not None:
                        dt['date'] = str(dt['date'])
                    data.append(dt)

            if data_filter:
                data_filter = data_filter[0]
                if data_filter['start_date'] and not data_filter['user_id']:
                    if category == "permission":
                        head_title = 'PERMISSION (USER: ALL, TANGGAL: {0} s/d {1})'.format(
                            data_filter['start_date'], data_filter['end_date']
                        )
                    else:
                        head_title = 'ALERT (USER: ALL, TANGGAL: {0} s/d {1})'.format(
                            data_filter['start_date'], data_filter['end_date']
                        )
                elif data_filter['user_id'] and not data_filter['start_date']:
                    if category == "permission":
                        head_title = 'PERMISSION (USER: {0}, TANGGAL: ALL)'.format(", ".join(x for x in data_filter['username']))
                    else:
                        head_title = 'ALERT (USER: {0}, TANGGAL: ALL)'.format(", ".join(x for x in data_filter['username']))

                else:
                    if category == "permission":
                        head_title = 'PERMISSION (USER: {0}, TANGGAL: {1} s/d {2})'.format(
                            ", ".join(x for x in data_filter['username']), data_filter['start_date'], data_filter['end_date']
                        )
                    else:
                        head_title = 'ALERT (USER: {0}, TANGGAL: {1} s/d {2})'.format(
                            ", ".join(x for x in data_filter['username']), data_filter['start_date'], data_filter['end_date']
                        )
            else:
                if category == "permission":
                    head_title = 'PERMISSION (USER: ALL, TANGGAL: ALL)'
                else:
                    head_title = 'ALERT (USER: ALL, TANGGAL: ALL)'
            if category == "permission":
                if job_category == 'sales':
                    head_table = OrderedDict()
                    head_table['user'] = "USER"
                    head_table['tanggal'] = "TANGGAL"
                    head_table['branch'] = "BRANCH"
                    head_table['division'] = "DIVISION"
                    head_table['type'] = "PERMISSION TYPE"
                    head_table['description'] = "DESCRIPTION"
                    head_table['status'] = "STATUS"
                    head_table['approval'] = "APPROVAL/REJECT BY"
                    body_table = []
                    for rec in data:
                        data_body = OrderedDict()
                        status_permission = "Pending"
                        if rec['is_approved'] == 1:
                            status_permission = "Approved"
                        if rec['is_rejected'] == 1:
                            status_permission = "Rejected"
                        approval_by = ""
                        if rec['approval_user']:
                            approval_by = rec['approval_user']['name']
                        if rec['reject_user']:
                            approval_by = rec['reject_user']['name']
                        data_body['user'] = rec['create_user']['name']
                        data_body['tanggal'] = rec['date']
                        data_body['branch'] = rec['create_user']['branch_name']
                        data_body['division'] = rec['create_user']['division_name']
                        data_body['type'] = rec['type'].replace("_", " ").title()
                        data_body['description'] = rec['notes']
                        data_body['status'] = status_permission
                        data_body['approval'] = approval_by
                        body_table.append(data_body)
                else:

                    head_table = OrderedDict()
                    head_table['user'] = "USER"
                    head_table['tanggal'] = "TANGGAL"
                    head_table['branch'] = "BRANCH"
                    head_table['type'] = "PERMISSION TYPE"
                    head_table['description'] = "DESCRIPTION"
                    head_table['status'] = "STATUS"
                    head_table['approval'] = "APPROVAL/REJECT BY"
                    body_table = []
                    for rec in data:
                        data_body = OrderedDict()
                        status_permission = "Pending"
                        if rec['is_approved'] == 1:
                            status_permission = "Approved"
                        if rec['is_rejected'] == 1:
                            status_permission = "Rejected"
                        approval_by = ""
                        if rec['approval_user']:
                            approval_by = rec['approval_user']['name']
                        if rec['reject_user']:
                            approval_by = rec['reject_user']['name']
                        data_body['user'] = rec['create_user']['name']
                        data_body['tanggal'] = rec['date']
                        data_body['branch'] = rec['create_user']['branch_name']
                        data_body['type'] = rec['type'].replace("_", " ").title()
                        data_body['description'] = rec['notes']
                        data_body['status'] = status_permission
                        data_body['approval'] = approval_by
                        body_table.append(data_body)
            else:
                if job_category == 'sales':
                    head_table = OrderedDict()
                    head_table['user'] = "USER"
                    head_table['tanggal'] = "TANGGAL"
                    head_table['branch'] = "BRANCH"
                    head_table['division'] = "DIVISION"
                    head_table['description'] = "DESCRIPTION"
                    body_table = []
                    for rec in data:
                        data_body = OrderedDict()
                        data_body['user'] = rec['create_user']['name']
                        data_body['tanggal'] = rec['date']
                        data_body['branch'] = rec['create_user']['branch_name']
                        data_body['division'] = rec['create_user']['division_name']
                        data_body['description'] = rec['notes']
                        body_table.append(data_body)
                else:
                    head_table = OrderedDict()
                    head_table['user'] = "USER"
                    head_table['tanggal'] = "TANGGAL"
                    head_table['branch'] = "BRANCH"
                    head_table['description'] = "DESCRIPTION"
                    body_table = []
                    for rec in data:
                        data_body = OrderedDict()
                        data_body['user'] = rec['create_user']['name']
                        data_body['tanggal'] = rec['date']
                        data_body['branch'] = rec['create_user']['branch_name']
                        data_body['description'] = rec['notes']
                        body_table.append(data_body)

            # rendered = render_template(
            #     'report_template.html', head_title=head_title, head_table=head_table,
            #     head_customer_table=head_customer_table, body_table=body_table, category="sales"
            # )
            rendered = render_template(
                'report_template.html', head_title=head_title, head_table=head_table, body_table=body_table
            )
            output = pdfkit.from_string(rendered, False)

            result['data'] = data
            result['file'] = output

        return result