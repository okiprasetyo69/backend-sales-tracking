import jwt
import json
from flask import current_app
from flask_jwt import JWTError
from rest.helpers import mysql
from rest.exceptions import BadRequest, RestException

from .model import Model
from .employee import EmployeeModel
from .branches import BranchesModel
from .division import DivisionModel
from .user_group import UserGroupModel
from passlib.hash import md5_crypt as pwd_context

__author__ = 'junior'


class User(object):
    def __init__(self, id, username, name, permissions, permissions_group, branch, division, job_function,
                 is_supervisor_sales, is_supervisor_logistic):
        self.id = id
        self.username = username
        self.name = name
        self.permissions = permissions
        self.permissions_group = permissions_group
        self.branch_privilege = branch
        self.division_privilege = division
        self.job_function = job_function
        self.is_supervisor_sales = is_supervisor_sales
        self.is_supervisor_logistic = is_supervisor_logistic

    def __str__(self):
        return "User(id='%s')" % self.id


class UserModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = "users"
        self.table_import = 'users'

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

    def insert_into_db(self, cursor, username, password, email, create_date, update_date, permissions,
                       branch_privilege_id, division_privilege_id, customer_id, employee_id, mobile_device_id,
                       mobile_no_id, printer_device_id, area_id, branch_id, user_group_id, division_id,
                       max_account_usages, is_approval, approval_by, create_by):
        try:
            value = {"username": username, "password": password, "email": email, "create_date": create_date,
                     "update_date": update_date, "permissions": permissions, "branch_privilege_id": branch_privilege_id,
                     "division_privilege_id": division_privilege_id, "customer_id": customer_id,
                     "employee_id": employee_id, "mobile_device_id": mobile_device_id, "mobile_no_id": mobile_no_id,
                     "printer_device_id": printer_device_id, "area_id": area_id, "branch_id": branch_id,
                     "user_group_id": user_group_id, "division_id": division_id,
                     "max_account_usages": max_account_usages, "is_approval": is_approval,
                     "approval_by": approval_by, "create_by": create_by}
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def update_by_id(self, cursor, user_data):
        try:
            return self.update(cursor, user_data, 'id')
        except Exception as e:
            raise e

    def get_user_by_username(self, cursor, username, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE username = '{}' AND is_deleted = 0".format(username))
        except Exception as e:
            raise e

    def get_user_by_employee(self, cursor, employee, _id=''):
        try:
            where = "WHERE `employee_id` = '{0}' AND `is_deleted` = 0".format(employee)
            if _id:
                where = "WHERE `employee_id` = '{0}' AND `id` != {1} AND `is_deleted` = 0".format(employee, _id)
            return self.get(cursor, where=where)
        except Exception as e:
            raise e

    def get_user_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE id = {}".format(_id))
        except Exception as e:
            raise e

    def get_all_user(self, cursor, start=0, limit=50, select='*', join='', where='', order=''):
        try:
            return self.get(cursor, fields=select, join=join, where=where, order=order,
                            limit="LIMIT {}, {}".format(start, limit))
        except Exception as e:
            raise e

    def get_count_all_user(self, cursor, select='id', join='', where=''):
        try:
            return self.get_sql_count_rows(cursor, key=select, join=join, where=where)
        except Exception as e:
            raise e

    def get_count_all_user_statistic(
            self, cursor, select='*', select_count='id', select_form='', join='', where='', order='', group=''
    ):
        try:
            return self.get_sql_count_statistic(
                cursor, key=select, key_count=select_count, from_select=select_form, join=join, where=where,
                order=order, group=group
            )
        except Exception as e:
            raise e

    @staticmethod
    def hash(password: str):
        return pwd_context.encrypt(password)

    @staticmethod
    def authenticate(username: 'str', password: 'str') -> 'UserModel':
        """

        :param username:
        :param password:
        :return:
        """
        cursor = mysql.connection.cursor()
        user_model = UserModel()
        employee_model = EmployeeModel()
        user_group_model = UserGroupModel()
        branches_model = BranchesModel()
        divisions_model = DivisionModel()
        user = user_model.get_user_by_username(cursor, username)

        if len(user) == 0:
            raise BadRequest("User not found", 500, 1, data=[])

        user = user[0]
        if user['employee_id'] is not None:
            employee = employee_model.get_employee_by_id(cursor, user['employee_id'])[0]
            user['name'] = employee['name']
            user['job_function'] = ("Collector" if employee['is_collector_only'] == 1 else employee['job_function'])
            user['is_supervisor_sales'] = employee['is_supervisor_sales']
            user['is_supervisor_logistic'] = employee['is_supervisor_logistic']
            # user['name'] = "Test"
        else:
            raise BadRequest("This user can't login, because hasn't been assign to employee ", 500, 1, data=[])

        if user['id'] == 1:
            data_branch = branches_model.get_all_branches_id(cursor)
            list_branch_id = []
            if data_branch:
                for rec_branch in data_branch:
                    list_branch_id.append(rec_branch['id'])
            user['branch_privilege_id'] = list_branch_id

            data_division = divisions_model.get_all_division_id(cursor)
            list_division_id = []
            if data_division:
                for rec_division in data_branch:
                    list_division_id.append(rec_division['id'])
            user['division_privilege_id'] = list_division_id
        else:
            if user['branch_privilege_id'] is not None:
                user['branch_privilege_id'] = json.loads(user['branch_privilege_id'])
            if user['division_privilege_id'] is not None:
                user['division_privilege_id'] = json.loads(user['division_privilege_id'])
        if user['user_group_id'] is not None:
            user_group = user_group_model.get_user_group_by_id(cursor, user['user_group_id'])[0]
            user['user_group'] = user_group['permissions']
            user['user_group'] = json.loads(user['user_group'])
        else:
            user['user_group'] = None

        if pwd_context.verify(password, user['password']):
            user = User(user['id'], user['username'], user['name'], json.loads(user['permissions']),
                        user['user_group'], user['branch_privilege_id'], user['division_privilege_id'],
                        user['job_function'], user['is_supervisor_sales'], user['is_supervisor_logistic'])
            return user

    @staticmethod
    def identity(payload: 'dict') -> 'UserModel':
        """

        :param payload:
        :return:
        """
        _id = payload['identity']
        cursor = mysql.connection.cursor()
        user_model = UserModel()
        employee_model = EmployeeModel()
        user_group_model = UserGroupModel()
        branches_model = BranchesModel()
        divisions_model = DivisionModel()
        user = user_model.get_user_by_id(cursor, _id)
        if len(user) == 0:
            raise BadRequest("User not found", 500, 1, data=[])
        user = user[0]
        if user['employee_id'] is not None:
            employee = employee_model.get_employee_by_id(cursor, user['employee_id'])[0]
            user['name'] = employee['name']
            user['job_function'] = employee['job_function']
            user['is_supervisor_sales'] = employee['is_supervisor_sales']
            user['is_supervisor_logistic'] = employee['is_supervisor_logistic']
            # user['name'] = "Test"
        else:
            raise BadRequest("This user hasn't been assign to employee ", 500, 1, data=[])

        if user['id'] == 1:
            data_branch = branches_model.get_all_branches_id(cursor)
            list_branch_id = []
            if data_branch:
                for rec_branch in data_branch:
                    list_branch_id.append(rec_branch['id'])
            user['branch_privilege_id'] = list_branch_id

            data_division = divisions_model.get_all_division_id(cursor)
            list_division_id = []
            if data_division:
                for rec_division in data_division:
                    list_division_id.append(rec_division['id'])
            user['division_privilege_id'] = list_division_id
        else:
            if user['branch_privilege_id'] is not None:
                user['branch_privilege_id'] = json.loads(user['branch_privilege_id'])
            if user['division_privilege_id'] is not None:
                user['division_privilege_id'] = json.loads(user['division_privilege_id'])
        if user['user_group_id'] is not None:
            user_group = user_group_model.get_user_group_by_id(cursor, user['user_group_id'])[0]
            user['user_group'] = user_group['permissions']
            user['user_group'] = json.loads(user['user_group'])
        else:
            user['user_group'] = None
        user = User(user['id'], user['username'], user['name'], json.loads(user['permissions']),
                    user['user_group'], user['branch_privilege_id'], user['division_privilege_id'],
                    user['job_function'], user['is_supervisor_sales'], user['is_supervisor_logistic'])
        return user


class DeviceTokenModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = "device_token"

    def insert_into_db(self, cursor, user_id, update_date, token):
        try:
            value = {
                "user_id": user_id, "update_date": update_date, "token": token
            }
            return self.insert_update(cursor, value, "user_id")
        except Exception as e:
            raise e

    def get_device_token_by_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE user_id = {}".format(_id))
        except Exception as e:
            raise e

    def get_device_token_by_list_id(self, cursor, _id, select='*'):
        try:
            return self.get(cursor, fields=select, where="WHERE user_id IN ({})".format(", ".join(str(x) for x in _id)))
        except Exception as e:
            raise e


class UserLoginStatusModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.table = "user_login"

    def insert_into_db(self, cursor, username, tipe_login, login_date):
        try:
            value = {
                "username": username, "type": tipe_login, "login_date": login_date
            }
            return self.insert_ignore(cursor, value)
        except Exception as e:
            raise e

    def get_user_by_user_type(self, cursor, username, tipe_login, select='*'):
        try:
            return self.get(
                cursor, fields=select, where="WHERE username = '{0}' AND type = '{1}'".format(username, tipe_login)
            )
        except Exception as e:
            raise e

    def get_user_by_username(self, cursor, username, select='*'):
        try:
            return self.get(
                cursor, fields=select, where="WHERE username = '{0}'".format(username)
            )
        except Exception as e:
            raise e
