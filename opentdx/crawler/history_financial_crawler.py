import secrets
import shutil
import tempfile
from pathlib import Path
from struct import calcsize, unpack

import pandas as pd

from opentdx.exceptions import ValidationException
from opentdx.crawler.base_crawler import BaseCrawler

VALUE = "<6s1c1L"


class HistoryFinancialListCrawler(BaseCrawler):
    """获取历史财务数据文件列表"""

    mode = "content"

    def get_url(self, *args, **kwargs):
        return "https://gitee.com/yutiansut/QADATA/raw/master/financial/content.txt"

    def get_content(self, reporthook=None, path_to_download=None, proxies=None, chunksize=1024 * 50, *args, **kwargs):
        content_bytes = kwargs.get("content_bytes")
        if content_bytes:
            download_file = (
                not path_to_download and tempfile.NamedTemporaryFile(delete=True) or open(path_to_download, "wb")
            )
            download_file.write(content_bytes)
            download_file.seek(0)
            return download_file

        raise ValidationException("content_bytes is required for HistoryFinancialListCrawler")

    def parse(self, download_file, *args, **kwargs):
        content = download_file.read()
        content = content.decode("utf-8")

        def list_to_dict(li):
            return {"filename": li[0], "hash": li[1], "filesize": int(li[2])}

        result = [list_to_dict(x) for x in [line.strip().split(",") for line in content.strip().split("\n")]]

        return result


class HistoryFinancialCrawler(BaseCrawler):
    """下载并解析历史财务数据"""

    mode = "content"

    def get_url(self, *args, **kwargs):
        if "filename" not in kwargs:
            raise ValidationException("Param filename is not set")

        filename = kwargs["filename"]
        return f"http://data.yutiansut.com/{filename}"

    def get_content(self, reporthook=None, path_to_download=None, proxies=None, chunksize=1024 * 50, *args, **kwargs):
        content_bytes = kwargs.get("content_bytes")
        if content_bytes:
            download_file = (
                path_to_download and open(path_to_download, "wb") or tempfile.NamedTemporaryFile(delete=True)
            )
            download_file.write(content_bytes)
            download_file.seek(0)
            return download_file

        raise ValidationException("content_bytes is required for HistoryFinancialCrawler")

    def parse(self, download_file, *args, **kwargs):
        tmpdir = None
        header_pack_format = "<1hI1H3L"

        if download_file.name.endswith(".zip"):
            tmpdir_root = tempfile.gettempdir()
            subdir_name = f"tdxpy_{secrets.randbelow(1000000)}"

            tmpdir = Path(tmpdir_root, subdir_name)
            shutil.rmtree(tmpdir, ignore_errors=True)

            tmpdir.mkdir(parents=True, exist_ok=True)
            shutil.unpack_archive(download_file.name, extract_dir=tmpdir)

            dat_file = None

            for _file in tmpdir.iterdir():
                if str(_file).endswith(".dat"):
                    dat_file = open(str(_file), "rb")

            if not dat_file:
                raise ValidationException("no dat file found in zip archive")
        else:
            dat_file = download_file

        header_size = calcsize(header_pack_format)
        stock_item_size = calcsize(VALUE)

        data_header = dat_file.read(header_size)
        stock_header = unpack(header_pack_format, data_header)

        max_count = stock_header[2]
        report_date = stock_header[1]
        report_size = stock_header[4]

        report_fields_count = int(report_size / 4)
        report_pack_format = f"<{report_fields_count}f"

        results = []

        for stock_idx in range(0, max_count):
            dat_file.seek(header_size + stock_idx * calcsize(VALUE))
            si = dat_file.read(stock_item_size)

            stock_item = unpack("<6s1c1L", si)
            code = stock_item[0].decode("utf-8")

            foa = stock_item[2]
            dat_file.seek(foa)

            info_data = dat_file.read(calcsize(report_pack_format))
            cw_info = unpack(report_pack_format, info_data)

            one_record = (code, report_date) + cw_info
            results.append(one_record)

        if download_file.name.endswith(".zip"):
            dat_file.close()
            shutil.rmtree(tmpdir, ignore_errors=True)

        return results

    @staticmethod
    def to_df(data, header=None):
        if not data:
            return None

        col = ["code", "report_date"]
        col += [f"col{str(i).zfill(3)}" for i in range(1, len(data[0]) - 1)]

        df = pd.DataFrame(data=data, columns=col)
        df.set_index("code", inplace=True)

        if header == 'zh':
            from opentdx.crawler.columns import columns

            for i, v in enumerate(df.columns):
                if i >= len(columns):
                    columns.append(v)
            df.columns = columns

        return df
