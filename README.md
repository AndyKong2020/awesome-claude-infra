# Awesome Claude Infra

`awesome-claude-infra` 是一个独立的 Claude Code marketplace，专注收录基础设施与运行观测类插件。

当前包含两个插件：

- `claude-session-log`
- `gitcode-api`

## 添加 marketplace

```bash
/plugin marketplace add AndyKong2020/awesome-claude-infra
```

## 安装插件

```bash
/plugin install claude-session-log@awesome-claude-infra
/plugin install gitcode-api@awesome-claude-infra
```

## 更新 marketplace

```bash
/plugin marketplace update awesome-claude-infra
```

## 插件说明

### claude-session-log

- 版本：`0.4.2`
- 分类：`utilities`
- 作用：把 Claude Code 的 transcript 与 telemetry 增量同步为项目内日志，默认写到 `./.agents-log`，并生成按时间命名的 session 总览、按 agent 拆分的 `summary/`，以及按 agent 拆分的 `meta/` 详细产物

### gitcode-api

- 版本：`1.0.0`
- 分类：`development`
- 作用：把 GitCode REST API 技能、参考文档索引和请求辅助脚本打包成 Claude Code 插件，便于在会话中直接查接口、做 dry-run 或执行请求

## 开发

运行插件测试：

```bash
python3 -m unittest discover -s plugins/claude-session-log/tests
```

## 兼容性说明

这个仓库是全新的 marketplace，不会影响旧的 `my-first-marketplace` 用户继续更新和安装原有插件版本。
