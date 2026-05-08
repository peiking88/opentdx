from opentdx.crawler.history_financial_crawler import HistoryFinancialCrawler
from opentdx.reader.base_reader import BaseReader


class HistoryFinancialReader(BaseReader):
    def get_df(self, data_file, **kwargs):
        crawler = HistoryFinancialCrawler()

        with open(data_file, "rb") as df:
            data = crawler.parse(download_file=df)

        return crawler.to_df(data)
