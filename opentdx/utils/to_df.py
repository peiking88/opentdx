import pandas as pd


def to_df(v):
    """将 list/dict/None 统一转换为 DataFrame（tdxpy 兼容）"""
    if isinstance(v, pd.DataFrame):
        return v
    if isinstance(v, list):
        return pd.DataFrame(data=v)
    if isinstance(v, dict):
        return pd.DataFrame(data=[v])
    return pd.DataFrame(data=[])
