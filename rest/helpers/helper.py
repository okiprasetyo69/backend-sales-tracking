from datetime import timedelta, datetime

__author__ = 'Junior'

USERS_NOTIF = []


def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in allowed_extensions


def date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days + 1)):
        yield start_date + timedelta(n)


def get_cycle_data(start, end, total_cycle):
    """Number of whole weeks between start and end dates."""
    weeks = 0
    start_day = start.weekday()
    end_day = end.weekday()

    start = start - timedelta(days=start_day)
    while start <= end:
        start += timedelta(weeks=1)
        weeks += 1

    cycle_number = weeks % total_cycle
    if cycle_number == 0:
        cycle_number = total_cycle
    return cycle_number, end_day


def convert_date_name(date_number):
    if date_number == 0:
        return "monday"
    elif date_number == 1:
        return "tuesday"
    elif date_number == 2:
        return "wednesday"
    elif date_number == 3:
        return "thursday"
    elif date_number == 4:
        return "friday"
    elif date_number == 5:
        return "saturday"
    elif date_number == 6:
        return "sunday"


def auto_correction_number_none(value):
    if value is not None:
        return int(value)
    else:
        return 0
