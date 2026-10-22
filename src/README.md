# LeaveReason（退出原因）—— 玩家异常退出原因检测

> 🌟 **AZ 生电服同款插件**，欢迎加入 AZ 生电服 QQ 审核群：`1101978932`

一个 [MCDReforged](https://github.com/Fallen-Breath/MCDReforged) 插件，通过解析服务端控制台日志，
检测玩家的异常退出原因，并在**公屏（聊天栏）**广播原因。

配合 Velocity 的 chathub 插件使用：chathub 负责转发「谁退出了」，本插件只负责补上「为什么退出」。

## 能检测的原因

| 原因 | 说明 | 公屏输出示例 |
| --- | --- | --- |
| 被踢 | 被管理员/插件踢出 | `xxx 退出游戏，原因：被踢出服务器（你已被移除）` |
| 连接超时 | 客户端超时断线 | `xxx 退出游戏，原因：连接超时` |
| 被封禁 | 登录时被封禁（在 banlist） | `xxx 退出游戏，原因：被封禁` |
| 不在白名单 | 登录时被白名单拦截 | `xxx 退出游戏，原因：不在白名单内` |
| 未归类 | 其他没匹配到关键词的原因 | `xxx 退出游戏，原因：Attempting to attack an invalid entity` |

文案均可自行修改（见下），上述为默认效果。

## 工作原理

- **被踢 / 超时**：发生在游戏内，控制台日志为 `<玩家> lost connection: <原因>`，直接能拿到玩家名。
- **封禁**：由原版 `banlist.json` 在登录阶段拦截，日志为 `Disconnecting <地址>: You are banned ...`。
- **白名单**：由 MeowtiWhitelist 把正确 UUID 写入 `whitelist.json`，原版白名单机制在登录阶段拦截，
  日志为 `Disconnecting <地址>: You are not white-listed ...`。

> ⚠️ 你的环境是 **Velocity 正版验证 + 后端子服离线模式（转发）**，后端日志里**不会出现**
> `UUID of player` 那行，所以「封禁 / 白名单」被拦截时通常**拿不到玩家名**，
> 此时会用 `message_no_name` 模板播报（默认「有玩家被拒绝加入，原因：…」）。
> 这是 Minecraft 后端日志本身不记录名字导致的，不是插件 bug。

## 安装

把 `leave_reason.mcdr` 放进 MCDR 的 `plugins/` 目录，然后：

```
!!MCDR plugin load leave_reason.mcdr
```

（或重启 MCDR。）

## 命令

| 命令 | 说明 | 权限 |
| --- | --- | --- |
| `!!lr` | 显示帮助 | **4** |
| `!!lr on` | 开启广播 | **4** |
| `!!lr off` | 关闭广播 | **4** |
| `!!lr reload` | 重载配置 | **4** |
| `!!lr status` | 查看当前状态 | **4** |

> 权限等级 4 = MCDR 拥有者（Owner）/ 控制台。等级 3 及以下会提示「权限不足」。
> 命令前缀 `!!lr` 在插件代码里的 `PREFIX` 常量定义，想换改这一处即可。

## 配置

首次加载后自动生成 `config/leave_reason/config.json`，**文件里自带中文说明字段**（以 `_` 开头的项插件会忽略），
改完用 `!!lr reload` 生效。

实际需要动的只有这几项：

| 字段 | 作用 |
| --- | --- |
| `enabled` | 总开关 |
| `message` / `message_no_name` | 公屏消息格式，`{player}`=玩家名，`{reason}`=原因 |
| `reason_text` | 四类原因的显示文字（`kick` / `timeout` / `ban` / `whitelist`） |
| `append_kick_detail` | 被踢时是否附上服务端给的原始理由 |
| `show_unknown` | 没匹配到关键词的原因是否也播报 |
| `echo_console` | 控制台是否也打印一条 |
| `dedup_seconds` | 同一玩家同一原因的去重秒数 |
| `debug` | 控制台打印每条断开日志及归类结果 |
| `keywords` | 归类关键词，服务端提示语不同就往里加词 |

最小可用配置就这么长，其余项删掉也没关系（插件会用默认值补上）：

```json
{
    "config_version": 2,
    "enabled": true,
    "message": "§7[§c!§7] §e{player} §7退出游戏，原因：§f{reason}",
    "message_no_name": "§7[§c!§7] §e有玩家 §7被拒绝加入，原因：§f{reason}",
    "reason_text": {
        "kick": "被踢出服务器",
        "timeout": "连接超时",
        "ban": "被封禁",
        "whitelist": "不在白名单内"
    }
}
```

> **从 1.2.x 升级**：旧配置没有 `config_version`，插件会自动把它备份成 `config.json.bak`，
> 再生成一份新格式配置。想沿用旧文案，照着 `.bak` 里的值填到新配置即可。

## 调参建议（针对你的环境）

1. 先把 `debug` 设为 `true` 并 `!!lr reload`，然后分别用「非白名单玩家」「被封禁玩家」
   试一次，观察控制台里 `[leave_reason][debug]` 的输出，确认归类正确。
2. 如果 MeowtiWhitelist 的拦截不是原版 `not white-listed`，而是插件自己踢人（日志为
   `<玩家> lost connection: <自定义文案>`），把那段自定义文案的关键词加进 `keywords.whitelist`。
3. 正常的客户端断开（`Disconnected`）默认在 `keywords.ignore` 里被忽略，不会刷屏；需要检测就删掉它。

## 问题反馈

使用中遇到问题或想提建议，欢迎加 QQ：`2683654412` 反馈。

> 本插件为 AZ 生电服同款插件，更多玩法欢迎加入 AZ 生电服 QQ 审核群：`1101978932`。
