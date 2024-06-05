import re
import json
import time
import pandas as pd
import dateutil.parser

from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql
from rest.models import ApprovalModel, BranchesModel,UserModel, EmployeeModel, DivisionModel

__author__ = 'Junior'


class ApprovalController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.approval_model = ApprovalModel()
        self.branches_model = BranchesModel()
        self.user_model = UserModel()
        self.employee_model = EmployeeModel()
        self.division_model = DivisionModel()
        self.branches_model = BranchesModel()

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
            result = self.approval_model.insert_into_db(
                self.cursor, prefix=create_data["prefix"], data_id=create_data["data_id"],
                type=create_data['type'], data=create_data["data"], create_by=user_id,
                create_date=today, update_date=today, is_approved=False, approved_by=None,
                is_rejected=False, rejected_by=None
            )
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return result

    def create_plan(self, create_data: 'dict', user_id: 'int'):
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
            result = self.approval_model.insert_into_db(
                self.cursor, prefix=create_data["prefix"], data_id=create_data["data_id"],
                type=create_data['type'], data=json.dumps(create_data["data"]), create_by=user_id,
                create_date=today, update_date=today, is_approved=False, approved_by=None,
                is_rejected=False, rejected_by=None
            )
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return result

    def get_approval_by_data_id_and_type(self, _id: str, data_type: str, prefix: str):
        """

        :param _id: str
        :param data_type: str
        :param prefix: str
        :return:
        """
        if self.is_number(_id):
            where = """WHERE `data_id` = {0} AND `type` = '{1}' AND `prefix` = '{2}'""".format(_id, data_type, prefix)
        else:
            where = """WHERE `data_id` = '{0}' AND `type` = '{1}' AND `prefix` = '{2}'""".format(_id, data_type, prefix)

        try:
            result = self.approval_model.get_all_approval(self.cursor, where=where)[0]
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return result

    def update_approval(self, update_data: 'dict'):
        """
        Update branches
        :param update_data: dict
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.approval_model.update_by_id(self.cursor, update_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return result

    def get_all_approval_data(
            self, page: int, limit: int, search: str, column: str, direction: str, prefix: str, permission: list
    ):
        """
        Get List Of branches
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: prefix: str
        :param: permission: list
        :return:
            list Branches Object
        """
        result = {}
        data = []
        start = page * limit - limit
        order = ''
        where = """WHERE `prefix` = '{}'""".format(prefix)
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        if search:
            where += """AND (type LIKE '%{0}%')""".format(search)
        approval_data = self.approval_model.get_all_approval(self.cursor, where=where, order=order,
                                                             start=start,  limit=limit)
        count_filter = self.approval_model.get_count_all_approval(self.cursor, where=where)
        count = self.approval_model.get_count_all_approval(self.cursor)
        if approval_data:
            for rec in approval_data:
                if rec['data'] is not None:
                    rec['data'] = json.loads(rec['data'])
                if rec['create_date'] is not None:
                    rec['create_date'] = str(rec['create_date'])
                if rec['update_date'] is not None:
                    rec['update_date'] = str(rec['update_date'])
                if rec['approved_date'] is not None:
                    rec['approved_date'] = str(rec['approved_date'])
                if rec['rejected_date'] is not None:
                    rec['rejected_date'] = str(rec['rejected_date'])
                if rec['create_by'] is not None:
                    try:
                        rec['create_user'] = self.user_model.get_user_by_id(
                            self.cursor, rec['create_by'], select="id, employee_id, branch_id, division_id"
                        )[0]
                        if rec['create_user']['employee_id'] is not None:
                            try:
                                rec['create_user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, rec['create_user']['employee_id'], select="name")[0]['name']
                            except:
                                rec['create_user']['employee_name'] = None
                        else:
                            rec['create_user']['employee_name'] = None
                        if rec['create_user']['branch_id'] is not None:
                            try:
                                rec['create_user']['branch_name'] = self.branches_model.get_branches_by_id(
                                    self.cursor, rec['create_user']['branch_id'], select="name")[0]['name']
                            except:
                                rec['create_user']['branch_name'] = None
                        else:
                            rec['create_user']['branch_name'] = None
                        if rec['create_user']['division_id'] is not None:
                            try:
                                rec['create_user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, rec['create_user']['division_id'], select="division_name")[0]['division_name']
                            except:
                                rec['create_user']['division_name'] = None
                        else:
                            rec['create_user']['division_name'] = None
                    except:
                        rec['create_user'] = {}
                else:
                    rec['create_user'] = {}
                if rec['approved_by'] is not None:
                    try:
                        rec['approved_user'] = self.user_model.get_user_by_id(
                            self.cursor, rec['approved_by'], select="id, employee_id, branch_id, division_id"
                        )[0]
                        if rec['approved_user']['employee_id'] is not None:
                            try:
                                rec['approved_user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, rec['approved_user']['employee_id'], select="name")[0]['name']
                            except:
                                rec['approved_user']['employee_name'] = None
                        else:
                            rec['approved_user']['employee_name'] = None
                        if rec['approved_user']['branch_id'] is not None:
                            try:
                                rec['approved_user']['branch_name'] = self.branches_model.get_branches_by_id(
                                    self.cursor, rec['approved_user']['branch_id'], select="name")[0]['name']
                            except:
                                rec['approved_user']['branch_name'] = None
                        else:
                            rec['approved_user']['branch_name'] = None
                        if rec['approved_user']['division_id'] is not None:
                            try:
                                rec['approved_user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, rec['approved_user']['division_id'], select="division_name")[0]['division_name']
                            except:
                                rec['approved_user']['division_name'] = None
                        else:
                            rec['approved_user']['division_name'] = None
                    except:
                        rec['approved_user'] = {}
                else:
                    rec['approved_user'] = {}
                if rec['rejected_by'] is not None:
                    try:
                        rec['rejected_user'] = self.user_model.get_user_by_id(
                            self.cursor, rec['rejected_by'], select="id, employee_id, branch_id, division_id"
                        )[0]
                        if rec['rejected_user']['employee_id'] is not None:
                            try:
                                rec['rejected_user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, rec['rejected_user']['employee_id'], select="name")[0]['name']
                            except:
                                rec['rejected_user']['employee_name'] = None
                        else:
                            rec['rejected_user']['employee_name'] = None
                        if rec['rejected_user']['branch_id'] is not None:
                            try:
                                rec['rejected_user']['branch_name'] = self.branches_model.get_branches_by_id(
                                    self.cursor, rec['rejected_user']['branch_id'], select="name")[0]['name']
                            except:
                                rec['rejected_user']['branch_name'] = None
                        else:
                            rec['rejected_user']['branch_name'] = None
                        if rec['rejected_user']['division_id'] is not None:
                            try:
                                rec['rejected_user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, rec['rejected_user']['division_id'], select="division_name")[0]['division_name']
                            except:
                                rec['rejected_user']['division_name'] = None
                        else:
                            rec['rejected_user']['division_name'] = None
                    except:
                        rec['rejected_user'] = {}
                else:
                    rec['rejected_user'] = {}
                if rec['is_approved'] != 1 or rec['is_rejected'] != 1:
                    if rec['type'] == 'create':
                        if permission[1] == 3:
                            rec['action_create'] = 1
                        else:
                            rec['action_create'] = 0
                    elif rec['type'] == 'edit':
                        if permission[2] == 3:
                            rec['action_edit'] = 1
                        else:
                            rec['action_edit'] = 0
                    elif rec['type'] == 'delete':
                        if permission[3] == 3:
                            rec['action_delete'] = 1
                        else:
                            rec['action_delete'] = 0
                    elif rec['type'] == 'import':
                        if permission[4] == 3:
                            rec['action_import'] = 1
                        else:
                            rec['action_import'] = 0
                    elif rec['type'] == 'print':
                        if permission[5] == 3:
                            rec['action_print'] = 1
                        else:
                            rec['action_print'] = 0
                    else:
                        rec['action_create'] = 0
                        rec['action_edit'] = 0
                        rec['action_delete'] = 0
                        rec['action_import'] = 0
                        rec['action_print'] = 0
                data.append(rec)
        result['data'] = data
        result['total'] = count
        result['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if result['total'] > page * limit:
            result['has_next'] = True
        else:
            result['has_next'] = False
        if limit <= page * count_filter - count_filter:
            result['has_prev'] = True
        else:
            result['has_prev'] = False
        return result

    def get_all_approval_data_privilege(
            self, page: int, limit: int, search: str, column: str, direction: str, prefix: str, permission: list,
            branch_privilege: dict, division_privilege: dict
    ):
        """
        Get List Of branches
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: prefix: str
        :param: permission: list
        :param: branch_privilege: dict
        :param: division_privilege: dict
        :return:
            list Branches Object
        """
        result = {}
        data = []
        start = page * limit - limit
        select = "da.*"
        select_count = "da.id"
        order = ''
        if division_privilege is not None:
            where = """WHERE (da.prefix = '{0}') AND (u.branch_id IN ({1}) AND u.division_id IN ({2}))""".format(
                prefix, ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
            )
        else:
            where = """WHERE (da.prefix = '{0}') AND (u.branch_id IN ({1}))""".format(
                prefix, ", ".join(str(x) for x in branch_privilege)
            )
        where_origin = where
        join = "AS da LEFT JOIN `users` as u ON da.create_by = u.id"
        if column:
            order = """ORDER BY da.{0} {1}""".format(column, direction)
        if search:
            where += """AND (da.type LIKE '%{0}%')""".format(search)
        approval_data = self.approval_model.get_all_approval(
            self.cursor, select=select, where=where, order=order, join=join, start=start, limit=limit
        )
        count_filter = self.approval_model.get_count_all_approval(self.cursor, select=select_count, where=where, join=join)
        count = self.approval_model.get_count_all_approval(self.cursor, select=select_count, where=where_origin, join=join)
        if approval_data:
            for rec in approval_data:
                if rec['data'] is not None:
                    rec['data'] = json.loads(rec['data'])
                if rec['create_date'] is not None:
                    rec['create_date'] = str(rec['create_date'])
                if rec['update_date'] is not None:
                    rec['update_date'] = str(rec['update_date'])
                if rec['approved_date'] is not None:
                    rec['approved_date'] = str(rec['approved_date'])
                if rec['rejected_date'] is not None:
                    rec['rejected_date'] = str(rec['rejected_date'])
                if rec['create_by'] is not None:
                    try:
                        rec['create_user'] = self.user_model.get_user_by_id(
                            self.cursor, rec['create_by'], select="id, employee_id, branch_id, division_id"
                        )[0]
                        if rec['create_user']['employee_id'] is not None:
                            try:
                                rec['create_user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, rec['create_user']['employee_id'], select="name")[0]['name']
                            except:
                                rec['create_user']['employee_name'] = None
                        else:
                            rec['create_user']['employee_name'] = None
                        if rec['create_user']['branch_id'] is not None:
                            try:
                                rec['create_user']['branch_name'] = self.branches_model.get_branches_by_id(
                                    self.cursor, rec['create_user']['branch_id'], select="name")[0]['name']
                            except:
                                rec['create_user']['branch_name'] = None
                        else:
                            rec['create_user']['branch_name'] = None
                        if rec['create_user']['division_id'] is not None:
                            try:
                                rec['create_user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, rec['create_user']['division_id'], select="division_name")[0][
                                    'division_name']
                            except:
                                rec['create_user']['division_name'] = None
                        else:
                            rec['create_user']['division_name'] = None
                    except:
                        rec['create_user'] = {}
                else:
                    rec['create_user'] = {}
                if rec['approved_by'] is not None:
                    try:
                        rec['approved_user'] = self.user_model.get_user_by_id(
                            self.cursor, rec['approved_by'], select="id, employee_id, branch_id, division_id"
                        )[0]
                        if rec['approved_user']['employee_id'] is not None:
                            try:
                                rec['approved_user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, rec['approved_user']['employee_id'], select="name")[0]['name']
                            except:
                                rec['approved_user']['employee_name'] = None
                        else:
                            rec['approved_user']['employee_name'] = None
                        if rec['approved_user']['branch_id'] is not None:
                            try:
                                rec['approved_user']['branch_name'] = self.branches_model.get_branches_by_id(
                                    self.cursor, rec['approved_user']['branch_id'], select="name")[0]['name']
                            except:
                                rec['approved_user']['branch_name'] = None
                        else:
                            rec['approved_user']['branch_name'] = None
                        if rec['approved_user']['division_id'] is not None:
                            try:
                                rec['approved_user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, rec['approved_user']['division_id'], select="division_name")[0][
                                    'division_name']
                            except:
                                rec['approved_user']['division_name'] = None
                        else:
                            rec['approved_user']['division_name'] = None
                    except:
                        rec['approved_user'] = {}
                else:
                    rec['approved_user'] = {}
                if rec['rejected_by'] is not None:
                    try:
                        rec['rejected_user'] = self.user_model.get_user_by_id(
                            self.cursor, rec['rejected_by'], select="id, employee_id, branch_id, division_id"
                        )[0]
                        if rec['rejected_user']['employee_id'] is not None:
                            try:
                                rec['rejected_user']['employee_name'] = self.employee_model.get_employee_by_id(
                                    self.cursor, rec['rejected_user']['employee_id'], select="name")[0]['name']
                            except:
                                rec['rejected_user']['employee_name'] = None
                        else:
                            rec['rejected_user']['employee_name'] = None
                        if rec['rejected_user']['branch_id'] is not None:
                            try:
                                rec['rejected_user']['branch_name'] = self.branches_model.get_branches_by_id(
                                    self.cursor, rec['rejected_user']['branch_id'], select="name")[0]['name']
                            except:
                                rec['rejected_user']['branch_name'] = None
                        else:
                            rec['rejected_user']['branch_name'] = None
                        if rec['rejected_user']['division_id'] is not None:
                            try:
                                rec['rejected_user']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, rec['rejected_user']['division_id'], select="division_name")[0][
                                    'division_name']
                            except:
                                rec['rejected_user']['division_name'] = None
                        else:
                            rec['rejected_user']['division_name'] = None
                    except:
                        rec['rejected_user'] = {}
                else:
                    rec['rejected_user'] = {}
                if rec['is_approved'] != 1 or rec['is_rejected'] != 1:
                    if rec['type'] == 'create':
                        if permission[1] == 3:
                            rec['action_create'] = 1
                        else:
                            rec['action_create'] = 0
                    elif rec['type'] == 'edit':
                        if permission[2] == 3:
                            rec['action_edit'] = 1
                        else:
                            rec['action_edit'] = 0
                    elif rec['type'] == 'delete':
                        if permission[3] == 3:
                            rec['action_delete'] = 1
                        else:
                            rec['action_delete'] = 0
                    elif rec['type'] == 'import':
                        if permission[4] == 3:
                            rec['action_import'] = 1
                        else:
                            rec['action_import'] = 0
                    elif rec['type'] == 'print':
                        if permission[5] == 3:
                            rec['action_print'] = 1
                        else:
                            rec['action_print'] = 0
                    else:
                        rec['action_create'] = 0
                        rec['action_edit'] = 0
                        rec['action_delete'] = 0
                        rec['action_import'] = 0
                        rec['action_print'] = 0
                data.append(rec)
        result['data'] = data
        result['total'] = count
        result['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if result['total'] > page * limit:
            result['has_next'] = True
        else:
            result['has_next'] = False
        if limit <= page * count_filter - count_filter:
            result['has_prev'] = True
        else:
            result['has_prev'] = False
        return result

    def get_approval_by_id(self, _id: int):
        """
        Get visit plan Information Data

        :param _id: int
        :param permission: list
        :return:
            Visit Cycle Object
        """
        result = self.approval_model.get_approval_by_id(self.cursor, _id)

        if len(result) == 0:
            raise BadRequest("This approval doesn't exist", 500, 1, data=[])
        else:
            rec = result[0]
            if rec['data'] is not None:
                rec['data'] = json.loads(rec['data'])
            if rec['create_date'] is not None:
                rec['create_date'] = str(rec['create_date'])
            if rec['update_date'] is not None:
                rec['update_date'] = str(rec['update_date'])
            if rec['approved_date'] is not None:
                rec['approved_date'] = str(rec['approved_date'])
            if rec['rejected_date'] is not None:
                rec['rejected_date'] = str(rec['rejected_date'])
            if rec['create_by'] is not None:
                try:
                    rec['create_user'] = self.user_model.get_user_by_id(
                        self.cursor, rec['create_by'], select="id, employee_id, branch_id, division_id"
                    )[0]
                    if rec['create_user']['employee_id'] is not None:
                        try:
                            rec['create_user']['employee_name'] = self.employee_model.get_employee_by_id(
                                self.cursor, rec['create_user']['employee_id'], select="name")[0]['name']
                        except:
                            rec['create_user']['employee_name'] = None
                    else:
                        rec['create_user']['employee_name'] = None
                    if rec['create_user']['branch_id'] is not None:
                        try:
                            rec['create_user']['branch_name'] = self.branches_model.get_branches_by_id(
                                self.cursor, rec['create_user']['branch_id'], select="name")[0]['name']
                        except:
                            rec['create_user']['branch_name'] = None
                    else:
                        rec['create_user']['branch_name'] = None
                    if rec['create_user']['division_id'] is not None:
                        try:
                            rec['create_user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, rec['create_user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            rec['create_user']['division_name'] = None
                    else:
                        rec['create_user']['division_name'] = None
                except:
                    rec['create_user'] = {}
            else:
                rec['create_user'] = {}
            if rec['approved_by'] is not None:
                try:
                    rec['approved_user'] = self.user_model.get_user_by_id(
                        self.cursor, rec['approved_by'], select="id, employee_id, branch_id, division_id"
                    )[0]
                    if rec['approved_user']['employee_id'] is not None:
                        try:
                            rec['approved_user']['employee_name'] = self.employee_model.get_employee_by_id(
                                self.cursor, rec['approved_user']['employee_id'], select="name")[0]['name']
                        except:
                            rec['approved_user']['employee_name'] = None
                    else:
                        rec['approved_user']['employee_name'] = None
                    if rec['approved_user']['branch_id'] is not None:
                        try:
                            rec['approved_user']['branch_name'] = self.branches_model.get_branches_by_id(
                                self.cursor, rec['approved_user']['branch_id'], select="name")[0]['name']
                        except:
                            rec['approved_user']['branch_name'] = None
                    else:
                        rec['approved_user']['branch_name'] = None
                    if rec['approved_user']['division_id'] is not None:
                        try:
                            rec['approved_user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, rec['approved_user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            rec['approved_user']['division_name'] = None
                    else:
                        rec['approved_user']['division_name'] = None
                except:
                    rec['approved_user'] = {}
            else:
                rec['approved_user'] = {}
            if rec['rejected_by'] is not None:
                try:
                    rec['rejected_user'] = self.user_model.get_user_by_id(
                        self.cursor, rec['rejected_by'], select="id, employee_id, branch_id, division_id"
                    )[0]
                    if rec['rejected_user']['employee_id'] is not None:
                        try:
                            rec['rejected_user']['employee_name'] = self.employee_model.get_employee_by_id(
                                self.cursor, rec['rejected_user']['employee_id'], select="name")[0]['name']
                        except:
                            rec['rejected_user']['employee_name'] = None
                    else:
                        rec['rejected_user']['employee_name'] = None
                    if rec['rejected_user']['branch_id'] is not None:
                        try:
                            rec['rejected_user']['branch_name'] = self.branches_model.get_branches_by_id(
                                self.cursor, rec['rejected_user']['branch_id'], select="name")[0]['name']
                        except:
                            rec['rejected_user']['branch_name'] = None
                    else:
                        rec['rejected_user']['branch_name'] = None
                    if rec['rejected_user']['division_id'] is not None:
                        try:
                            rec['rejected_user']['division_name'] = self.division_model.get_division_by_id(
                                self.cursor, rec['rejected_user']['division_id'], select="division_name")[0][
                                'division_name']
                        except:
                            rec['rejected_user']['division_name'] = None
                    else:
                        rec['rejected_user']['division_name'] = None
                except:
                    rec['rejected_user'] = {}
            else:
                rec['rejected_user'] = {}

        return rec

    def get_count_approval(self, prefix: str, create: bool, edit: bool, delete: bool):
        """

        :param prefix:
        :param create:
        :param edit:
        :param delete:
        :return:
        """
        category_type = []
        if create:
            category_type.append("create")
        if edit:
            category_type.append("edit")
        if delete:
            category_type.append("delete")
        where = """WHERE `prefix` = '{0}' AND `type` IN ('{1}') 
        AND `is_approved` = 0 AND `is_rejected` = 0""".format(prefix, "', '".join(x for x in category_type))
        count = self.approval_model.get_count_all_approval(self.cursor, where=where)
        return count

    def get_count_approval_privilege(
            self, prefix: str, create: bool, edit: bool, delete: bool, branch_privilege: dict, division_privilege: dict
    ):
        """

        :param prefix:
        :param create:
        :param edit:
        :param delete:
        :param branch_privilege:
        :param division_privilege:
        :return:
        """
        category_type = []
        if create:
            category_type.append("create")
        if edit:
            category_type.append("edit")
        if delete:
            category_type.append("delete")
        select="da.id"
        if division_privilege is not None:
            where = """WHERE da.prefix = '{0}' AND da.type IN ('{1}') 
            AND da.is_approved = 0 AND da.is_rejected = 0 
            AND (u.branch_id IN ({2}) AND u.division_id IN ({3}))""".format(
                prefix, "', '".join(x for x in category_type), ", ".join(str(x) for x in branch_privilege),
                ", ".join(str(x) for x in division_privilege)
            )
        else:
            where = """WHERE da.prefix = '{0}' AND da.type IN ('{1}') 
            AND da.is_approved = 0 AND da.is_rejected = 0 
            AND (u.branch_id IN ({2}))""".format(
                prefix, "', '".join(x for x in category_type), ", ".join(str(x) for x in branch_privilege)
            )
        join = "AS da LEFT JOIN `users` as u ON da.create_by = u.id"
        count = self.approval_model.get_count_all_approval(self.cursor, select=select, where=where, join=join)
        return count

    @staticmethod
    def is_number(s):
        if type(s) is str:
            intstr = ['Infinity', 'infinity', 'nan', 'inf', 'NAN', 'INF']
            if intstr.count(s.lower()) or re.match(r'[0-9]+(e|E)[0-9]+', s):
                return False

        try:
            float(s)
            return True
        except Exception:
            pass

        try:
            import unicodedata
            unicodedata.numeric(s)
            return True
        except Exception:
            pass

        return False