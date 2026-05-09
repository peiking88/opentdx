"""VipdocValidator 测试"""
import os
import struct
import tempfile
from pathlib import Path

import pytest

from opentdx.utils.vipdoc_validator import VipdocValidator


class TestVipdocValidatorDateParsing:
    def test_parse_date_base(self):
        """测试日期解析基准：2004-00-00"""
        y, m, d = VipdocValidator._parse_date(0)
        assert y == 2004
        assert m == 0
        assert d == 0

    def test_parse_date_2026_05_08(self):
        """测试 2026-05-08 日期解析"""
        # (2026-2004)=22, 22*2048 + 5*100 + 8 = 45564
        y, m, d = VipdocValidator._parse_date(45564)
        assert y == 2026
        assert m == 5
        assert d == 8

    def test_parse_date_zip(self):
        """测试分钟线日期压缩值解析"""
        # 2026-05-06: (22 << 11) | (5 << 6) | 6
        zip_val = (22 << 11) | (5 << 6) | 6
        y, m, d = VipdocValidator._parse_date_zip(zip_val)
        assert y == 2026
        assert m == 5
        assert d == 6

    def test_fmt_date(self):
        """测试日期格式化"""
        assert VipdocValidator._fmt_date((2026, 5, 8)) == "2026-05-08"
        assert VipdocValidator._fmt_date(None) is None


