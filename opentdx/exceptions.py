class TdxConnectionError(Exception):
    """连接服务器出错时抛出"""
    pass


class TdxFunctionCallError(Exception):
    """函数调用出错时抛出"""

    def __init__(self, *args):
        super().__init__(*args)
        self.original_exception = None


class ValidationException(Exception):
    """参数验证异常"""
    pass
