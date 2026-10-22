# -*- coding: utf-8 -*-
"""LeaveReason：检测玩家异常退出原因并在公屏广播。"""

import json
import os
import re
import time

from mcdreforged.api.all import *

# RText 相关类在不同 MCDR 版本中的位置不同，做兼容导入
try:
    from mcdreforged.api.rtext import RText, RTextList, RColor, RStyle
except ImportError:
    from mcdreforged.minecraft.rtext import RText, RTextList, RColor, RStyle

from .config import DEFAULT_CONFIG, CONFIG_VERSION

PLUGIN_ID = 'leave_reason'
PLUGIN_VERSION = '1.3.0'
PREFIX = '!!lr'

# 使用 !!lr 所需的最低 MCDR 权限等级：4 = 拥有者（控制台默认也是 4）
PERMISSION_LEVEL = 4

# 用于从封禁/白名单拦截行补全玩家名时，认为“最近连接玩家”有效的时间窗口（秒）
CONNECT_WINDOW = 30.0

# 日志匹配正则（一般不用改，服务端日志格式不同时才需要动这里）
# lost connection: 游戏内断开（被踢 / 超时 / 其他异常）
RE_LOST_CONNECTION = re.compile(r'^(?P<player>[A-Za-z0-9_]{1,16}) lost connection: (?P<reason>.*)$')
# Disconnecting: 登录阶段被拦截（封禁 / 白名单）
RE_DISCONNECTING = re.compile(r'^Disconnecting (?P<who>.+?): (?P<reason>.*)$')
# UUID of player: 在线模式认证行，用于给上一种情况补全玩家名（离线模式不会出现）
RE_UUID_OF_PLAYER = re.compile(r'UUID of player (?P<player>[A-Za-z0-9_]{1,16}) is')

# 去除 § 颜色代码（控制台回显用）：0-9 a-f k l m n o r 及对应大写
_STRIP_COLOR = re.compile(r'§[0-9a-fklmnorA-FKLMNOR]')

# 不需要附在文案后的通用/冗余原始原因
_GENERIC_RAW_REASONS = {'disconnected', 'disconnect', 'kicked by an operator'}


def _strip_color(text):
    return _STRIP_COLOR.sub('', text)


# § 颜色代码解析：MCDR 2.13+ 移除了 RText.from_legacy_text，这里自己实现
_LEGACY_SPLIT = re.compile(r'(§[0-9a-fklmnorA-FKLMNOR])')
_LEGACY_COLOR = {
    '0': 'black', '1': 'dark_blue', '2': 'dark_green', '3': 'dark_aqua',
    '4': 'dark_red', '5': 'dark_purple', '6': 'gold', '7': 'gray',
    '8': 'dark_gray', '9': 'blue', 'a': 'green', 'b': 'aqua',
    'c': 'red', 'd': 'light_purple', 'e': 'yellow', 'f': 'white',
}
_LEGACY_STYLE = {
    'l': 'bold', 'o': 'italic', 'n': 'underlined',
    'm': 'strikethrough', 'k': 'obfuscated',
}


def legacy_to_rtext(text: str):
    """把带 § 颜色代码的字符串转成 RTextBase，用于公屏广播时正确显示颜色。"""
    color = None
    styles = set()
    result = RTextList()
    for part in _LEGACY_SPLIT.split(text):
        if not part:
            continue
        if part.startswith('§') and len(part) == 2:
            code = part[1].lower()
            if code in _LEGACY_COLOR:
                color = RColor.from_mc_value(_LEGACY_COLOR[code])
            elif code in _LEGACY_STYLE:
                styles.add(getattr(RStyle, _LEGACY_STYLE[code]))
            elif code == 'r':
                color = None
                styles.clear()
        else:
            result.append(RText(part, color=color, styles=list(styles)))
    return result


