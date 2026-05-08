from collections import OrderedDict
from pathlib import Path

import pandas as pd

from opentdx.reader.base_reader import BaseReader, TdxFileNotFoundException


class TdxMinBarReader(BaseReader):
    def parse_data_by_file(self, filename):
        if not Path(filename).is_file():
            raise TdxFileNotFoundException("no tdx kline data, please check path %s" % filename)

        results = []
        content = Path(filename).read_bytes()
        content = self.unpack_records("<HHIIIIfII", content)

        for row in content:
            year, month, day = self._parse_date(row[0])
            hour, minute = self._parse_time(row[1])

            results.append(
                OrderedDict([
                    ("date", f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"),
                    ("year", year),
                    ("month", month),
                    ("day", day),
                    ("hour", hour),
                    ("minute", minute),
                    ("open", row[2] / 100),
                    ("high", row[3] / 100),
                    ("low", row[4] / 100),
                    ("close", row[5] / 100),
                    ("amount", row[6]),
                    ("volume", row[7]),
                ])
            )

        return results

    def get_df(self, code_or_file, **kwargs):
        df = pd.DataFrame(data=self.parse_data_by_file(code_or_file))
        df.index = pd.to_datetime(df.date)
        df = df[["open", "high", "low", "close", "amount", "volume"]]
        return df
