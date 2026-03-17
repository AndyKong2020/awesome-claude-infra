# Awesome Claude Infra

`awesome-claude-infra` 是一个独立的 Claude Code marketplace，专注收录基础设施与运行观测类插件。

当前只包含一个插件：

- `claude-session-log`

## 添加 marketplace

```bash
/plugin marketplace add AndyKong2020/awesome-claude-infra
```

## 安装插件

```bash
/plugin install claude-session-log@awesome-claude-infra
```

## 更新 marketplace

```bash
/plugin marketplace update awesome-claude-infra
```

## 插件说明

### claude-session-log

- 版本：`0.3.2`
- 分类：`utilities`
- 作用：把 Claude Code 的 transcript 与 telemetry 增量同步为项目内日志，并生成按时间命名的 `summary/<yyyy-mm-dd_hh-mm-ss>/` 与完整 `meta/` 详细产物

## 开发

运行插件测试：

```bash
python3 -m unittest discover -s plugins/claude-session-log/tests
```

## 兼容性说明

这个仓库是全新的 marketplace，不会影响旧的 `my-first-marketplace` 用户继续更新和安装原有插件版本。
