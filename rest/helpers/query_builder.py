import pymysql
import re
import json

__author__ = 'junior'


class NoChange:
    def __init__(self):
        pass


class QueryBuilder:
    no_change = True

    def __init__(self):
        pass

    def insert(self, data, table_name, ignore=False):
        global sql
        ignore_str = ""
        if ignore: ignore_str = "IGNORE"
        try:
            keys = data.keys()
            fields = ", ".join(keys)

            sql = "INSERT {0} INTO ".format(ignore_str)
            sql += table_name
            sql += " (" + fields + ") "
            sql += "VALUES "
            sql += "(" + self.value_insert(data, keys) + ")"
            # :debug for query insert:
            # print(sql)
            return sql
        except Exception as e:
            raise e

    def value_insert(self, data, keys):
        values = list()
        for key in keys:
            # try:
            #     data[key] = str(data[key].encode('utf-8'))
            # except:
            #     pass

            if isinstance(data[key], dict):
                if "inc" in data[key]:
                    values.append(str(data[key]["inc"]))
                elif "dec" in data[key]:
                    values.append(str(data[key]["dec"]))
                else:
                    values.append("'{0}'".format(json.dumps(data[key])))
            elif isinstance(data[key], list):
                values.append("'{0}'".format(json.dumps(data[key])))
            elif data[key] is None or data[key] == "":
                values.append('NULL')
            elif self.is_number(data[key]):
                values.append('{0}'.format(data[key]))
            else:
                values.append('"{0}"'.format(pymysql.escape_string(data[key])))
        value = ", ".join(values)
        # :debug for value of query insert:
        # print("query builder : " ,value)
        return value

    def value_insert_batch(self, batch_data, keys):
        values = list()
        batch_values = list()
        for data in batch_data:
            for key in keys:
                # try:
                #     data[key] = str(data[key].encode('utf-8'))
                # except:
                #     pass

                if isinstance(data[key], dict):
                    if "inc" in data[key]:
                        values.append(str(data[key]["inc"]))
                    elif "dec" in data[key]:
                        values.append(str(data[key]["dec"]))
                    else:
                        values.append("'{0}'".format(json.dumps(data[key])))
                elif isinstance(data[key], list):
                    values.append("'{0}'".format(json.dumps(data[key])))
                elif data[key] is None or data[key] == "":
                    values.append('NULL')
                elif self.is_number(data[key]):
                    values.append('{0}'.format(data[key]))
                else:
                    values.append('"{0}"'.format(pymysql.escape_string(data[key])))
            value = ", ".join(values)

            value = "({})".format(value)
            batch_values.append(value)
        batch_values = ", ".join(batch_values)
        # :debug for value of query insert:
        # print(value)
        return batch_values

    def insert_update_clean(self, data, key, table_name):
        return pymysql.escape_string(self.insert_update(data, key, table_name))

    def insert_update(self, data, key, table_name, exclude_field=''):
        global sql
        try:
            keys = data.keys()
            fields = "`, `".join(keys)

            sql = "INSERT INTO "
            sql += table_name
            sql += " (`" + fields + "`) "
            sql += "VALUES "
            sql += "(" + self.value_insert(data, keys) + ") "
            sql += "ON DUPLICATE KEY UPDATE "
            sql += self.value_update(data, key, exclude_field)
            return sql
        except Exception as e:
            raise e

    def insert_update_batch(self, batch_data, table_name, exclude_field=''):
        global sql
        try:
            keys = batch_data[0].keys()
            fields = "`, `".join(keys)

            sql = "INSERT INTO "
            sql += table_name
            sql += " (`" + fields + "`) "
            sql += "VALUES "
            sql += self.value_insert_batch(batch_data, keys)
            # sql += "(" + self.value_insert(data, keys) + ") "
            sql += "ON DUPLICATE KEY UPDATE "
            sql += self.value_duplicate(keys, exclude_field)
            return sql
        except Exception as e:
            raise e

    def update_clean(self, data, table, key):
        return pymysql.escape_string(self.update(data, table, key))

    def update(self, data, table, key, commit=False):
        global sql
        try:
            sql = "UPDATE {0} SET ".format(table)
            sql += self.value_update(data, key)
            sql += " WHERE {0} = '{1}'".format(key, data[key])
            return sql
        except Exception as e:
            raise e

    def update_key(self, data, table, key, key2, val, commit=False):
        global sql
        try:
            sql = "UPDATE {0} SET ".format(table)
            sql += self.value_update(data, key)
            sql += " WHERE {0} = '{1}'".format(key, data[key])
            sql += " AND {0} = '{1}'".format(key2, val)
            return sql
        except Exception as e:
            raise e

    def truncate(self, table):
        global sql
        try:
            sql = "TRUNCATE TABLE {0}".format(table)
            return sql
        except Exception as e:
            raise e

    def value_update(self, data, primary, exclude_field=''):
        try:
            primaries = primary.replace(' ', '').split(',')
            # print(primaries)
            exclude_fields = exclude_field.replace(' ', '').split(',')
            sets = list()
            keys = data.keys()
            for key in keys:
                if key not in primaries or isinstance(key, NoChange) or key not in exclude_fields:
                    if data[key] is not None and data[key] != "":
                        # try:
                        #     data[key] = data[key].encode('utf-8')
                        # except Exception:
                        #     pass

                        if isinstance(data[key], dict):
                            if "inc" in data[key]:
                                sets.append('`{0}` = {0} + {1}'.format(str(key), data[key]["inc"]))
                            elif "dec" in data[key]:
                                sets.append('`{0}` = {0} - {1}'.format(str(key), data[key]["dec"]))
                            else:
                                sets.append("`{0}` = '{1}'".format(str(key), json.dumps(data[key])))
                        elif isinstance(data[key], list):
                            sets.append("`{0}` = '{1}'".format(str(key), json.dumps(data[key])))
                        elif self.is_number(data[key]):
                            sets.append('`{0}` = {1}'.format(str(key), data[key]))
                        else:
                            sets.append('`{0}` = "{1}"'.format(str(key), pymysql.escape_string(data[key])))
                    else:
                        sets.append('`{}` = NULL'.format(str(key)))

            return ", ".join(sets)
        except Exception as e:
            raise e

    def value_duplicate(self, keys, exclude_field=''):
        try:
            exclude_fields = exclude_field.replace(' ', '').split(',')
            sets = list()
            for key in keys:
                if isinstance(key, NoChange) or key not in exclude_fields:
                    sets.append("{0}=VALUES({0})".format(key))

            return ", ".join(sets)
        except Exception as e:
            raise e

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