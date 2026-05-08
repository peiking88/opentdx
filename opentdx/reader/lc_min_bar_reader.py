from collections import OrderedDict
from pathlib import Path

import pandas as pd

from opentdx.reader.base_reader import BaseReader, TdxFileNotFoundException


class TdxLCMinBarReader(BaseReader):
    def parse_data_by_file(self, filename):
        if not Path(filename).is_file():
            raise TdxFileNotFoundException(f"no tdx kline data, please check path {filename}")

        content = Path(filename).read_bytes()
        raw_li = self.unpack_records("<HHfffffII", content)

        data = []

        for row in raw_li:
            year, month, day = self._parse_date(row[0])
            hour, minute = self._parse_time(row[1])

            data.append(
                OrderedDict([
                    ("date", f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"),
                    ("year", year),
                    ("month", month),
                    ("day", day),
                    ("hour", hour),
                    ("minute", minute),
                    ("open", row[2]),
                    ("high", row[3]),
                    ("low", row[4]),
                    ("close", row[5]),
                    ("amount", row[6]),
                    ("volume", row[7]),
                ])
            )

        return data

    def get_df(self, code_or_file, **kwargs):
        df = pd.DataFrame(data=self.parse_data_by_file(code_or_file))
        df.index = pd.to_datetime(df.date)
        df = df[["open", "high", "low", "close", "amount", "volume"]]
        return df
