"""TdxConnectCfgReader 测试"""
import os
import tempfile
from pathlib import Path

import pytest

from opentdx.reader.connect_cfg_reader import TdxConnectCfgReader


class TestTdxConnectCfgReader:
    def test_parse_hqhost_section(self):
        """测试解析 [HQHOST] section"""
        content = (
            "[USER]\r\n"
            "UserName=\r\n"
            "SavePass=1\r\n"
            "[HQHOST]\r\n"
            "HostNum=3\r\n"
            "PrimaryHost=1\r\n"
            "HostName01=通达信深圳双线主站1\r\n"
            "IPAddress01=110.41.147.114\r\n"
            "Port01=7709\r\n"
            "HostName02=通达信深圳双线主站2\r\n"
            "IPAddress02=110.41.2.72\r\n"
            "Port02=7709\r\n"
            "HostName03=通达信深圳双线主站3\r\n"
            "IPAddress03=110.41.4.4\r\n"
            "Port03=7709\r\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False, encoding="gbk") as f:
            f.write(content)
            tmp_path = f.name

        try:
            reader = TdxConnectCfgReader(cfg_path=tmp_path, auto_detect=False)
            assert reader.is_loaded

            hq = reader.get_hq_servers()
            assert len(hq) == 3
            assert hq[0]["hostname"] == "通达信深圳双线主站1"
            assert hq[0]["ip"] == "110.41.147.114"
            assert hq[0]["port"] == 7709
            assert hq[1]["ip"] == "110.41.2.72"
            assert hq[2]["ip"] == "110.41.4.4"
        finally:
            os.unlink(tmp_path)

    def test_parse_all_sections(self):
        """测试解析多个 section"""
        content = (
            "[HQHOST]\r\n"
            "HostNum=2\r\n"
            "HostName01=深圳主站1\r\n"
            "IPAddress01=1.1.1.1\r\n"
            "Port01=7709\r\n"
            "HostName02=深圳主站2\r\n"
            "IPAddress02=2.2.2.2\r\n"
            "Port02=7709\r\n"
            "[INFOHOST]\r\n"
            "HostNum=1\r\n"
            "HostName01=资讯主站\r\n"
            "IPAddress01=3.3.3.3\r\n"
            "Port01=7721\r\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False, encoding="gbk") as f:
            f.write(content)
            tmp_path = f.name

        try:
            reader = TdxConnectCfgReader(cfg_path=tmp_path, auto_detect=False)
            all_servers = reader.get_all_servers()
            assert "HQHOST" in all_servers
            assert "INFOHOST" in all_servers
            assert len(all_servers["HQHOST"]) == 2
            assert len(all_servers["INFOHOST"]) == 1
            assert all_servers["INFOHOST"][0]["ip"] == "3.3.3.3"
        finally:
            os.unlink(tmp_path)

    def test_file_not_found(self):
        """测试文件不存在时的行为"""
        reader = TdxConnectCfgReader(cfg_path="/nonexistent/connect.cfg", auto_detect=False)
        assert not reader.is_loaded
        assert reader.get_hq_servers() == []
        assert reader.get_all_servers() == {}

    def test_auto_detect_not_found(self):
        """测试自动检测在无文件时返回 None"""
        reader = TdxConnectCfgReader(auto_detect=False)
        assert not reader.is_loaded

    def test_empty_config(self):
        """测试空配置文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False, encoding="gbk") as f:
            f.write("")
            tmp_path = f.name

        try:
            reader = TdxConnectCfgReader(cfg_path=tmp_path, auto_detect=False)
            assert reader.is_loaded
            assert reader.get_hq_servers() == []
        finally:
            os.unlink(tmp_path)

    def test_missing_hqhost_section(self):
        """测试没有 HQHOST section 的配置"""
        content = (
            "[USER]\r\n"
            "UserName=test\r\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False, encoding="gbk") as f:
            f.write(content)
            tmp_path = f.name

        try:
            reader = TdxConnectCfgReader(cfg_path=tmp_path, auto_detect=False)
            assert reader.is_loaded
            assert reader.get_hq_servers() == []
        finally:
            os.unlink(tmp_path)

    def test_gbk_encoding(self):
        """测试 GBK 编码中文正确解析"""
        content = (
            "[HQHOST]\r\n"
            "HostNum=1\r\n"
            "HostName01=通达信深圳双线主站1\r\n"
            "IPAddress01=10.0.0.1\r\n"
            "Port01=7709\r\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False, encoding="gbk") as f:
            f.write(content)
            tmp_path = f.name

        try:
            reader = TdxConnectCfgReader(cfg_path=tmp_path, auto_detect=False)
            hq = reader.get_hq_servers()
            assert len(hq) == 1
            assert "通达信" in hq[0]["hostname"]
        finally:
            os.unlink(tmp_path)

    def test_invalid_port_defaults_to_zero(self):
        """测试端口号无效时默认为 0"""
        content = (
            "[HQHOST]\r\n"
            "HostNum=1\r\n"
            "HostName01=测试\r\n"
            "IPAddress01=10.0.0.1\r\n"
            "Port01=abc\r\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False, encoding="gbk") as f:
            f.write(content)
            tmp_path = f.name

        try:
            reader = TdxConnectCfgReader(cfg_path=tmp_path, auto_detect=False)
            hq = reader.get_hq_servers()
            assert len(hq) == 1
            assert hq[0]["port"] == 0
        finally:
            os.unlink(tmp_path)

    def test_get_all_servers_memoization(self):
        """测试 get_all_servers 返回一致结果"""
        content = (
            "[HQHOST]\r\n"
            "HostNum=1\r\n"
            "HostName01=主站\r\n"
            "IPAddress01=1.1.1.1\r\n"
            "Port01=7709\r\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False, encoding="gbk") as f:
            f.write(content)
            tmp_path = f.name

        try:
            reader = TdxConnectCfgReader(cfg_path=tmp_path, auto_detect=False)
            r1 = reader.get_all_servers()
            r2 = reader.get_all_servers()
            assert r1 == r2
        finally:
            os.unlink(tmp_path)


class TestTdxConnectCfgReaderReal:
    """真实环境测试 — 如果存在 connect.cfg 则验证"""

    def test_real_file_if_exists(self):
        path = TdxConnectCfgReader._auto_detect_path()
        if path is None:
            pytest.skip("未找到本地 connect.cfg 文件")

        reader = TdxConnectCfgReader(cfg_path=path, auto_detect=False)
        assert reader.is_loaded

        hq = reader.get_hq_servers()
        assert len(hq) > 0
        for srv in hq:
            assert "ip" in srv
            assert "port" in srv
            assert srv["port"] > 0