def _deep_merge(default: dict, override: dict) -> dict:
    """递归合并配置，保证配置文件里删掉的项（如 keywords 某一类）也能用默认值补上。"""
    result = dict(default)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class LeaveReason:
    def __init__(self, server: PluginServerInterface):
        self.server = server
        self.config = dict(DEFAULT_CONFIG)
        self._enabled = True
        self._last_connecting_player = None
        self._last_connecting_time = 0.0
        self._recent = {}  # (player, category) -> timestamp

    # ------------------------------------------------------------------ 生命周期
    def load(self):
        self._load_config()
        self._register_commands()
        self.server.register_help_message(
            PREFIX,
            '检测玩家异常退出原因并公屏广播（需要权限等级 {}）'.format(PERMISSION_LEVEL)
        )
        self.server.logger.info('{} v{} 已加载'.format(PLUGIN_ID, PLUGIN_VERSION))

    def unload(self):
        self.server.logger.info('{} 已卸载'.format(PLUGIN_ID))

    # ------------------------------------------------------------------ 配置
    def _config_path(self) -> str:
        try:
            return os.path.join(self.server.get_data_folder(), 'config.json')
        except Exception:
            return 'config.json'

    def _backup_outdated_config(self):
        """
        旧版配置（没有 config_version 或版本号不同）先备份成 config.json.bak，
        再让 MCDR 重新生成一份新格式的 config.json，避免旧字段名误导。
        """
        path = self._config_path()
        if not os.path.isfile(path):
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                old = json.load(f)
            if isinstance(old, dict) and old.get('config_version') == CONFIG_VERSION:
                return
        except Exception:
            pass
        try:
            os.replace(path, path + '.bak')
            self.server.logger.info(
                '[{}] 旧配置已备份为 config.json.bak，并重新生成新格式配置'.format(PLUGIN_ID)
            )
        except OSError as e:
            self.server.logger.warning('[{}] 旧配置备份失败：{}'.format(PLUGIN_ID, e))

    def _load_config(self):
        self._backup_outdated_config()
        loaded = self.server.load_config_simple(
            file_name='config.json',
            default_config=DEFAULT_CONFIG,
            in_data_folder=True,
        )
        # 深合并默认值：用户删掉的键自动补全，改过的值保持不变
        self.config = _deep_merge(DEFAULT_CONFIG, loaded)
        # reload 会把广播开关重置为配置文件里的 enabled 值
        self._enabled = bool(self.config.get('enabled', True))

    # ------------------------------------------------------------------ 事件
    def on_info(self, info: Info):
        if not self._enabled:
            return
        content = info.content
        if not content:
            content = info.raw_content
        if content:
            self._handle_line(content)

    def _handle_line(self, line: str):
        line = line.strip()
        if not line:
            return

        # 1) 在线模式认证行：记住“最近正在连接的玩家名”，供封禁/白名单拦截时补全
        m = RE_UUID_OF_PLAYER.search(line)
        if m:
            self._last_connecting_player = m.group('player')
            self._last_connecting_time = time.time()
            return

        # 2) 游戏内断开：被踢 / 超时 / 其他异常
        m = RE_LOST_CONNECTION.search(line)
        if m:
            self._emit(m.group('player'), m.group('reason'), source='lost_connection')
            return

        # 3) 登录阶段拦截：封禁 / 白名单
        m = RE_DISCONNECTING.search(line)
        if m:
            who = m.group('who').strip()
            if self._is_player_name(who):
                player = who
            elif (
                self._last_connecting_player
                and (time.time() - self._last_connecting_time) < CONNECT_WINDOW
            ):
                player = self._last_connecting_player
            else:
                player = None
            self._emit(player, m.group('reason'), source='disconnecting')

    # ------------------------------------------------------------------ 归类与输出
    @staticmethod
    def _is_player_name(s: str) -> bool:
        return bool(re.fullmatch(r'[A-Za-z0-9_]{1,16}', s))

    def _classify(self, reason: str):
        """按关键词归类，返回 None(忽略) / kick / timeout / ban / whitelist / unknown。"""
        r = reason.strip().lower()
        kws = self.config.get('keywords', {})

        for kw in kws.get('ignore', []):
            if str(kw).lower() in r:
                return None
        for category in ('timeout', 'whitelist', 'ban', 'kick'):
            for kw in kws.get(category, []):
                if str(kw).lower() in r:
                    return category
        # 其余一律当作“未归类原因”，原样显示控制台给的原因
        return 'unknown'

    def _reason_text(self, category: str, raw_reason: str) -> str:
        if category == 'unknown':
            return raw_reason
        text = self.config.get('reason_text', {}).get(category, category)
        if category == 'kick' and self.config.get('append_kick_detail', True):
            raw = raw_reason.strip()
            if raw and raw.lower() not in _GENERIC_RAW_REASONS:
                text = '{}（{}）'.format(text, raw)
        return text

    def _emit(self, player, raw_reason: str, source: str):
        raw_reason = raw_reason.strip()
        category = self._classify(raw_reason)

        if category is None:
            self._debug('忽略: {}'.format(raw_reason))
            return
        if category == 'unknown' and not self.config.get('show_unknown', True):
            self._debug('未归类且已关闭播报: {}'.format(raw_reason))
            return

        self._debug('{} -> {} | 来源={} | 玩家={}'.format(
            raw_reason, category, source, player or '未知'
        ))

        # 去重：同一玩家同一原因（未归类时带上原因文本）短时间内只播一次
        now = time.time()
        dedup = float(self.config.get('dedup_seconds', 0))
        if dedup > 0:
            key = (player, category, raw_reason if category == 'unknown' else '')
            last = self._recent.get(key)
            if last is not None and (now - last) < dedup:
                return
            self._recent[key] = now
            self._prune_recent(now)

        reason_text = self._reason_text(category, raw_reason)
        if player:
            template = self.config.get('message', '{player} 退出游戏，原因：{reason}')
            msg = template.replace('{player}', player).replace('{reason}', reason_text)
        else:
            template = self.config.get('message_no_name', '有玩家被拒绝加入，原因：{reason}')
            msg = template.replace('{reason}', reason_text)

        # 公屏广播
        self.server.broadcast(legacy_to_rtext(msg))

        # 控制台回显
        if self.config.get('echo_console', True):
            self.server.logger.info('[{}] {}'.format(PLUGIN_ID, _strip_color(msg)))

    def _debug(self, text: str):
        if self.config.get('debug', False):
            self.server.logger.info('[{}][debug] {}'.format(PLUGIN_ID, text))

    def _prune_recent(self, now: float):
        # 简单清理过期条目，避免无限增长
        if len(self._recent) > 200:
            dedup = float(self.config.get('dedup_seconds', 0))
            self._recent = {
                k: v for k, v in self._recent.items()
                if (now - v) < max(dedup, 1.0)
            }

    # ------------------------------------------------------------------ 命令
    def _register_commands(self):
        self.server.register_command(
            Literal(PREFIX).runs(self._cmd_help)
            .then(Literal('on').runs(self._cmd_on))
            .then(Literal('off').runs(self._cmd_off))
            .then(Literal('reload').runs(self._cmd_reload))
            .then(Literal('status').runs(self._cmd_status))
        )

    def _reply(self, source: CommandSource, text: str):
        source.reply(legacy_to_rtext(text))

    def _check_permission(self, source: CommandSource) -> bool:
        """所有 !!lr 命令统一要求 MCDR 权限等级 4。"""
        if source.has_permission(PERMISSION_LEVEL):
            return True
        self._reply(source, '§c权限不足：{} 需要 MCDR 权限等级 {}（拥有者/控制台）'.format(
            PREFIX, PERMISSION_LEVEL
        ))
        return False

    def _cmd_help(self, source: CommandSource):
        if not self._check_permission(source):
            return
        self._reply(source, '§e===== LeaveReason 退出原因 =====')
        self._reply(source, '§7{} on/off §f- 开启/关闭广播'.format(PREFIX))
        self._reply(source, '§7{} reload §f- 重载配置文件'.format(PREFIX))
        self._reply(source, '§7{} status §f- 查看当前状态'.format(PREFIX))

    def _cmd_on(self, source: CommandSource):
        if not self._check_permission(source):
            return
        self._enabled = True
        self._reply(source, '§a已开启异常退出广播')

    def _cmd_off(self, source: CommandSource):
        if not self._check_permission(source):
            return
        self._enabled = False
        self._reply(source, '§c已关闭异常退出广播')

    def _cmd_reload(self, source: CommandSource):
        if not self._check_permission(source):
            return
        self._load_config()
        self._reply(source, '§a配置已重新加载')

    def _cmd_status(self, source: CommandSource):
        if not self._check_permission(source):
            return
        texts = self.config.get('reason_text', {})
        self._reply(source, '§e===== LeaveReason 状态 =====')
        self._reply(source, '§7广播：§f{}'.format('开' if self._enabled else '关'))
        self._reply(source, '§7调试：§f{}'.format('开' if self.config.get('debug', False) else '关'))
        self._reply(source, '§7被踢：§f{}'.format(texts.get('kick', '-')))
        self._reply(source, '§7超时：§f{}'.format(texts.get('timeout', '-')))
        self._reply(source, '§7封禁：§f{}'.format(texts.get('ban', '-')))
        self._reply(source, '§7白名单：§f{}'.format(texts.get('whitelist', '-')))
        self._reply(source, '§7配置文件：§f{}'.format(self._config_path()))


_plugin = None


def on_load(server: PluginServerInterface, old):
    global _plugin
    _plugin = LeaveReason(server)
    _plugin.load()


def on_unload(server: PluginServerInterface):
    global _plugin
    if _plugin:
        _plugin.unload()
        _plugin = None


def on_info(server: PluginServerInterface, info: Info):
    if _plugin:
        _plugin.on_info(info)
