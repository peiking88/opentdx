"""通达信 connect.cfg 通信配置读取器"""
import configparser
import os
from pathlib import Path

from opentdx.utils.help import _tdx_base_path


class TdxConnectCfgReader:
    """读取并解析通达信 connect.cfg 文件，获取服务器通信配置"""

    # connect.cfg 中每个 section 对应的配置键模式
    SECTION_KEYS = {
        "HQHOST": {"count": "HostNum", "name": "HostName", "ip": "IPAddress", "port": "Port"},
        "HFHost": {"count": "HostNum", "name": "HostName", "ip": "IPAddress", "port": "Port"},
        "WTHOST": {"count": "HostNum", "name": "HostName", "ip": "IPAddress", "port": "Port"},
        "INFOHOST": {"count": "HostNum", "name": "HostName", "ip": "IPAddress", "port": "Port"},
        "INFOHOST2": {"count": "HostNum", "name": "HostName", "ip": "IPAddress", "port": "Port"},
        "USERHOST": {"count": "HostNum", "name": "HostName", "ip": "IPAddress", "port": "Port"},
        "DSHOST": {"count": "HostNum", "name": "HostName", "ip": "IPAddress", "port": "Port"},
    }

    def __init__(self, cfg_path=None, auto_detect=True):
        self.cfg_path = cfg_path
        self._raw_config = None

        if auto_detect and cfg_path is None:
            self.cfg_path = self._auto_detect_path()

        if self.cfg_path and Path(self.cfg_path).is_file():
            self._raw_config = self._read_config(self.cfg_path)

    @classmethod
    def _auto_detect_path(cls):
        base = _tdx_base_path()
        # 优先 tc/connect.cfg，其次 tc/T0002/connect.cfg 等
        candidates = [base / "connect.cfg"]
        for d in sorted(base.glob("T*")):
            candidate = d / "connect.cfg"
            if candidate not in candidates:
                candidates.append(candidate)
        for p in candidates:
            if p.is_file():
                return str(p)
        return None

    @staticmethod
    def _read_config(filepath):
        raw = Path(filepath).read_bytes()
        try:
            text = raw.decode("gbk")
        except UnicodeDecodeError:
            text = raw.decode("gb2312", errors="replace")

        parser = configparser.ConfigParser(strict=False)
        parser.read_string(text)
        return parser

    def parse(self):
        """解析所有可识别的 section，返回 {section: [entries]}"""
        if self._raw_config is None:
            return {}

        result = {}
        for section, keys in self.SECTION_KEYS.items():
            entries = self._parse_section(section, keys)
            if entries:
                result[section] = entries
        return result

    def _parse_section(self, section, keys):
        parser = self._raw_config
        if section not in parser:
            return []

        count_key = keys["count"]
        try:
            count = int(parser[section].get(count_key, 0))
        except (ValueError, KeyError):
            return []

        name_key = keys["name"]
        ip_key = keys["ip"]
        port_key = keys["port"]

        entries = []
        for i in range(1, count + 1):
            suffix = f"{i:02d}"
            name = parser[section].get(f"{name_key}{suffix}", "")
            ip = parser[section].get(f"{ip_key}{suffix}", "")
            port_str = parser[section].get(f"{port_key}{suffix}", "0")
            try:
                port = int(port_str)
            except (ValueError, KeyError):
                port = 0

            entries.append({"hostname": name, "ip": ip, "port": port})

        return entries

    def get_hq_servers(self):
        """返回 [HQHOST] 行情主站列表"""
        parsed = self.parse()
        return parsed.get("HQHOST", [])

    def get_all_servers(self):
        """返回所有已解析的 section"""
        return self.parse()

    @property
    def is_loaded(self):
        return self._raw_config is not None
