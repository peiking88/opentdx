"""通达信 vipdoc 本地数据校验器"""
import os
import struct
from datetime import date
from pathlib import Path


def _tdx_base_path():
    """获取 TDX 安装根路径，可通过环境变量 TDX_HOME 配置"""
    env = os.environ.get("TDX_HOME", "")
    if env:
        return Path(env)
    return Path.home() / ".local" / "share" / "tdxcfv" / "drive_c" / "tc"


class VipdocValidator:
    """扫描并校验通达信 vipdoc 目录中各周期数据的完整性和时效性"""

    PERIOD_DIRS = {
        "lday": ("日线", ".day"),
        "fzline": ("5分钟线", ".lc5"),
        "minline": ("1分钟线", ".lc1"),
        "eday": ("扩展数据", ".day"),
    }

    MARKETS = ["sz", "sh", "bj", "ds"]

    RECORD_SIZES = {
        ".day": struct.calcsize("<IIIIIfII"),
        ".lc5": struct.calcsize("<HHIIIIfII"),
        ".lc1": struct.calcsize("<HHIIIIfII"),
    }

    def __init__(self, vipdoc_path=None):
        if vipdoc_path is None:
            vipdoc_path = _tdx_base_path() / "vipdoc"
        self.vipdoc_path = Path(vipdoc_path)

    @staticmethod
    def _parse_date(num):
        """解析通达信压缩日期格式
        year = num // 2048 + 2004
        month = (num % 2048) // 100
        day = (num % 2048) % 100
        """
        year = num // 2048 + 2004
        month = (num % 2048) // 100
        day = (num % 2048) % 100
        return year, month, day

    @staticmethod
    def _parse_date_zip(zip_val):
        """解析分钟线日期压缩值 (HHHHHYYYYYYY MMMMDDDDD)"""
        year = (zip_val >> 11) + 2004
        month = (zip_val >> 6) & 0x0F
        day = zip_val & 0x1F
        return year, month, day

    def validate(self, markets=None, periods=None):
        """运行全量校验，返回结构化结果"""
        markets = markets or self.MARKETS
        periods = periods or list(self.PERIOD_DIRS.keys())

        result = {}
        for market in markets:
            result[market] = {}
            for period in periods:
                result[market][period] = self._validate_period(market, period)
        return result

    def _validate_period(self, market, period):
        period_dir = self.vipdoc_path / market / period
        if not period_dir.is_dir():
            return {
                "exists": False,
                "file_count": 0,
                "latest_date": None,
                "earliest_date": None,
                "total_records": 0,
                "errors": [],
            }

        ext = self.PERIOD_DIRS[period][1]
        files = sorted(period_dir.glob(f"*{ext}"))
        record_size = self.RECORD_SIZES.get(ext, 32)

        if not files:
            return {
                "exists": True,
                "file_count": 0,
                "latest_date": None,
                "earliest_date": None,
                "total_records": 0,
                "errors": [],
            }

        latest = None
        earliest = None
        total_records = 0
        errors = []

        for fp in files:
            info = self._check_file(fp, ext, record_size)
            if info["error"]:
                errors.append({"file": str(fp), "error": info["error"]})
                continue

            total_records += info["record_count"]
            last_date = info["last_date"]
            first_date = info.get("first_date")

            if last_date:
                if latest is None or last_date > latest:
                    latest = last_date
                if earliest is None or first_date < earliest:
                    earliest = first_date

        return {
            "exists": True,
            "file_count": len(files),
            "latest_date": self._fmt_date(latest) if latest else None,
            "earliest_date": self._fmt_date(earliest) if earliest else None,
            "total_records": total_records,
            "errors": errors,
        }

    def _check_file(self, filepath, ext, record_size):
        try:
            fsize = filepath.stat().st_size
        except OSError as e:
            return {"error": str(e), "record_count": 0, "last_date": None, "first_date": None}

        if fsize == 0:
            return {"error": "空文件", "record_count": 0, "last_date": None, "first_date": None}

        if fsize % record_size != 0:
            return {
                "error": f"文件大小 {fsize} 不是记录大小 {record_size} 的整数倍",
                "record_count": 0,
                "last_date": None,
                "first_date": None,
            }

        record_count = fsize // record_size
        last_date = None
        first_date = None

        try:
            raw = filepath.read_bytes()
        except OSError as e:
            return {"error": str(e), "record_count": 0, "last_date": None, "first_date": None}

        # 最后一条记录的日期
        last_offset = (record_count - 1) * record_size
        last_date = self._extract_date(raw, last_offset, ext)

        # 第一条记录的日期
        first_date = self._extract_date(raw, 0, ext)

        return {
            "error": None,
            "record_count": record_count,
            "last_date": last_date,
            "first_date": first_date,
        }

    def _extract_date(self, data, offset, ext):
        if ext == ".day":
            date_num = struct.unpack_from("<I", data, offset)[0]
            return self._parse_date(date_num)
        elif ext in (".lc5", ".lc1"):
            date_zip = struct.unpack_from("<H", data, offset)[0]
            return self._parse_date_zip(date_zip)
        return None

    @staticmethod
    def _fmt_date(d):
        if d is None:
            return None
        return f"{d[0]:04d}-{d[1]:02d}-{d[2]:02d}"

    def count_files(self, market, period):
        """返回 {market}/{period}/ 下的数据文件数量"""
        period_dir = self.vipdoc_path / market / period
        if not period_dir.is_dir():
            return 0
        ext = self.PERIOD_DIRS.get(period, ("", ""))[1]
        return len(list(period_dir.glob(f"*{ext}")))

    def check_freshness(self, markets=None, periods=None):
        """检查各周期数据是否最新。返回每个周期的最新日期和距今天数"""
        result = self.validate(markets, periods)
        today = date.today()
        freshness = {}

        for market, periods_data in result.items():
            for period, info in periods_data.items():
                key = f"{market}/{period}"
                entry = {"file_count": info["file_count"], "latest_date": info["latest_date"]}
                if info["latest_date"]:
                    try:
                        d = date.fromisoformat(info["latest_date"])
                        entry["days_behind"] = (today - d).days
                    except (ValueError, TypeError):
                        entry["days_behind"] = None
                else:
                    entry["days_behind"] = None
                freshness[key] = entry

        return freshness

    def generate_report(self, markets=None, periods=None):
        """生成人类可读的校验报告"""
        result = self.validate(markets, periods)
        today = date.today()
        lines = []
        lines.append(f"vipdoc 数据校验报告")
        lines.append(f"路径: {self.vipdoc_path}")
        lines.append(f"校验时间: {today.isoformat()}")
        lines.append("=" * 60)

        for market in sorted(result):
            lines.append(f"\n## {market.upper()} 市场")
            for period in sorted(result[market]):
                info = result[market][period]
                period_name = self.PERIOD_DIRS.get(period, (period, ""))[0]
                if not info["exists"]:
                    lines.append(f"  {period_name}({period}): 目录不存在")
                    continue

                files_str = f"{info['file_count']} 个文件"
                records_str = f"{info['total_records']} 条记录"
                date_str = info["latest_date"] or "无数据"
                days_str = ""
                if info["latest_date"]:
                    try:
                        d = date.fromisoformat(info["latest_date"])
                        days = (today - d).days
                        days_str = f" (距今 {days} 天)"
                    except (ValueError, TypeError):
                        pass

                lines.append(f"  {period_name}({period}): {files_str}, {records_str}, 最新: {date_str}{days_str}")

                if info["errors"]:
                    lines.append(f"    !! 错误 ({len(info['errors'])} 个文件):")
                    for e in info["errors"][:5]:
                        lines.append(f"      - {Path(e['file']).name}: {e['error']}")
                    if len(info["errors"]) > 5:
                        lines.append(f"      ... 及其他 {len(info['errors']) - 5} 个文件")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
