# -*- coding: utf-8 -*-
"""默认配置，首次加载时生成到 config/leave_reason/config.json。"""

# 配置版本号：插件升级时用来判断旧配置要不要备份，请勿修改
CONFIG_VERSION = 2

DEFAULT_CONFIG = {
    'config_version': CONFIG_VERSION,

    '_颜色': '§ 是颜色代码：§c 红  §e 黄  §f 白  §7 灰  §a 绿  §6 金  §r 重置',
    '_用法': '改完配置执行 !!lr reload 生效；不想要的项整行删掉，插件会自动用默认值补上',

    '_总开关': 'true = 广播退出原因，false = 不广播（游戏里也可用 !!lr on / !!lr off 临时切换）',
    'enabled': True,

    '_消息格式': '能拿到玩家名时用 message，拿不到玩家名时用 message_no_name（封禁/白名单在登录阶段就被拦下，日志里常常没有名字）',
    '_占位符': '{player} = 玩家名，{reason} = 原因',
    'message': '§7[§c!§7] §e{player} §7退出游戏，原因：§f{reason}',
    'message_no_name': '§7[§c!§7] §e有玩家 §7被拒绝加入，原因：§f{reason}',

    '_原因文案': '四类原因的显示文字，想换说法改这里就行',
    'reason_text': {
        'kick': '被踢出服务器',
        'timeout': '连接超时',
        'ban': '被封禁',
        'whitelist': '不在白名单内',
    },

    '_附原始理由': '被踢时是否在文案后加上服务端给的原始理由，例：被踢出服务器（你已被管理员移除）',
    'append_kick_detail': True,

    '_未归类原因': 'true = 没匹配到下面关键词的断开原因也照原样播报，false = 只播报上面四类',
    'show_unknown': True,

    '_控制台回显': 'true = 服务端控制台也打印一条（无颜色）',
    'echo_console': True,

    '_去重': '同一玩家同一原因多少秒内只播报一次，0 = 不去重',
    'dedup_seconds': 5,

    '_调试': 'true = 控制台打印每条断开日志及归类结果，用来排查"为什么没播报"',
    'debug': False,

    '_关键词': '不区分大小写，日志里出现就算该类原因；ignore 里的词命中后直接跳过、不播报',
    'keywords': {
        'kick': ['kick', '被踢', '踢出', '被移出'],
        'timeout': ['timed out', 'timeout', '超时', '掉线'],
        'ban': ['banned', '封禁', '被禁'],
        'whitelist': ['white-list', 'whitelist', '白名单'],
        'ignore': ['disconnected', 'disconnect'],
    },
}
