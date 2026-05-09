class TdxError(Exception):
    """所有 TDX 异常的基类"""
    pass


class TdxConnectionError(TdxError):
    """连接服务器出错时抛出"""
    pass


class TdxFunctionCallError(TdxError):
    """函数调用出错时抛出（解析失败、解压失败等）"""

    def __init__(self, *args):
        super().__init__(*args)
        self.original_exception = None


class ValidationException(TdxError):
    """参数验证异常"""
    pass
