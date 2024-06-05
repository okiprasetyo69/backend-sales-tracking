import re
import json
import base64
import pandas as pd
import dateutil.parser

from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql
from rest.models import BranchesModel, CompanyModel, DivisionModel, ApprovalModel

__author__ = 'Junior'


class BranchesController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.branches_model = BranchesModel()
        self.company_model = CompanyModel()
        self.division_model = DivisionModel()
        self.approval_model = ApprovalModel()

    def create(self, branches_data: 'dict', user_id: 'int'):
        """
        Function for create new branches

        :param branches_data: dict
        :param user_id: int
        :return:
            Branches Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.branches_model.insert_into_db(self.cursor, name=branches_data['name'],
                                                        branch_code=branches_data['branch_code'],
                                                        phone=branches_data['phone'], email=branches_data['email'],
                                                        address=branches_data['address'], lng=branches_data['lng'],
                                                        lat=branches_data['lat'],
                                                        working_day_start=branches_data['working_day_start'],
                                                        working_day_end=branches_data['working_day_end'],
                                                        working_hour_start=branches_data['working_hour_start'],
                                                        working_hour_end=branches_data['working_hour_end'],
                                                        area_id=branches_data['area_id'],
                                                        division_id=branches_data['division_id'],
                                                        create_date=today, update_date=today,
                                                        is_approval=branches_data['is_approval'],
                                                        approval_by=branches_data['approval_by'], create_by=user_id)
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return last_insert_id

    def import_branch(self, file, user_id: 'int'):
        """
        import sales payment
        :param file: file
        :param user_id: int
        :return:
        """
        headers = ['Branch Code', 'Name', 'Phone', 'Email', 'Address', 'Longitude', 'Latitude', 'Working Day Start',
                   'Working Day End', 'Working Hour Start', 'Working Hour End', 'Division ID']
        batch_data = []
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        df = pd.read_excel(file, sheet_name=0, skiprows=0)
        for idx in df.columns:
            if idx not in headers:
                raise BadRequest('Wrong header name', 422, 1, data=[{'header': idx}])

        # TODO: Get Parent Sales Order
        df_parent = df[
            ['Branch Code', 'Name', 'Phone', 'Email', 'Address', 'Longitude', 'Latitude', 'Working Day Start',
             'Working Day End', 'Working Hour Start', 'Working Hour End', 'Division ID']
        ]
        df_parent.set_index("Branch Code", inplace=True)
        df_parent = df_parent.groupby('Branch Code').last()
        df_parent.columns = ['name', 'phone', 'email', 'address', 'lng', 'lat', 'working_day_start', 'working_day_end',
                             'working_hour_start', 'working_hour_end', 'division_id']
        df_parent.index.names = ['branch_code']

        df_parent_json = df_parent.to_json(orient='index', date_format='iso')
        df_parent_json = json.loads(df_parent_json)

        for key, val in df_parent_json.items():
            value = val
            value['branch_code'] = key[:2]
            data_division = []
            if value['division_id'] is not None:
                array_division = value['division_id'].split(', ')
                print(array_division)
                for rec in array_division:
                    try:
                        division_id = self.division_model.get_division_by_code(
                            self.cursor, code=rec, _id=None
                        )[0]
                        data_division.append(division_id['id'])
                    except:
                        print("not found division")
            value['division_id'] = data_division
            value['create_date'] = today
            value['update_date'] = today
            # value['import_by'] = user_id
            value['create_by'] = user_id
            value['approval_by'] = user_id
            value['is_approval'] = True
            batch_data.append(value)

        for rec in batch_data:
            try:
                result = self.branches_model.import_insert(self.cursor, rec, 'branch_code')
                mysql.connection.commit()
            except Exception as e:
                # raise BadRequest(e, 200, 1, data=[])
                pass

        return True

    def import_branch_file(self, filename: str, filename_origin: str, table: str, user_id: int):
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
            result = self.branches_model.import_insert_file(self.cursor, file_name=filename,
                                                            file_name_origin=filename_origin, table=table,
                                                            create_date=today, update_date=today, create_by=user_id)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def check_branches_by_name(self, name: str, _id: int):
        """
        Check for name branches

        :param name: str
        :param _id: int
        :return:
            Branches Object
        """
        branches = self.branches_model.get_branches_by_name(self.cursor, name, _id)

        if len(branches) == 0:
            return False
        else:
            return True

    def check_branches_by_code(self, code: str, _id: int):
        """
        Check for name branches

        :param name: str
        :param _id: int
        :return:
            Branches Object
        """
        branches = self.branches_model.get_branches_by_code(self.cursor, code, _id)

        if len(branches) == 0:
            return False
        else:
            return True

    def get_branches_by_id(self, _id: int):
        """
        Get branches Information Data

        :param _id: int
        :return:
            Branches Object
        """
        branches = self.branches_model.get_branches_by_id(self.cursor, _id)

        if len(branches) == 0:
            raise BadRequest("This branches not exist", 200, 1, data=[])
        else:
            branches = branches[0]
            if branches['edit_data'] is not None:
                branches['edit_data'] = json.loads(branches['edit_data'])
            if branches['division_id'] is not None:
                branches['division_id'] = json.loads(branches['division_id'])
            if branches['working_hour_start'] is not None:
                branches['working_hour_start'] = str(branches['working_hour_start'])
            if branches['working_hour_end'] is not None:
                branches['working_hour_end'] = str(branches['working_hour_end'])

        return branches

    def get_all_branches_data(
            self, page: int, limit: int, search: str, column: str, direction: str, dropdown: bool,
            branch_privilege: list
    ):
        """
        Get List Of branches
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :return:
            list Branches Object
        """
        branches = {}
        data = []
        start = page * limit - limit
        order = ''
        where = """WHERE (is_approval = 1 AND is_deleted = 0) """
        if dropdown:
            where += "AND id IN ({0}) ".format(
                ", ".join(str(x) for x in branch_privilege)
            )
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        if search:
            where += """AND (branch_code LIKE '%{0}%' OR name LIKE '%{0}%' 
            OR phone LIKE '%{0}%' OR address LIKE '%{0}%')""".format(search)
        branches_data = self.branches_model.get_all_branches(self.cursor, where=where, order=order,
                                                             start=start,  limit=limit)
        count_filter = self.branches_model.get_count_all_branches(self.cursor, where=where)
        count = self.branches_model.get_count_all_branches(self.cursor)
        if branches_data:
            for emp in branches_data:
                if emp['edit_data'] is not None:
                    emp['edit_data'] = json.loads(emp['edit_data'])
                if emp['division_id'] is not None:
                    emp['division_id'] = json.loads(emp['division_id'])
                if emp['working_hour_start'] is not None:
                    emp['working_hour_start'] = str(emp['working_hour_start'])
                if emp['working_hour_end'] is not None:
                    emp['working_hour_end'] = str(emp['working_hour_end'])
                data.append(emp)
        branches['data'] = data
        branches['total'] = count
        branches['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if branches['total'] > page * limit:
            branches['has_next'] = True
        else:
            branches['has_next'] = False
        if limit <= page * count - count:
            branches['has_prev'] = True
        else:
            branches['has_prev'] = False
        return branches

    def get_all_branches_data_cycle(self, page: int, limit: int, search: str, column: str, direction: str):
        """
        Get List Of branches
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :return:
            list Branches Object
        """
        branches = {}
        company = {}
        data = []
        company_data = self.company_model.get_company_by_id(self.cursor, 1)[0]
        company['id'] = 0
        company['name'] = company_data['name']
        data.append(company)
        start = page * limit - limit
        order = ''
        where = 'WHERE (is_approval = 1 AND is_deleted = 0) '
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        if search:
            where += """AND (branch_code LIKE '%{0}%' OR name LIKE '%{0}%' 
            OR phone LIKE '%{0}%' OR address LIKE '%{0}%')""".format(search)
        branches_data = self.branches_model.get_all_branches(self.cursor, where=where, order=order,
                                                             start=start,  limit=limit)
        count = self.branches_model.get_count_all_branches(self.cursor)
        if branches_data:
            for emp in branches_data:
                data_employee = {}
                data_employee['id'] = emp['id']
                data_employee['name'] = emp['name']
                data.append(data_employee)
        branches['data'] = data
        branches['total'] = count

        # TODO: Check Has Next and Prev
        if branches['total'] > page * limit:
            branches['has_next'] = True
        else:
            branches['has_next'] = False
        if limit <= page * count - count:
            branches['has_prev'] = True
        else:
            branches['has_prev'] = False
        return branches

    def update_branches(self, branches_data: 'dict', _id: 'int'):
        """
        Update branches
        :param branches_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.branches_model.update_by_id(self.cursor, branches_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])

        return result

    def get_branches_delete_count(self, code: 'str'):
        """
        Update division
        :param code: str
        :return:
            Message Boolean Success or Failure
        """
        try:
            select = "is_delete_count"
            where = "WHERE `branch_code` = '{}' AND `is_deleted` = 1".format(code)
            order = "ORDER BY is_delete_count DESC"
            count = self.branches_model.get_all_branches(
                self.cursor, select=select, where=where, order=order, start=0, limit=1000)[0]
        except Exception as e:
            count = {
                "is_delete_count": 0
            }

        return count['is_delete_count']

    def rollback_insert(self, _id: 'int'):
        """
        Rollback insert branches
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            query = "DELETE from `branches` WHERE id = {}".format(_id)
            result = self.cursor.execute(query=query)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_all_branch_import(self):
        """
        Get List Of import branch
        :return:
            list Sales Orders Object
        """
        import_file = {}
        data = []
        import_data = self.branches_model.get_all_branch_import(self.cursor, where="""WHERE `status` = 0 
        AND `table_name` = 'branches'""")
        count = self.branches_model.get_count_all_branch_import(self.cursor, key="id", where="""WHERE `status` = 0 
        AND `table_name` = 'branches'""")
        if import_data:
            for emp in import_data:
                data.append(emp)
        import_file['data'] = data
        import_file['total'] = count

        # TODO: Check Has Next and Prev
        import_file['has_next'] = False
        import_file['has_prev'] = False
        return import_file

    # TODO: using for general purpose
    def get_import_file(self, _id: int):
        """
        Get import by id

        :param _id: int
        :return:
            area Object
        """
        import_file = self.branches_model.get_import_by_id(self.cursor, _id)

        if len(import_file) == 0:
            raise BadRequest("This import file not exist", 200, 1, data=[])
        else:
            import_file = import_file[0]

        return import_file

    def update_import_file(self, _id: int, user_id: int):
        """
        Get area Information Data

        :param _id: int
        :param user_id: int
        :return:
            area Object
        """
        try:
            result = self.branches_model.update_import_by_id(self.cursor, _id, user_id)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_list_all_branch_id(self):
        """
        Get List All Branch ID
        :return:
            list id
        """
        try:
            query = "SELECT id from `branches` "
            self.cursor.execute(query)
            branch = self.cursor.fetchall()
            list_id = []
            for data in branch:
                list_id.append(data['id'])
        except Exception as e:
            raise BadRequest(e, 422, 1)

        return list_id
