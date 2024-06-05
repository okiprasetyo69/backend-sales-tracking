import re
import json

username_validation = re.compile(r"^[a-zA-Z0-9_]+$")
code_validation = re.compile(r"^[a-zA-Z0-9_\-]+$")
email_validation = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", re.VERBOSE)
invalid_format = ["'", '"', "\\", "/"]

safe_invalid_format_message = ", ".join(invalid_format)[0:-len(", " + invalid_format[-1])] + ", and " + invalid_format[
    -1]


def safe_format(value):
    safe_format_status = False
    invalid_format_count = 0
    for f in invalid_format:
        if f in value:
            invalid_format_count += 1
    if invalid_format_count == 0:
        safe_format_status = True
    return safe_format_status


class Validator:

    def __init__(self):
        pass

    def validator_field(self, data, rule):
        response = []
        keys = data.keys()
        rule_key = rule.keys()
        for key in keys:
            if key in rule_key:
                error = dict()
                if data[key] and data[key] is not None and data[key] != "":
                    if rule[key].get('numeric'):
                        if not self.is_number(data[key]):
                            error['field'] = key
                            error['message'] = 'Must be numeric'
                            response.append(error)
                    if rule[key].get('max'):
                        if len(data[key]) > rule[key]['max']:
                            error['field'] = key
                            error['message'] = 'Max character exceeds, maximum {} character allowed'.format(
                                rule[key]['max'])
                            response.append(error)
                    if rule[key].get('min'):
                        if len(data[key]) < rule[key]['min']:
                            error['field'] = key
                            error['message'] = 'Minimum {} character allowed'.format(rule[key]['min'])
                            response.append(error)
                    if rule[key].get('alpha_num'):
                        if not data[key].isalnum():
                            error['field'] = key
                            error['message'] = 'Must be alpha numeric, allowed character a-z A-Z 0-9'
                            response.append(error)
                    if rule[key].get('code_format'):
                        if not code_validation.match(data[key]):
                            error['field'] = key
                            error['message'] = 'Allowed character a-z A-Z 0-9 _ -'
                            response.append(error)
                    if rule[key].get('email_format'):
                        if not email_validation.match(data[key]):
                            error['field'] = key
                            error['message'] = "Your email is not valid "
                            response.append(error)
                    if rule[key].get('username_format'):
                        if not username_validation.match(data[key]):
                            error['field'] = key
                            error['message'] = "Username format not valid allowed character a-z A-Z 0-9 _ "
                            response.append(error)
                    if rule[key].get('safe_format'):
                        if not safe_format(data[key]):
                            error['field'] = key
                            error[
                                'message'] = "Format not valid character such as " + safe_invalid_format_message + " is not allowed"
                            response.append(error)
                else:
                    if rule[key].get('required'):
                        if isinstance(data[key], list):
                            if len(data[key]) == 0:
                                error['field'] = key
                                error['message'] = "Please select at least 1 item"
                        else:
                            error['field'] = key
                            error['message'] = "Can't contains null value"
                        response.append(error)
        print(response)
        return response

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
