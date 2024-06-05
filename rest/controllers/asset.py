import re
import json

from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql
from rest.models import AssetModel, AssetTypeModel

__author__ = 'Junior'


class AssetsController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.assets_model = AssetModel()
        self.assets_type_model = AssetTypeModel()

    def create(self, assets_data: 'dict', user_id: 'int'):
        """
        Function for create new assets

        :param assets_data: dict
        :param user_id: int
        :return:
            assets Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.assets_model.insert_into_db(
                self.cursor, code=assets_data['code'], device_code=assets_data['device_code'], name=assets_data['name'],
                asset_type_id=assets_data['asset_type_id'], asset_status=assets_data['asset_status'],
                notes=assets_data['notes'], create_date=today, update_date=today,
                is_approval=assets_data['is_approval'], approval_by=assets_data['approval_by'], create_by=user_id
            )
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return last_insert_id

    def check_assets_by_code(self, code: str, _id: int):
        """
        Check for name assets

        :param code: int
        :param _id: int
        :return:
            assets Object
        """
        assets = self.assets_model.get_asset_by_code(self.cursor, code, _id=_id)

        if len(assets) == 0:
            return False
        else:
            return True

    def get_assets_by_id(self, _id: int):
        """
        Get assets Information Data

        :param _id: int
        :return:
            assets Object
        """
        assets = self.assets_model.get_asset_by_id(self.cursor, _id)

        if len(assets) == 0:
            raise BadRequest("This assets not exist", 200, 1, data=[])
        else:
            assets = assets[0]
            if assets['edit_data'] is not None:
                assets['edit_data'] = json.loads(assets['edit_data'])

            if assets['asset_type_id'] is not None:
                try:
                    asset_type = self.assets_type_model.get_asset_type_by_id(self.cursor, assets['asset_type_id'])[0]
                    assets['asset_type_name'] = asset_type['name']
                except:
                    assets['asset_type_name'] = None
            else:
                assets['asset_type_name'] = None

        return assets

    def get_all_assets_data(
            self, page: int, limit: int, tag: str, search: str, column: str, direction: str, dropdown: bool
    ):
        """
        Get List Of assets
        :param: page: int
        :param: limit: int
        :param: tag: str
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: dropdown: str
        :return:
            list assets Object
        """
        assets = {}
        data = []
        start = page * limit - limit
        order_flag = False
        order = ''
        where = """WHERE (is_approval = 1 AND is_deleted = 0) """
        if dropdown:
            where += """AND `asset_status` = 'active' """
        if column:
            if column == 'type':
                order_flag = True
                order = """ORDER BY at.type {0}""".format(direction)
            else:
                if search:
                    order = """ORDER BY a.{0} {1}""".format(column, direction)
                else:
                    order = """ORDER BY {0} {1}""".format(column, direction)

        if tag:
            select = "a.*"
            select_count = "a.id"
            join = """as a LEFT JOIN `asset_types` as at ON a.asset_type_id = at.id"""
            where += "AND at.tag = '{}' ".format(tag)
            assets_data = self.assets_model.get_all_asset(self.cursor, select=select, join=join, where=where,
                                                           start=start, limit=limit)
            count_filter = self.assets_model.get_count_all_asset(self.cursor, select=select_count,
                                                                  join=join, where=where)
            count = count_filter
        else:

            if search or order_flag:
                select = "a.*"
                select_count = "a.id"
                join = """as a LEFT JOIN `asset_types` as at ON a.asset_type_id = at.id"""
                if search:
                    where += """AND (a.code LIKE '%{0}%' OR a.name LIKE '%{0}%' OR a.asset_status LIKE '%{0}%' 
                    OR at.name LIKE '%{0}%')""".format(search)
                assets_data = self.assets_model.get_all_asset(self.cursor, select=select, join=join, where=where,
                                                               order=order, start=start, limit=limit)
                count_filter = self.assets_model.get_count_all_asset(self.cursor, select=select_count,
                                                                      join=join, where=where)
                count = self.assets_model.get_count_all_asset(self.cursor)
            else:
                assets_data = self.assets_model.get_all_asset(self.cursor, start=start, limit=limit, where=where,
                                                              order=order)
                count = self.assets_model.get_count_all_asset(self.cursor, where=where)
                count_filter = count

        if assets_data:
            for emp in assets_data:
                if emp['edit_data'] is not None:
                    emp['edit_data'] = json.loads(emp['edit_data'])
                if emp['create_date'] is not None:
                    emp['create_date'] = str(emp['create_date'])
                if emp['update_date'] is not None:
                    emp['update_date'] = str(emp['update_date'])
                if emp['asset_type_id'] is not None:
                    try:
                        asset_type = self.assets_type_model.get_asset_type_by_id(self.cursor, emp['asset_type_id'])[0]
                        emp['asset_type_name'] = asset_type['name']
                    except:
                        emp['asset_type_name'] = None
                else:
                    emp['asset_type_name'] = None
                data.append(emp)

        assets['data'] = data
        assets['total'] = count
        assets['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if assets['total'] > page * limit:
            assets['has_next'] = True
        else:
            assets['has_next'] = False
        if limit <= page * count - count:
            assets['has_prev'] = True
        else:
            assets['has_prev'] = False
        return assets

    def get_all_assets_type_data(self, page: int, limit: int, tag: str, search: str, column: str, direction: str):
        """
        Get List Of assets
        :param: page: int
        :param: limit: int
        :param: tag: str
        :return:
            list assets Object
        """
        assets = {}
        data = []
        start = page * limit - limit
        order = ''
        # select = """*"""
        where = """WHERE isActive = {0}""".format('1')
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)

        assets_data = self.assets_type_model.get_all_asset_type(self.cursor, where=where, order=order, start=start, limit=limit)
        count_filter = self.assets_type_model.get_count_all_asset_type(self.cursor, where=where)
        count = count_filter

        if assets_data:
            for emp in assets_data:
                data.append(emp)

        assets['data'] = data
        assets['total'] = count
        assets['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if assets['total'] > page * limit:
            assets['has_next'] = True
        else:
            assets['has_next'] = False
        if limit <= page * count - count:
            assets['has_prev'] = True
        else:
            assets['has_prev'] = False
        return assets

    def update_assets(self, assets_data: 'dict', _id: 'int'):
        """
        Update assets
        :param assets_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.assets_model.update_by_id(self.cursor, assets_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def rollback_insert(self, _id: 'int'):
        """
        Rollback insert branches
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            query = "DELETE from `assets` WHERE id = {}".format(_id)
            result = self.cursor.execute(query=query)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result