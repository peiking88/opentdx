import datetime


def parse_tdx_date(date):
    """解析通达信日期格式

    :param date: None, '', datetime.date, 或 int (如 20230501)
    :return: datetime.date or None
    """
    if date is None or date == '':
        return None
    if isinstance(date, datetime.date):
        return date
    if isinstance(date, int) and date > 0:
        s = str(date)
        return datetime.date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    return None
