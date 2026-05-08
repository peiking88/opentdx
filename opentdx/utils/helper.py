import struct
from datetime import datetime

from opentdx.utils.log import logger

SECURITY_COEFFICIENT = {
    "SH_A_STOCK": [0.01, 0.01],
    "SH_B_STOCK": [0.001, 0.01],
    "SH_INDEX": [0.01, 1.0],
    "SH_FUND": [0.001, 1.0],
    "SH_BOND": [0.0001, 1.0],
    "SZ_A_STOCK": [0.01, 0.01],
    "SZ_B_STOCK": [0.01, 0.01],
    "SZ_INDEX": [0.01, 1.0],
    "SZ_FUND": [0.001, 0.01],
    "SZ_BOND": [0.0001, 0.01],
}


def get_price(data, pos):
    """
    解析变长有符号价格编码
    :param data: 原始数据
    :param pos: 起始位置
    :return: (价格, 新位置)
    """
    pos_byte = 6

    bdata = index_bytes(data, pos)
    int_data = bdata & 0x3F

    if bdata & 0x40:
        sign = True
    else:
        sign = False

    if bdata & 0x80:
        while True:
            pos += 1
            bdata = index_bytes(data, pos)
            int_data += (bdata & 0x7F) << pos_byte
            pos_byte += 7

            if not (bdata & 0x80):
                break

    pos += 1

    if sign:
        int_data = -int_data

    return int_data, pos


def get_volume(vol):
    """
    解码成交量（自定义浮点编码）
    :param vol: 原始 uint32
    :return: 成交量浮点数
    """
    logpoint = vol >> (8 * 3)

    hleax = (vol >> (8 * 2)) & 0xFF
    lheax = (vol >> 8) & 0xFF
    lleax = vol & 0xFF

    dw_ecx = logpoint * 2 - 0x7F
    dw_edx = logpoint * 2 - 0x86
    dw_esi = logpoint * 2 - 0x8E
    dw_eax = logpoint * 2 - 0x96

    if dw_ecx < 0:
        tmp_eax = -dw_ecx
    else:
        tmp_eax = dw_ecx

    dbl_xmm6 = pow(2.0, tmp_eax)

    if dw_ecx < 0:
        dbl_xmm6 = 1.0 / dbl_xmm6

    if hleax > 0x80:
        dwtmpeax = dw_edx + 1
        tmpdbl_xmm3 = pow(2.0, dwtmpeax)
        dbl_xmm0 = pow(2.0, dw_edx) * 128.0
        dbl_xmm0 += (hleax & 0x7F) * tmpdbl_xmm3
        dbl_xmm4 = dbl_xmm0
    else:
        if dw_edx >= 0:
            dbl_xmm0 = pow(2.0, dw_edx) * hleax
        else:
            dbl_xmm0 = (1 / pow(2.0, dw_edx)) * hleax
        dbl_xmm4 = dbl_xmm0

    dbl_xmm3 = pow(2.0, dw_esi) * lheax
    dbl_xmm1 = pow(2.0, dw_eax) * lleax

    if hleax & 0x80:
        dbl_xmm3 *= 2.0
        dbl_xmm1 *= 2.0

    return dbl_xmm6 + dbl_xmm4 + dbl_xmm3 + dbl_xmm1


def get_datetime(category, buffer, pos):
    """
    解析日期时间
    :param category: K线类别
    :param buffer: 数据
    :param pos: 起始位置
    :return: (year, month, day, hour, minute, pos)
    """
    minute = 0
    hour = 15

    if category < 4 or category == 7 or category == 8:
        zip_day, minutes = struct.unpack("<HH", buffer[pos: pos + 4])

        month = int((zip_day % 2048) / 100)
        year = (zip_day >> 11) + 2004
        day = (zip_day % 2048) % 100

        minute = minutes % 60
        hour = int(minutes / 60)
    else:
        (zip_day,) = struct.unpack("<I", buffer[pos: pos + 4])

        month = int((zip_day % 10000) / 100)
        year = int(zip_day / 10000)
        day = zip_day % 100

    pos += 4

    return year, month, day, hour, minute, pos


def get_time(buffer, pos):
    """
    解析时间
    :param buffer: 数据
    :param pos: 起始位置
    :return: (hour, minute, pos)
    """
    (minutes,) = struct.unpack("<H", buffer[pos: pos + 2])

    hour = int(minutes / 60)
    minute = minutes % 60

    pos += 2

    return hour, minute, pos


def index_bytes(data, pos):
    """
    索引字节
    :param data: 数据
    :param pos: 位置
    :return: 字节值
    """
    return data[pos]


def get_security_coefficient(market=None, code=None):
    """获取证券价格系数"""
    try:
        security_type = get_security_type(market=market, code=code)
        coefficient = SECURITY_COEFFICIENT[security_type]
        return coefficient[0]
    except NotImplementedError:
        logger.error("NotImplementedError")
        return 0.01


def get_security_type(market, code):
    """
    获取股票类型 (A股, B股, 指数等)
    :param market: 市场 (0/1 或 "SZ"/"SH")
    :param code: 代码
    :return: 证券类型字符串
    """
    code = str(code)
    code_head = str(code)[:2]

    if market in ["SZ", "sz", 0]:
        if code_head in ["00", "30"]:
            return "SZ_A_STOCK"
        if code_head in ["20"]:
            return "SZ_B_STOCK"
        if code_head in ["39"]:
            return "SZ_INDEX"
        if code_head in ["15", "16"]:
            return "SZ_FUND"
        if code_head in ["10", "11", "12", "13", "14"]:
            return "SZ_BOND"

    if market in ["SH", "sh", 1]:
        if code_head in ["60", "68"]:
            return "SH_A_STOCK"
        if code_head in ["90"]:
            return "SH_B_STOCK"
        if code_head in ["00", "88", "99"]:
            return "SH_INDEX"
        if code_head in ["50", "51"]:
            return "SH_FUND"
        if code_head in ["01", "10", "11", "12", "13", "14", "20"]:
            return "SH_BOND"

    logger.debug("Unknown security exchange !")
    raise NotImplementedError


def time_frame(current_time=None):
    """
    判断是否在交易时间段内
    :param current_time: 要检查的时间，默认当前时间
    :return: 在交易时间段内返回 True，否则返回 False
    """
    current_time = current_time or datetime.now()

    start_time = datetime.strptime(str(current_time.date()) + "9:30", "%Y-%m-%d%H:%M")
    end_time = datetime.strptime(str(current_time.date()) + "11:30", "%Y-%m-%d%H:%M")

    if start_time < current_time < end_time:
        return True

    start_time = datetime.strptime(str(current_time.date()) + "13:00", "%Y-%m-%d%H:%M")
    end_time = datetime.strptime(str(current_time.date()) + "15:00", "%Y-%m-%d%H:%M")

    if start_time < current_time < end_time:
        return True

    return False


def dump(buf):
    """调试用的 hexdump"""
    from pprint import pprint

    try:
        from hexdump import hexdump
        pprint(hexdump(buf))
    except ImportError:
        pprint(buf)
