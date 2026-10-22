# LeaveReason —— Detect abnormal player disconnections

> 🌟 The same plugin used by the AZ Tech Server. Join the AZ Tech Server QQ review group: `1101978932`

A [MCDReforged](https://github.com/Fallen-Breath/MCDReforged) plugin that parses server console logs,
detects why players disconnected abnormally, and broadcasts the reason to the **public chat**.

This plugin only fills in the "why" of a disconnection; the "who left" part itself is shown by the server or a chat forwarding plugin.

## Detectable reasons

| Reason | Description | Public chat example |
| --- | --- | --- |
| Kicked | Kicked by an admin/plugin | `xxx left the game, reason: kicked from server (You have been removed)` |
| Connection timeout | Client timed out | `xxx left the game, reason: connection timed out` |
| Banned | Banned at login (in banlist) | `xxx left the game, reason: banned` |
| Not whitelisted | Blocked by the whitelist at login | `xxx left the game, reason: not whitelisted` |
| Uncategorized | Other reasons not matching any keyword | `xxx left the game, reason: Attempting to attack an invalid entity` |

All texts are customizable (see below); the above are the default effects.

## How it works

- **Kicked / timeout**: happens in-game, console log is `<player> lost connection: <reason>`, player name is directly available.
- **Banned**: blocked by the vanilla `banlist.json` at the login stage, log is `Disconnecting <address>: You are banned ...`.
- **Whitelist**: blocked by the vanilla `whitelist.json` whitelist mechanism at the login stage,
  log is `Disconnecting <address>: You are not white-listed ...`.

> ⚠️ When "banned / whitelist" is blocked at the login stage, the backend log usually **does not record the player name**,
> so the plugin falls back to the `message_no_name` template (default "A player was refused to join, reason: …").
> This is because the Minecraft backend log itself doesn't record the name — not a plugin bug.

## Installation

Put `leave_reason.mcdr` into MCDR's `plugins/` directory, then:

```
!!MCDR plugin load leave_reason.mcdr
```

(or restart MCDR.)

## Commands

| Command | Description | Permission |
| --- | --- | --- |
| `!!lr` | Show help | **4** |
| `!!lr on` | Enable broadcasting | **4** |
| `!!lr off` | Disable broadcasting | **4** |
| `!!lr reload` | Reload config | **4** |
| `!!lr status` | Show current status | **4** |

> Permission level 4 = MCDR owner / console. Level 3 and below get a "permission denied" message.
> The command prefix `!!lr` is defined by the `PREFIX` constant in the plugin code; change that one place if you want a different prefix.

## Configuration

On first load, `config/leave_reason/config.json` is generated automatically. The file contains self-explanatory
Chinese comment fields (items starting with `_` are ignored by the plugin). Apply changes with `!!lr reload`.

Only these fields really need attention:

| Field | Purpose |
| --- | --- |
| `enabled` | Master switch |
| `message` / `message_no_name` | Public chat message format, `{player}`=player name, `{reason}`=reason |
| `reason_text` | Display text for the four reason categories (`kick` / `timeout` / `ban` / `whitelist`) |
| `append_kick_detail` | Whether to append the server's raw kick reason |
| `show_unknown` | Whether to also broadcast uncategorized reasons |
| `echo_console` | Whether to also print a line in the console |
| `dedup_seconds` | Dedup window (seconds) for the same player + reason |
| `debug` | Print every disconnect log and its classification in the console |
| `keywords` | Classification keywords; add words here if your server's messages differ |

The minimal usable config is this short; you can delete the rest (the plugin fills defaults):

```json
{
    "config_version": 2,
    "enabled": true,
    "message": "§7[§c!§7] §e{player} §7left the game, reason: §f{reason}",
    "message_no_name": "§7[§c!§7] §eA player §7was refused to join, reason: §f{reason}",
    "reason_text": {
        "kick": "Kicked from server",
        "timeout": "Connection timed out",
        "ban": "Banned",
        "whitelist": "Not whitelisted"
    }
}
```

> **Upgrading from 1.2.x**: old configs have no `config_version`; the plugin backs them up as `config.json.bak`
> and generates a new-format config. To keep your old wording, copy the values from the `.bak` into the new config.

## Tuning tips

1. First set `debug` to `true` and run `!!lr reload`, then test with a "non-whitelisted player" and a "banned player"
   separately, watching the `[leave_reason][debug]` output in the console to confirm the classification is correct.
2. If the whitelist block is not vanilla `not white-listed` but a plugin kicking players (log like
   `<player> lost connection: <custom text>`), add keywords from that custom text to `keywords.whitelist`.
3. Normal client disconnects (`Disconnected`) are ignored by default in `keywords.ignore` and won't spam the chat;
   remove it if you need to detect them.

## Feedback

If you run into problems or have suggestions, feel free to contact QQ: `2683654412`.

> This is the same plugin used by the AZ Tech Server. For more gameplay, join the AZ Tech Server QQ review group: `1101978932`.
