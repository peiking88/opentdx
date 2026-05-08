import struct


class TdxFileNotFoundException(Exception):
    pass


class TdxNotAssignVipdocPathException(Exception):
    pass


class BaseReader:
    def __init__(self, vipdoc_path=None):
        self.vipdoc_path = vipdoc_path

    @staticmethod
    def unpack_records(fmt, data):
        record = struct.Struct(fmt)
        return (record.unpack_from(data, offset)
                for offset in range(0, len(data), record.size))

    def get_df(self, code_or_file, exchange=None):
        raise NotImplementedError("not yet")

    @staticmethod
    def _parse_date(num):
        month = (num % 2048) // 100
        year = num // 2048 + 2004
        day = (num % 2048) % 100
        return year, month, day

    @staticmethod
    def _parse_time(num):
        return (num // 60), (num % 60)
