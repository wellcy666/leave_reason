# -*- coding: utf-8 -*-
"""用假的 MCDR 服务端跑一遍插件核心流程，验证配置生成 / 归类 / 权限。"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '_leave_reason_src'))

from mcdreforged.api.all import CommandSource, Info
import leave_reason
from leave_reason import LeaveReason


class FakeLogger:
    def __init__(self):
        self.lines = []
    def info(self, msg): self.lines.append(str(msg))
    def warning(self, msg): self.lines.append('WARN ' + str(msg))


class FakeServer:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.logger = FakeLogger()
        self.said = []
        self.commands = []
        self.helps = []

    def get_data_folder(self):
        return self.data_dir

    def load_config_simple(self, file_name, default_config, in_data_folder=True):
        path = os.path.join(self.data_dir, file_name)
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
        return default_config

    def register_command(self, node):
        self.commands.append(node)

    def register_help_message(self, prefix, msg):
        self.helps.append((prefix, msg))

    def broadcast(self, msg):
        self.said.append(str(msg))


def main():
    data_dir = os.path.join(HERE, 'data')
    shutil.rmtree(data_dir, ignore_errors=True)
    os.makedirs(data_dir)

    srv = FakeServer(data_dir)
    p = LeaveReason(srv)
    p.load()

    cfg_path = os.path.join(data_dir, 'config.json')
    print('== 生成的 config.json 前 12 行 ==')
    with open(cfg_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 12:
                break
            print(line.rstrip())

    print('\n== 广播测试 ==')
    p.config['dedup_seconds'] = 0
    lines = [
        'Steve lost connection: Disconnected',
        'Steve lost connection: Kicked by an operator',
        'Alex lost connection: Timed out',
        'UUID of player Herobrine is 069a79f4-44e9-4726-a5be-fca90e38aaf5',
        'Disconnecting /1.2.3.4:5678: You are banned from this server!',
        'Disconnecting /1.2.3.4:5678: You are not white-listed on this server!',
        'Notch lost connection: Attempting to attack an invalid entity',
    ]
    for line in lines:
        p._handle_line(line)
    for s in srv.said:
        print('  公屏 ->', s)

    print('\n== 未归类关闭后 ==')
    p.config['show_unknown'] = False
    srv.said.clear()
    p._handle_line('Notch lost connection: Attempting to attack an invalid entity')
    print('  播报条数:', len(srv.said))

    print('\n== 权限测试 ==')
    for level in (3, 4):
        src = CommandSource(level=level)
        p._cmd_status(src)
        print('  等级 {} -> 首行: {}'.format(level, src.msgs[0]))

    print('\n== 旧配置迁移测试 ==')
    with open(cfg_path, 'w', encoding='utf-8') as f:
        json.dump({'enabled': True, 'message_template': 'OLD'}, f, ensure_ascii=False, indent=4)
    p._load_config()
    print('  config.json.bak 存在:', os.path.isfile(cfg_path + '.bak'))
    with open(cfg_path, 'r', encoding='utf-8') as f:
        new_cfg = json.load(f)
    print('  新配置有 config_version:', new_cfg.get('config_version'), '| 有 message:', 'message' in new_cfg)

    print('\n== 删字段容错测试 ==')
    with open(cfg_path, 'w', encoding='utf-8') as f:
        json.dump({'config_version': 2, 'keywords': {'kick': ['kick']}}, f, ensure_ascii=False, indent=4)
    p._load_config()
    print('  timeout 关键词仍存在:', len(p.config['keywords']['timeout']))
    print('  reason_text.kick:', p.config['reason_text']['kick'])


if __name__ == '__main__':
    main()
