import re
import json
import time
import pandas as pd
import dateutil.parser

from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template
from passlib.hash import md5_crypt as pwd_context

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql
from rest.models import UserModel, UserGroupModel, BranchesModel, AreaModel, EmployeeModel, DivisionModel, AssetModel, \
    CustomerModel, DeviceTokenModel, GeneralModel, UserLoginStatusModel

__author__ = 'Junior'

username_validation = re.compile(r"^[a-zA-Z0-9_]+$")
email_validation = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", re.VERBOSE)


class UserController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.user_model = UserModel()
        self.user_group_model = UserGroupModel()
        self.employee_model = EmployeeModel()
        self.branches_model = BranchesModel()
        self.division_model = DivisionModel()
        self.customer_model = CustomerModel()
        self.general_model = GeneralModel()
        self.area_model = AreaModel()
        self.asset_model = AssetModel()
        self.token_model = DeviceTokenModel()
        self.user_login_model = UserLoginStatusModel()

    def import_user(self, file, user_id: 'int'):
        """
        import User
        :param file: file
        :param user_id: int
        :return:
        """
        headers = ['Username', 'email']
        batch_data = []
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        df = pd.read_excel(file, sheet_name=0, skiprows=0)
        for idx in df.columns:
            if idx not in headers:
                raise BadRequest('Wrong header name', 422, 1, data=[{'header': idx}])

        # TODO: Get Parent Sales Order
        df_parent = df[['Username', 'email']]
        df_parent.set_index("Username", inplace=True)
        df_parent.columns = ['email']
        df_parent.index.names = ['username']

        df_parent_json = df_parent.to_json(orient='index', date_format='iso')
        df_parent_json = json.loads(df_parent_json)

        for key, val in df_parent_json.items():
            value = val
            value['username'] = key
            value['create_date'] = today
            value['update_date'] = today
            value['is_approval'] = True
            value['approval_by'] = user_id
            value['permissions'] = current_app.config['PERMISSION_CONFIGURATION']
            batch_data.append(value)

        # truncate = self.so_model.delete_table(self.cursor)

        for rec in batch_data:
            try:
                result = self.user_model.import_insert(self.cursor, rec, 'username')
                mysql.connection.commit()
            except Exception as e:
                # raise BadRequest(e, 200, 1, data=[])
                pass

        return True

    def import_user_file(self, filename: str, filename_origin: str, table: str, user_id: int):
        """

        :param filename:
        :param filename_origin:
        :param table:
        :param user_id:
        :return:
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        try:
            result = self.user_model.import_insert_file(self.cursor, file_name=filename,
                                                        file_name_origin=filename_origin, table=table,
                                                        create_date=today, update_date=today, create_by=user_id)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def create(self, user_data: 'dict', user_id: 'int'):
        """
        Function for create new user

        :param user_data: dict
        :param user_id: int
        :return:
            User Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        try:
            result = self.user_model.insert_into_db(
                self.cursor, username=user_data['username'], password=self.user_model.hash(user_data['password']),
                email=user_data['email'], create_date=today, update_date=today, permissions=user_data['permissions'],
                branch_privilege_id=user_data['branch_privilege_id'],
                division_privilege_id=user_data['division_privilege_id'], customer_id=user_data['customer_id'],
                employee_id=user_data['employee_id'], mobile_device_id=user_data['mobile_device_id'],
                mobile_no_id=user_data['mobile_no_id'], printer_device_id=user_data['printer_device_id'],
                area_id=user_data['area_id'], branch_id=user_data['branch_id'],
                user_group_id=user_data['user_group_id'], division_id=user_data['division_id'],
                max_account_usages=user_data['max_account_usages'], is_approval=user_data['is_approval'],
                approval_by=user_data['approval_by'], create_by=user_id
            )
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return last_insert_id

    def create_user_group(self, user_group_data: 'dict', user_id: 'int'):
        """
        Function for create new user_group
        :param user_group_data: dict
        :param user_id: int
        :return:
            User Group Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        try:
            result = self.user_group_model.insert_into_db(
                self.cursor, group_name=user_group_data['group_name'], code=user_group_data['code'],
                have_asset=user_group_data['have_asset'], asset=user_group_data['asset'], create_date=today,
                update_date=today, permissions=user_group_data['permissions'],
                is_approval=user_group_data['is_approval'], approval_by=user_group_data['approval_by'],
                create_by=user_id
            )
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return last_insert_id

    def username_already_use(self, username: 'str', _id: 'int'):
        try:
            if _id:
                self.cursor.execute('''SELECT username FROM users 
                WHERE username = "{0}" AND id != {1} AND `is_deleted` = 0 '''.format(username, _id))
            else:
                self.cursor.execute(
                    '''SELECT username FROM users WHERE username = "{0}" AND `is_deleted` = 0 '''.format(username))
            result = self.cursor.fetchall()
            return len(result) != 0
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

    def email_already_use(self, email: 'str', _id: 'int'):
        try:
            if _id:
                self.cursor.execute('''SELECT email FROM users WHERE email = "{0}" AND id != {1}'''.format(email, _id))
            else:
                self.cursor.execute('''SELECT email FROM users WHERE email = "{0}"'''.format(email))
            result = self.cursor.fetchall()
            return len(result) != 0
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

    def check_user_by_employee(self, employee: int, _id: int):
        """
        Check for name division

        :param employee: int
        :param _id: int
        :return:
            division Object
        """
        user = self.user_model.get_user_by_employee(self.cursor, employee, _id)

        if len(user) == 0:
            return False
        else:
            return True

    def check_user_by_id(self, _id: int):
        """
        Check for user by id

        :param _id: int
        :return:
            User Object
        """
        user = self.user_model.get_user_by_id(self.cursor, _id)

        if len(user) == 0:
            return False
        else:
            return True

    def create_login_status(self, username: str, tipe_login: str):
        """
        Function for create user login status

        :param username: dict
        :param tipe_login: int
        :return:
            User Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        try:
            result = self.user_login_model.insert_into_db(
                self.cursor, username=username, tipe_login=tipe_login, login_date=today
            )
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return result

    def check_user_is_login(self, username: str, tipe_login: str):
        """
        Check for user is login

        :param username: str
        :param tipe_login: str
        :return:
            boolean status
        """
        user = self.user_login_model.get_user_by_user_type(self.cursor, username, tipe_login)

        if len(user) == 0:
            return False
        else:
            return True

    def get_user_login_data(self, username: str):
        """
        Get User Information Data

        :param username: str
        :return:
            User Object
        """
        data = []
        user = self.user_login_model.get_user_by_username(self.cursor, username)

        if len(user) == 0:
            pass
            # raise BadRequest("This User not exist", 422, 1)
        else:
            for rec in user:
                data.append(rec)

        return data

    def delete_user_login(self, username: str, tipe_login: str):
        """
        Rollback insert branches
        :param username: int
        :param tipe_login: str
        :return:
            Message Boolean Success or Failure
        """
        try:
            query = "DELETE from `user_login` WHERE username = '{0}' AND type = '{1}'".format(username, tipe_login)
            result = self.cursor.execute(query=query)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def delete_all_user_login(self):
        """
        Rollback insert branches
        :param username: int
        :param tipe_login: str
        :return:
            Message Boolean Success or Failure
        """
        try:
            query = "TRUNCATE TABLE `user_login`"
            result = self.cursor.execute(query=query)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_user_data(self, username: str):
        """
        Get User Information Data

        :param username: str
        :return:
            User Object
        """
        user = self.user_model.get_user_by_username(self.cursor, username)

        if len(user) == 0:
            raise BadRequest("This User not exist", 200, 1)
        else:
            user = user[0]
            if user['permissions'] is not None:
                user['permissions'] = json.loads(user['permissions'])
            if user['handle_division_id'] is not None:
                user['handle_division_id'] = json.loads(user['handle_division_id'])
            if user['edit_data'] is not None:
                user['edit_data'] = json.loads(user['edit_data'])

        return user

    def get_user_group_by_name(self, name: str):
        """
        Get User Group Information Data

        :param name: int
        :return:
            User Group Object
        """
        user_group = self.user_group_model.get_user_group_by_name(self.cursor, name)

        if len(user_group) == 0:
            raise BadRequest("This User not exist", 200, 1)
        else:
            user_group = user_group[0]
            if user_group['permissions'] is not None:
                user_group['permissions'] = json.loads(user_group['permissions'])
            if user_group['asset'] is not None:
                user_group['asset'] = json.loads(user_group['asset'])
            if user_group['edit_data'] is not None:
                user_group['edit_data'] = json.loads(user_group['edit_data'])

        return user_group

    def check_user_group_by_name(self, name: str, _id: int):
        """
        Get User Group Information Data

        :param name: str
        :param _id: int
        :return:
            User Group Object
        """
        user_group = self.user_group_model.get_user_group_by_name(self.cursor, name, _id)

        if len(user_group) == 0:
            return False
        else:
            return True

    def get_user_data_login(self, username: str):
        """
        Get User Information Data

        :param username: str
        :return:
            User Object
        """

        general = self.general_model.get_general_by_id(self.cursor, 1)
        if len(general) == 0:
            raise BadRequest("This Company not exist", 200, 1, data=[])
        else:
            general = general[0]
            if general['visit_cycle_start'] is not None:
                general['visit_cycle_start'] = str(general['visit_cycle_start'])

        user = self.user_model.get_user_by_username(self.cursor, username)

        if len(user) == 0:
            raise BadRequest("Wrong username or password", 500, 1, data=[])
        else:
            user = user[0]
            if user['employee_id'] is not None:
                employee = self.employee_model.get_employee_by_id(self.cursor, user['employee_id'])[0]
            else:
                employee = None
            if user['mobile_no_id'] is not None:
                try:
                    user['mobile_no'] = self.asset_model.get_asset_by_id(self.cursor, user['mobile_no_id'],
                                                                         select="id, code, device_code, name")[0]
                except:
                    user['mobile_no'] = {}
            else:
                user['mobile_no'] = {}
            if user['branch_id'] is not None:
                try:
                    user['branch'] = self.branches_model.get_branches_by_id(self.cursor, user['branch_id'],
                                                                            select="id, name")[0]
                except:
                    user['branch'] = {}
            else:
                user['branch'] = {}
            if user['division_id'] is not None:
                try:
                    user['division'] = self.division_model.get_division_by_id(self.cursor, user['division_id'],
                                                                              select="id, division_code, division_name")[
                        0]
                except:
                    user['division'] = {}
            else:
                user['division'] = {}
            if user['permissions'] is not None:
                user['permissions'] = json.loads(user['permissions'])
            if user['branch_privilege_id'] is not None:
                user['branch_privilege_id'] = json.loads(user['branch_privilege_id'])
            if user['division_privilege_id'] is not None:
                user['division_privilege_id'] = json.loads(user['division_privilege_id'])
            user['employee'] = employee
            user['setting'] = {
                "max_length_visit_time": general['max_length_visit_time'],
                "max_length_unloading": general['max_length_unloading'],
                "max_breaktime_time": general['max_breaktime_time'],
                "max_idle_time": general['max_idle_time'],
                "alert_wrong_route": general['alert_wrong_route'],
                "alert_break_time": general['alert_break_time']
            }

        return user

    def get_user_by_id(self, _id: int):
        """
        Get User Information Data

        :param _id: int
        :return:
            User Object
        """
        user = self.user_model.get_user_by_id(self.cursor, _id)

        if len(user) == 0:
            raise BadRequest("This User not exist", 200, 1)
        else:
            user = user[0]
            if user['permissions'] is not None:
                # TODO: raw from database
                user['permissions'] = json.loads(user['permissions'])
                # TODO: Change format into list
                # user_permission = json.loads(user['permissions'])
                # # for up in user_permission:
                # #     print(up)
                # user['permissions'] = []
                # keys_parent = user_permission.copy().keys()
                # print(keys_parent)
                # i = 0
                # for key in keys_parent:
                #     value = dict()
                #     value['name'] = user_permission[key]['name']
                #     value['code'] = key
                #     value['rule-view'] = user_permission[key]['rule-view']
                #     user['permissions'].insert(i, value)
                #     i += 1
                #     if user_permission[key].get('data'):
                #         keys_child = user_permission[key]['data'].keys()
                #         for k in keys_child:
                #             value = dict()
                #             value['name'] = user_permission[key]['data'][k]['name']
                #             value['code'] = k
                #             value['rule-view'] = user_permission[key]['data'][k]['rule-view']
                #             user['permissions'].insert(i, value)
                #             i += 1
                #             if user_permission[key]['data'][k].get('data'):
                #                 keys_last = user_permission[key]['data'][k]['data'].keys()
                #                 for kl in keys_last:
                #                     value = dict()
                #                     value['name'] = user_permission[key]['data'][k]['data'][kl]['name']
                #                     value['code'] = kl
                #                     value['rule-view'] = user_permission[key]['data'][k]['data'][kl]['rule-view']
                #                     value['rule'] = user_permission[key]['data'][k]['data'][kl]['rule']
                #                     user['permissions'].insert(i, value)
                #                     i += 1

            if user['handle_division_id'] is not None:
                user['handle_division_id'] = json.loads(user['handle_division_id'])
            if user['edit_data'] is not None:
                user['edit_data'] = json.loads(user['edit_data'])

            if user['branch_privilege_id'] is not None:
                user['branch_privilege_id'] = json.loads(user['branch_privilege_id'])
                user['branch_privilege'] = []
                for rec in user['branch_privilege_id']:
                    try:
                        user['branch_privilege'].append(
                            self.branches_model.get_branches_by_id(self.cursor, rec, select="id, name")[0])
                    except:
                        pass
            else:
                user['branch_privilege'] = []

            if user['division_privilege_id'] is not None:
                user['division_privilege_id'] = json.loads(user['division_privilege_id'])
                user['division_privilege'] = []
                for rec in user['division_privilege_id']:
                    try:
                        user['division_privilege'].append(
                            self.division_model.get_division_by_id(self.cursor, rec, select="id, division_name")[0])
                    except:
                        pass
            else:
                user['division_privilege'] = []

            if user['customer_id'] is not None:
                user['customer_id'] = json.loads(user['customer_id'])
                user['customer'] = []
                for rec in user['customer_id']:
                    try:
                        user['customer'].append(
                            self.customer_model.get_customer_by_id(self.cursor, rec, select="code, name, email, phone, "
                                                                                            "address, lng, lat, nfcid, "
                                                                                            "parent_code")[0])
                    except:
                        pass

            else:
                user['customer'] = []

            if user['branch_id'] is not None:
                try:
                    user['branch'] = self.branches_model.get_branches_by_id(self.cursor, user['branch_id'],
                                                                            select="id, name, phone, email, address, "
                                                                                   "lng, lat, working_day_start, "
                                                                                   "working_day_end, working_hour_start, "
                                                                                   "working_hour_end, nfcid, area_id, "
                                                                                   "division_id")[0]
                except:
                    user['branch'] = {}
                if user['branch']['working_hour_start'] is not None:
                    user['branch']['working_hour_start'] = str(user['branch']['working_hour_start'])
                if user['branch']['working_hour_end'] is not None:
                    user['branch']['working_hour_end'] = str(user['branch']['working_hour_end'])
                if user['branch']['division_id'] is not None:
                    user['branch']['division_id'] = json.loads(user['branch']['division_id'])
                    user['branch']['division'] = []
                    for rec in user['branch']['division_id']:
                        user['branch']['division'].append(self.division_model.get_division_by_id(
                            self.cursor, rec, select="id, division_name, division_code")[0])
            else:
                user['branch'] = {}
            if user['employee_id'] is not None:
                try:
                    user['employee'] = self.employee_model.get_employee_by_id(
                        self.cursor, user['employee_id'], select="id, name, nip, email, phone, job_function")[0]
                except:
                    user['employee'] = {}
            else:
                user['employee'] = {}
            if user['user_group_id'] is not None:
                try:
                    user['user_group'] = self.user_group_model.get_user_group_by_id(
                        self.cursor, user['user_group_id'], select="id, group_name, code, have_asset, asset")[0]
                except:
                    user['user_group'] = {}
                if user['user_group']['asset'] is not None:
                    user['user_group']['asset'] = json.loads(user['user_group']['asset'])
            else:
                user['user_group'] = {}
            if user['area_id'] is not None:
                try:
                    user['area'] = self.area_model.get_area_by_id(
                        self.cursor, user['area_id'],
                        select="id, name, marker_type, marker_color, markers, description")[0]
                except:
                    user['area'] = {}
                if user['area']['markers'] is not None:
                    user['area']['markers'] = json.loads(user['area']['markers'])
            else:
                user['area'] = {}

            if user['mobile_device_id'] is not None:
                try:
                    user['mobile_device'] = self.asset_model.get_asset_by_id(self.cursor, user['mobile_device_id'],
                                                                             select="id, code, device_code, name")[0]
                except:
                    user['mobile_device'] = {}
            else:
                user['mobile_device'] = {}

            if user['mobile_no_id'] is not None:
                try:
                    user['mobile_no'] = self.asset_model.get_asset_by_id(self.cursor, user['mobile_no_id'],
                                                                         select="id, code, device_code, name")[0]
                except:
                    user['mobile_no'] = {}
            else:
                user['mobile_no'] = {}

            if user['printer_device_id'] is not None:
                try:
                    user['printer_device'] = self.asset_model.get_asset_by_id(self.cursor, user['printer_device_id'],
                                                                              select="id, code, device_code, name")[0]
                except:
                    user['printer_device'] = {}
            else:
                user['printer_device'] = {}

        return user

    def get_user_group_by_id(self, _id: int):
        """
        Get User Group Information Data

        :param _id: int
        :return:
            User Group Object
        """
        user_group = self.user_group_model.get_user_group_by_id(self.cursor, _id)

        if len(user_group) == 0:
            raise BadRequest("This User not exist", 200, 1, data=[])
        else:
            user_group = user_group[0]
            if user_group['permissions'] is not None:
                user_group['permissions'] = json.loads(user_group['permissions'])
            if user_group['asset'] is not None:
                user_group['asset'] = json.loads(user_group['asset'])
            if user_group['edit_data'] is not None:
                user_group['edit_data'] = json.loads(user_group['edit_data'])

        return user_group

    def get_all_user_data(self, page: int, limit: int, search: str, column: str, direction: str):
        """
        Get List Of User
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :return:
            list User Object
        """
        user = {}
        data = []
        start = page * limit - limit
        where = """WHERE u.is_approval = 1 AND u.is_deleted = 0 """
        where_original = where
        order = ''
        if column:
            if column == 'employee':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'user_group':
                order = """ORDER BY ug.group_name {0}""".format(direction)
            elif column == 'division':
                order = """ORDER BY d.division_name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY b.name {0}""".format(direction)
            else:
                order = """ORDER BY u.{0} {1}""".format(column, direction)
        select = "u.*"
        select_count = "u.id"
        join = """as u LEFT JOIN `employee` as e ON u.employee_id = e.id 
        LEFT JOIN `branches` as b ON u.branch_id = b.id 
        LEFT JOIN `divisions` as d ON u.division_id = d.id 
        LEFT JOIN `user_groups` as ug ON u.user_group_id = ug.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR u.email LIKE '%{0}%' OR b.name LIKE '%{0}%' OR d.division_name LIKE '%{0}%' 
            OR ug.group_name LIKE '%{0}%' OR e.name LIKE '%{0}%')""".format(search)
        user_data = self.user_model.get_all_user(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.user_model.get_count_all_user(self.cursor, select=select_count, join=join, where=where)
        count = self.user_model.get_count_all_user(self.cursor, select=select_count, join=join, where=where_original)

        if user_data:
            for u in user_data:
                if u['permissions'] is not None:
                    u['permissions'] = json.loads(u['permissions'])
                if u['division_id'] is not None:
                    try:
                        u['division'] = self.division_model.get_division_by_id(
                            self.cursor, u['division_id'], select="id, division_code, division_name"
                        )[0]
                    except:
                        u['division'] = {}
                else:
                    u['division'] = {}
                if u['branch_id'] is not None:
                    try:
                        u['branch'] = self.branches_model.get_branches_by_id(
                            self.cursor, u['branch_id'], select="id, branch_code, name, phone, email, address, lng, "
                                                                "lat, working_day_start, working_day_end, "
                                                                "working_hour_start, working_hour_end, nfcid, "
                                                                "area_id, division_id"
                        )[0]
                    except:
                        u['branch'] = {}
                    if u['branch']['working_hour_start'] is not None:
                        u['branch']['working_hour_start'] = str(u['branch']['working_hour_start'])
                    if u['branch']['working_hour_end'] is not None:
                        u['branch']['working_hour_end'] = str(u['branch']['working_hour_end'])
                    if u['branch']['division_id'] is not None:
                        u['branch']['division_id'] = json.loads(u['branch']['division_id'])
                else:
                    u['branch'] = {}
                if u['employee_id'] is not None:
                    try:
                        u['employee'] = self.employee_model.get_employee_by_id(
                            self.cursor, u['employee_id'], select="id, name, nip, email, phone, job_function"
                        )[0]
                    except:
                        u['employee'] = {}
                else:
                    u['employee'] = {}
                if u['user_group_id'] is not None:
                    try:
                        u['user_group'] = self.user_group_model.get_user_group_by_id(self.cursor, u['user_group_id'],
                                                                                     select="id, group_name, code, "
                                                                                            "have_asset, asset")[0]
                    except:
                        u['user_group'] = {}
                    if u['user_group']['asset'] is not None:
                        u['user_group']['asset'] = json.loads(u['user_group']['asset'])
                else:
                    u['user_group'] = {}
                if u['area_id'] is not None:
                    try:
                        u['area'] = self.area_model.get_area_by_id(self.cursor, u['area_id'],
                                                                   select="id, name, marker_type, marker_color, "
                                                                          "markers, description")[0]
                    except:
                        u['area'] = {}
                    if u['area']['markers'] is not None:
                        u['area']['markers'] = json.loads(u['area']['markers'])
                else:
                    u['area'] = {}
                data.append(u)
        user['data'] = data
        user['total'] = count
        user['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if user['total'] > page * limit:
            user['has_next'] = True
        else:
            user['has_next'] = False
        if limit <= page * count - count:
            user['has_prev'] = True
        else:
            user['has_prev'] = False
        return user

    def get_all_user_sales_data(
            self, page: int, limit: int, search: str, column: str, direction: str,
            branch_privilege: list, division_privilege: list, data_filter: list
    ):
        """
        Get List Of User
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: branch_privilege: list
        :param: division_privilege: list
        :param: data_filter: list
        :return:
            list User Object
        """
        user = {}
        data = []
        start = page * limit - limit
        where = """WHERE (e.job_function = 'sales' AND u.branch_id IN ({0}) AND u.division_id IN ({1}) 
        AND u.is_approval = 1 AND u.is_deleted = 0) """.format(
            ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
        )
        where_original = where
        order = ''
        if column:
            if column == 'employee':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'user_group':
                order = """ORDER BY ug.group_name {0}""".format(direction)
            elif column == 'division':
                order = """ORDER BY d.division_name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY b.name {0}""".format(direction)
            else:
                order = """ORDER BY u.{0} {1}""".format(column, direction)

        select = "u.*"
        select_count = "u.id"
        join = """as u LEFT JOIN `employee` as e ON u.employee_id = e.id 
        LEFT JOIN `branches` as b ON u.branch_id = b.id 
        LEFT JOIN `divisions` as d ON u.division_id = d.id 
        LEFT JOIN `user_groups` as ug ON u.user_group_id = ug.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR u.email LIKE '%{0}%' OR b.name LIKE '%{0}%' OR d.division_name LIKE '%{0}%' 
            OR ug.group_name LIKE '%{0}%' OR e.name LIKE '%{0}%') """.format(search)
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['user_id']:
                where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in data_filter['user_id']))
            if data_filter['branch_id']:
                where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['branch_id']))
            if data_filter['division_id']:
                where += """AND u.division_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['division_id']))
        user_data = self.user_model.get_all_user(
            self.cursor, select=select, join=join, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.user_model.get_count_all_user(self.cursor, select=select_count, join=join, where=where)
        count = self.user_model.get_count_all_user(self.cursor, select=select_count, join=join, where=where_original)

        if user_data:
            for u in user_data:
                if u['permissions'] is not None:
                    u['permissions'] = json.loads(u['permissions'])
                if u['division_id'] is not None:
                    try:
                        u['division'] = self.division_model.get_division_by_id(
                            self.cursor, u['division_id'], select="id, division_code, division_name"
                        )[0]
                    except:
                        u['division'] = {}
                else:
                    u['division'] = {}
                if u['branch_id'] is not None:
                    try:
                        u['branch'] = self.branches_model.get_branches_by_id(
                            self.cursor, u['branch_id'], select="id, branch_code, name, phone, email, address, lng, "
                                                                "lat, working_day_start, working_day_end, "
                                                                "working_hour_start, working_hour_end, nfcid, "
                                                                "area_id, division_id"
                        )[0]
                    except:
                        u['branch'] = {}
                    if u['branch']['working_hour_start'] is not None:
                        u['branch']['working_hour_start'] = str(u['branch']['working_hour_start'])
                    if u['branch']['working_hour_end'] is not None:
                        u['branch']['working_hour_end'] = str(u['branch']['working_hour_end'])
                    if u['branch']['division_id'] is not None:
                        u['branch']['division_id'] = json.loads(u['branch']['division_id'])
                else:
                    u['branch'] = {}
                if u['employee_id'] is not None:
                    try:
                        u['employee'] = self.employee_model.get_employee_by_id(
                            self.cursor, u['employee_id'],
                            select="id, name, nip, email, phone, job_function, is_collector_only, is_can_collect"
                        )[0]
                    except:
                        u['employee'] = {}
                else:
                    u['employee'] = {}
                if u['user_group_id'] is not None:
                    try:
                        u['user_group'] = self.user_group_model.get_user_group_by_id(self.cursor, u['user_group_id'],
                                                                                     select="id, group_name, code, "
                                                                                            "have_asset, asset")[0]
                    except:
                        u['user_group'] = {}
                    if u['user_group']['asset'] is not None:
                        u['user_group']['asset'] = json.loads(u['user_group']['asset'])
                else:
                    u['user_group'] = {}
                if u['area_id'] is not None:
                    try:
                        u['area'] = self.area_model.get_area_by_id(self.cursor, u['area_id'],
                                                                   select="id, name, marker_type, marker_color, "
                                                                          "markers, description")[0]
                    except:
                        u['area'] = {}
                    if u['area']['markers'] is not None:
                        u['area']['markers'] = json.loads(u['area']['markers'])
                else:
                    u['area'] = {}
                data.append(u)
        user['data'] = data
        user['total'] = count
        user['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if user['total'] > page * limit:
            user['has_next'] = True
        else:
            user['has_next'] = False
        if limit <= page * count - count:
            user['has_prev'] = True
        else:
            user['has_prev'] = False
        return user

    def get_all_user_logistic_data(self, page: int, limit: int, search: str, column: str, direction: str,
                                   branch_privilege: list, data_filter: list):
        """
        Get List Of User
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: branch_privilege: list
        :param: division_privilege: list
        :return:
            list User Object
        """
        user = {}
        data = []
        start = page * limit - limit
        where = """WHERE (e.job_function = 'driver' AND u.branch_id IN ({0}) 
        AND u.is_approval = 1 AND u.is_deleted = 0) """.format(
            ", ".join(str(x) for x in branch_privilege)
        )
        where_original = where
        order = ''
        if column:
            if column == 'employee':
                order = """ORDER BY e.name {0}""".format(direction)
            elif column == 'user_group':
                order = """ORDER BY ug.group_name {0}""".format(direction)
            elif column == 'division':
                order = """ORDER BY d.division_name {0}""".format(direction)
            elif column == 'branch':
                order = """ORDER BY b.name {0}""".format(direction)
            else:
                order = """ORDER BY u.{0} {1}""".format(column, direction)

        select = "u.*"
        select_count = "u.id"
        join = """as u LEFT JOIN `employee` as e ON u.employee_id = e.id 
        LEFT JOIN `branches` as b ON u.branch_id = b.id 
        LEFT JOIN `divisions` as d ON u.division_id = d.id 
        LEFT JOIN `user_groups` as ug ON u.user_group_id = ug.id"""
        if search:
            where += """AND (u.username LIKE '%{0}%' OR u.email LIKE '%{0}%' OR b.name LIKE '%{0}%' OR d.division_name LIKE '%{0}%' 
            OR ug.group_name LIKE '%{0}%' OR e.name LIKE '%{0}%')""".format(search)
        if data_filter:
            data_filter = data_filter[0]
            if data_filter['user_id']:
                where += """AND u.id IN ({0}) """.format(", ".join(str(x) for x in data_filter['user_id']))
            if data_filter['branch_id']:
                where += """AND u.branch_id IN ({0}) """.format(", ".join(str(x) for x in data_filter['branch_id']))

        user_data = self.user_model.get_all_user(self.cursor, select=select, join=join, where=where, order=order,
                                                 start=start, limit=limit)
        count_filter = self.user_model.get_count_all_user(self.cursor, select=select_count, join=join, where=where)
        count = self.user_model.get_count_all_user(self.cursor, select=select_count, join=join, where=where_original)

        if user_data:
            for u in user_data:
                if u['permissions'] is not None:
                    u['permissions'] = json.loads(u['permissions'])
                if u['division_id'] is not None:
                    try:
                        u['division'] = self.division_model.get_division_by_id(
                            self.cursor, u['division_id'], select="id, division_code, division_name"
                        )[0]
                    except:
                        u['division'] = {}
                else:
                    u['division'] = {}
                if u['branch_id'] is not None:
                    try:
                        u['branch'] = self.branches_model.get_branches_by_id(
                            self.cursor, u['branch_id'], select="id, branch_code, name, phone, email, address, lng, "
                                                                "lat, working_day_start, working_day_end, "
                                                                "working_hour_start, working_hour_end, nfcid, "
                                                                "area_id, division_id"
                        )[0]
                    except:
                        u['branch'] = {}
                    if u['branch']['working_hour_start'] is not None:
                        u['branch']['working_hour_start'] = str(u['branch']['working_hour_start'])
                    if u['branch']['working_hour_end'] is not None:
                        u['branch']['working_hour_end'] = str(u['branch']['working_hour_end'])
                    if u['branch']['division_id'] is not None:
                        u['branch']['division_id'] = json.loads(u['branch']['division_id'])
                else:
                    u['branch'] = {}
                if u['employee_id'] is not None:
                    try:
                        u['employee'] = self.employee_model.get_employee_by_id(
                            self.cursor, u['employee_id'], select="id, name, nip, email, phone, job_function"
                        )[0]
                    except:
                        u['employee'] = {}
                else:
                    u['employee'] = {}
                if u['user_group_id'] is not None:
                    try:
                        u['user_group'] = self.user_group_model.get_user_group_by_id(self.cursor, u['user_group_id'],
                                                                                     select="id, group_name, code, "
                                                                                            "have_asset, asset")[0]
                    except:
                        u['user_group'] = {}
                    if u['user_group']['asset'] is not None:
                        u['user_group']['asset'] = json.loads(u['user_group']['asset'])
                else:
                    u['user_group'] = {}
                if u['area_id'] is not None:
                    try:
                        u['area'] = self.area_model.get_area_by_id(self.cursor, u['area_id'],
                                                                   select="id, name, marker_type, marker_color, "
                                                                          "markers, description")[0]
                    except:
                        u['area'] = {}
                    if u['area']['markers'] is not None:
                        u['area']['markers'] = json.loads(u['area']['markers'])
                else:
                    u['area'] = {}
                data.append(u)
        user['data'] = data
        user['total'] = count
        user['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if user['total'] > page * limit:
            user['has_next'] = True
        else:
            user['has_next'] = False
        if limit <= page * count - count:
            user['has_prev'] = True
        else:
            user['has_prev'] = False
        return user

    def get_all_user_group_data(self, page: int, limit: int, search: str, column: str, direction: str):
        """
        Get List Of User Group
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :return:
            list User Group Object
        """
        user_group = {}
        data = []
        start = page * limit - limit
        order = ''
        where = 'WHERE is_approval = 1 AND is_deleted = 0 '
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        if search:
            where += """AND (group_name LIKE '%{0}%' OR code LIKE '%{0}%')""".format(search)
        user_group_data = self.user_group_model.get_all_user_group(
            self.cursor, start=start, limit=limit, order=order, where=where
        )
        count_filter = self.user_group_model.get_count_all_user_group(self.cursor, where=where)
        count = self.user_group_model.get_count_all_user_group(self.cursor)
        if user_group_data:
            for ug in user_group_data:
                if ug['permissions'] is not None:
                    ug['permissions'] = json.loads(ug['permissions'])
                if ug['asset'] is not None:
                    ug['asset'] = json.loads(ug['asset'])
                if ug['edit_data'] is not None:
                    ug['edit_data'] = json.loads(ug['edit_data'])
                data.append(ug)
        user_group['data'] = data
        user_group['total'] = count
        user_group['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if user_group['total'] > page * limit:
            user_group['has_next'] = True
        else:
            user_group['has_next'] = False
        if limit <= page * count - count:
            user_group['has_prev'] = True
        else:
            user_group['has_prev'] = False
        return user_group

    def update_user(self, user_data: 'dict', _id: 'int'):
        """
        Update User
        :param user_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:

            result = self.user_model.update_by_id(self.cursor, user_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)
        return result

    def get_user_delete_count(self, username: 'str'):
        """
        Update visit cycle
        :param username: 'str'
        :return:
            Message Boolean Success or Failure
        """
        try:
            select = "is_delete_count"
            where = "WHERE `id` = {0} AND `is_deleted` = 1".format(username)
            order = "ORDER BY is_delete_count DESC"
            count = self.user_model.get_all_user(
                self.cursor, select=select, where=where, order=order, start=0, limit=1000)[0]
        except Exception as e:
            count = {
                "is_delete_count": 0
            }

        return count['is_delete_count']

    def rollback_user_insert(self, _id: 'int'):
        """
        Rollback insert branches
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            query = "DELETE from `users` WHERE id = {}".format(_id)
            result = self.cursor.execute(query=query)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def update_user_groups(self, user_group_data: 'dict', _id: 'int'):
        """
        Update User Groups
        :param user_group_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.user_group_model.update_by_id(self.cursor, user_group_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_user_group_delete_count(self, group_name: 'str'):
        """
        Update visit cycle
        :param group_name: 'str'
        :return:
            Message Boolean Success or Failure
        """
        try:
            select = "is_delete_count"
            where = "WHERE `group_name` = {0} AND `is_deleted` = 1".format(group_name)
            order = "ORDER BY is_delete_count DESC"
            count = self.user_group_model.get_all_user_group(
                self.cursor, select=select, where=where, order=order, start=0, limit=1000)[0]
        except Exception as e:
            count = {
                "is_delete_count": 0
            }

        return count['is_delete_count']

    def rollback_user_group_insert(self, _id: 'int'):
        """
        Rollback insert branches
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            query = "DELETE from `users_groups` WHERE id = {}".format(_id)
            result = self.cursor.execute(query=query)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def update_device_token(self, update_data: 'dict'):
        """
        Update device token
        :param update_data:
        :return:
            Message Boolean Success or Failure
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        try:
            result = self.token_model.insert_into_db(
                self.cursor, user_id=update_data['user_id'], update_date=today, token=update_data['token']
            )
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def get_device_token_by_id(self, _id: int):
        """
        Get Device Token Information Data

        :param _id: int
        :return:
            Device Token Object
        """
        result = self.token_model.get_device_token_by_id(self.cursor, _id)

        if len(result) == 0:
            raise BadRequest("This User not exist", 200, 1, data=[])
        else:
            result = result[0]

        return result

    def get_device_token_by_list_id(self, list_id: list):
        """
        Get Device Token Information Data

        :param list_id: list
        :return:
            Device Token Object
        """
        result = self.token_model.get_device_token_by_list_id(self.cursor, list_id)
        if len(result) == 0:
            # raise BadRequest("This User not exist", 200, 1, data=[])
            result = False
        else:
            result = result

        return result

    def delete_device_token(self, user_id: int):
        """
        Rollback insert branches
        :param user_id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            query = "DELETE from `device_token` WHERE user_id = {0}".format(user_id)
            result = self.cursor.execute(query=query)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_supervisor_by_id(self, _id: int, category: str):
        """

        :param _id: int
        :param category: str
        :return:
        """
        list_supervisor = []

        user = self.user_model.get_user_by_id(self.cursor, _id)

        if len(user) == 0:
            raise BadRequest("This User not exist", 200, 1)
        else:
            user = user[0]
            if category == "sales":
                select = "u.id"
                join = "AS u LEFT JOIN `employee` AS e ON u.employee_id = e.id "
                where = """WHERE JSON_CONTAINS(u.branch_privilege_id, '[{0}]') 
                AND u.is_deleted = 0 AND u.is_approval = 1
                AND e.job_function = 'supervisor' AND e.is_supervisor_sales = 1""".format(user['branch_id'])
                all_supervisor = self.user_model.get_all_user(
                    self.cursor, select=select, where=where, join=join
                )

                for rec in all_supervisor:
                    list_supervisor.append(rec['id'])
            elif category == "logistic":
                select = "u.id"
                join = "AS u LEFT JOIN `employee` AS e ON u.employee_id = e.id "
                where = """WHERE JSON_CONTAINS(u.branch_privilege_id, '[{0}]') 
                AND u.is_deleted = 0 AND u.is_approval = 1 
                AND e.job_function = 'supervisor' AND e.is_supervisor_logistic = 1""".format(user['branch_id'])
                all_supervisor = self.user_model.get_all_user(
                    self.cursor, select=select, where=where, join=join
                )

                for rec in all_supervisor:
                    list_supervisor.append(rec['id'])

        return list_supervisor

    def get_customer_from_supervisor(self, branch_privilege: list, division_privilege: list, category: str):
        """

        :param branch_privilege: list
        :param division_privilege: list
        :param category: str
        :return:
        """
        list_customer = []

        if category == "sales":
            select = "u.customer_id"
            join = "AS u LEFT JOIN `employee` AS e ON u.employee_id = e.id "
            where = """WHERE u.is_deleted = 0 AND u.is_approval = 1 AND u.branch_id IN ({0}) AND u.division_id IN ({1}) 
            AND e.job_function = 'sales' AND e.is_deleted = 0 AND e.is_approval = 1 """.format(
                ", ".join(str(x) for x in branch_privilege), ", ".join(str(x) for x in division_privilege)
            )
            all_customer = self.user_model.get_all_user(
                self.cursor, select=select, where=where, join=join
            )
            for rec in all_customer:
                if rec['customer_id']:
                    cust = json.loads(rec['customer_id'])
                    for c in cust:
                        list_customer.append(c)
            unique_customer = set(list_customer)
        elif category == "logistic":
            select = "u.customer_id"
            join = "AS u LEFT JOIN `employee` AS e ON u.employee_id = e.id "
            where = """WHERE u.is_deleted = 0 AND u.is_approval = 1 AND u.branch_id IN ({0}) 
            AND ( e.job_function = 'driver' OR e.job_function = 'driver' ) AND 
            e.is_deleted = 0 AND e.is_approval = 1 """.format(
                ", ".join(str(x) for x in branch_privilege)
            )
            all_customer = self.user_model.get_all_user(
                self.cursor, select=select, where=where, join=join
            )
            for rec in all_customer:
                if rec['customer_id']:
                    cust = json.loads(rec['customer_id'])
                    for c in cust:
                        list_customer.append(c)
            unique_customer = set(list_customer)
        elif category == "all":
            select = "u.customer_id"
            join = "AS u LEFT JOIN `employee` AS e ON u.employee_id = e.id "
            where = """WHERE u.is_deleted = 0 AND u.is_approval = 1 AND u.branch_id IN ({0}) 
            AND ( e.job_function = 'sales' OR e.job_function = 'driver' OR e.job_function = 'driver' ) AND 
            e.is_deleted = 0 AND e.is_approval = 1 """.format(
                ", ".join(str(x) for x in branch_privilege)
            )
            all_customer = self.user_model.get_all_user(
                self.cursor, select=select, where=where, join=join
            )
            for rec in all_customer:
                if rec['customer_id']:
                    cust = json.loads(rec['customer_id'])
                    for c in cust:
                        list_customer.append(c)
            unique_customer = set(list_customer)
        else:
            unique_customer = []

        return unique_customer

    def get_user_customer(self, customer_id: any):
        where = "WHERE customer_id LIKE '%{0}%'".format(
            customer_id
        )
        data_user = self.user_model.get_all_user(
            self.cursor, where=where
        )
        return data_user

    def update_user_customer(self, update_data: 'dict', _id: 'int'):
        try:

            result = self.user_model.update_by_id(self.cursor, update_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)
        return result