class TestVipdocValidator:
    def test_empty_directory(self):
        """测试空 vipdoc 目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = VipdocValidator(vipdoc_path=tmpdir)
            result = validator.validate(markets=["sz"], periods=["lday"])
            assert result["sz"]["lday"]["exists"] is False
            assert result["sz"]["lday"]["file_count"] == 0

    def test_count_files(self):
        """测试文件计数"""
        with tempfile.TemporaryDirectory() as tmpdir:
            lday_dir = Path(tmpdir, "sz", "lday")
            lday_dir.mkdir(parents=True)
            # 创建测试文件
            for i in range(5):
                (lday_dir / f"sz00000{i}.day").touch()

            validator = VipdocValidator(vipdoc_path=tmpdir)
            count = validator.count_files("sz", "lday")
            assert count == 5

    def test_validate_with_synthetic_day_files(self):
        """测试用合成 .day 文件的校验"""
        with tempfile.TemporaryDirectory() as tmpdir:
            lday_dir = Path(tmpdir, "sz", "lday")
            lday_dir.mkdir(parents=True)

            # 创建合成 .day 文件，3 条记录，最后一条日期为 20260508
            records = []
            for i, d in enumerate([45562, 45563, 45564]):
                row = struct.pack(
                    "<IIIIIfII",
                    d,  # date
                    1137, 1142, 1130, 1130,  # ohlc
                    575654656.0,  # amount
                    614950,  # volume
                    0,
                )
                records.append(row)

            filepath = lday_dir / "sz000001.day"
            filepath.write_bytes(b"".join(records))

            validator = VipdocValidator(vipdoc_path=tmpdir)
            result = validator.validate(markets=["sz"], periods=["lday"])

            info = result["sz"]["lday"]
            assert info["exists"] is True
            assert info["file_count"] == 1
            assert info["total_records"] == 3
            assert info["latest_date"] == "2026-05-08"
            assert info["latest_date"] is not None

    def test_validate_with_synthetic_lc5_files(self):
        """测试用合成 .lc5 文件的校验"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fzline_dir = Path(tmpdir, "sh", "fzline")
            fzline_dir.mkdir(parents=True)

            # 分钟线日期格式: zip_day + minutes
            # zip_day: (year-2004)<<11 | month<<6 | day
            # 第一条: 20260504,  最后一条: 20260506
            zip_d1 = (22 << 11) | (5 << 6) | 4
            zip_d2 = (22 << 11) | (5 << 6) | 5
            zip_d3 = (22 << 11) | (5 << 6) | 6

            records = []
            for zip_day in [zip_d1, zip_d2, zip_d3]:
                row = struct.pack(
                    "<HHIIIIfII",
                    zip_day, 570,  # date, minutes=9:30
                    1137, 1142, 1130, 1130,
                    500000,
                    10000,
                    0,
                )
                records.append(row)

            filepath = fzline_dir / "sh600000.lc5"
            filepath.write_bytes(b"".join(records))

            validator = VipdocValidator(vipdoc_path=tmpdir)
            result = validator.validate(markets=["sh"], periods=["fzline"])

            info = result["sh"]["fzline"]
            assert info["exists"] is True
            assert info["file_count"] == 1
            assert info["total_records"] == 3
            assert info["latest_date"] == "2026-05-06"

    def test_generate_report(self):
        """测试生成文本报告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            lday_dir = Path(tmpdir, "sz", "lday")
            lday_dir.mkdir(parents=True)

            row = struct.pack("<IIIIIfII", 45564, 1137, 1142, 1130, 1130, 575654656.0, 614950, 0)
            (lday_dir / "sz000001.day").write_bytes(row)

            validator = VipdocValidator(vipdoc_path=tmpdir)
            report = validator.generate_report(markets=["sz"], periods=["lday"])
            assert "vipdoc 数据校验报告" in report
            assert "SZ 市场" in report
            assert "日线" in report
            assert "2026-05-08" in report

    def test_check_freshness(self):
        """测试时效性检查"""
        with tempfile.TemporaryDirectory() as tmpdir:
            lday_dir = Path(tmpdir, "sz", "lday")
            lday_dir.mkdir(parents=True)

            row = struct.pack("<IIIIIfII", 45564, 1137, 1142, 1130, 1130, 575654656.0, 614950, 0)
            (lday_dir / "sz000001.day").write_bytes(row)

            validator = VipdocValidator(vipdoc_path=tmpdir)
            freshness = validator.check_freshness(markets=["sz"], periods=["lday"])
            assert "sz/lday" in freshness
            assert freshness["sz/lday"]["file_count"] == 1
            assert freshness["sz/lday"]["latest_date"] == "2026-05-08"
            assert isinstance(freshness["sz/lday"]["days_behind"], int)

    def test_empty_file_handled(self):
        """测试空文件处理"""
        with tempfile.TemporaryDirectory() as tmpdir:
            lday_dir = Path(tmpdir, "sz", "lday")
            lday_dir.mkdir(parents=True)
            (lday_dir / "sz000001.day").write_bytes(b"")
            (lday_dir / "sz000002.day").write_bytes(
                struct.pack("<IIIIIfII", 45564, 1137, 1142, 1130, 1130, 575654656.0, 614950, 0)
            )

            validator = VipdocValidator(vipdoc_path=tmpdir)
            result = validator.validate(markets=["sz"], periods=["lday"])
            info = result["sz"]["lday"]
            assert info["latest_date"] == "2026-05-08"
            # 空文件被记录为错误
            assert len(info["errors"]) == 1

    def test_corrupted_file_handled(self):
        """测试损坏文件（大小不是记录整数倍）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            lday_dir = Path(tmpdir, "sz", "lday")
            lday_dir.mkdir(parents=True)
            # 写入非 32 字节整数倍的数据
            (lday_dir / "szbad.day").write_bytes(b"\x00" * 15)

            validator = VipdocValidator(vipdoc_path=tmpdir)
            result = validator.validate(markets=["sz"], periods=["lday"])
            info = result["sz"]["lday"]
            assert len(info["errors"]) == 1
            assert "整数倍" in info["errors"][0]["error"]

    def test_multiple_markets_and_periods(self):
        """测试多市场多周期"""
        with tempfile.TemporaryDirectory() as tmpdir:
            row = struct.pack("<IIIIIfII", 45564, 1137, 1142, 1130, 1130, 575654656.0, 614950, 0)

            for market in ["sz", "sh"]:
                for period in ["lday"]:
                    d = Path(tmpdir, market, period)
                    d.mkdir(parents=True)
                    (d / f"{market}000001.day").write_bytes(row)

            validator = VipdocValidator(vipdoc_path=tmpdir)
            result = validator.validate()

            assert "sz" in result
            assert "sh" in result
            assert result["sz"]["lday"]["file_count"] == 1
            assert result["sh"]["lday"]["file_count"] == 1
            # 不存在的周期
            assert result["sz"]["eday"]["exists"] is False


class TestVipdocValidatorReal:
    """真实环境测试 — 如果存在 vipdoc 则验证"""

    def test_real_vipdoc_if_exists(self):
        vp = Path.home() / ".local" / "share" / "tdxcfv" / "drive_c" / "tc" / "vipdoc"
        if not vp.is_dir():
            pytest.skip("未找到本地 vipdoc 目录")

        validator = VipdocValidator(vipdoc_path=vp)
        result = validator.validate(markets=["sz"], periods=["lday"])

        info = result["sz"]["lday"]
        assert info["exists"] is True
        assert info["file_count"] > 0
        # 日线数据应该包含最新日期
        if info["latest_date"]:
            assert info["total_records"] > 0

    def test_real_report_if_exists(self):
        vp = Path.home() / ".local" / "share" / "tdxcfv" / "drive_c" / "tc" / "vipdoc"
        if not vp.is_dir():
            pytest.skip("未找到本地 vipdoc 目录")

        validator = VipdocValidator(vipdoc_path=vp)
        report = validator.generate_report(markets=["sz", "sh"], periods=["lday", "fzline", "minline"])
        assert "SZ 市场" in report
        assert "SH 市场" in report
