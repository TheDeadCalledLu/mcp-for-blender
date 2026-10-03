# MCP for Blender — 中文说明

[English](README.md) | **中文**

> 本文档是 [README.md](README.md) 的中文版，重点说明**本分支（fork）新增的功能**。
> 上游完整文档请见 [README.md](README.md)。

---

## 这是什么

MCP for Blender 通过 Model Context Protocol 把 Blender 接入任意支持 MCP 的大模型客户端
（Claude、Copilot、Cursor、Codex 等），让模型可以直接查看并操控 Blender，
实现"用自然语言做 3D 建模"。

> **本项目是 [ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender) 的社区分支**，
> **与 Blender 官方基金会无关**。

## 本分支新增内容

| 功能 | 解决什么问题 |
|---|---|
| **内嵌 MCP 服务器（Streamable HTTP，端口 9877）** | 无需在 agent 侧跑任何进程，客户端直接连 `http://localhost:9877/mcp`。 |
| **异步任务 + 轮询** | 长时间渲染/脚本不再撞上客户端约 60 秒的请求超时。用 `async=true` 启动，再轮询 `get_task_status`。 |
| **`request_id` 幂等** | 客户端重试时自动去重，代码不会被执行两次。 |
| **`render_scene` 工具** | 从相机渲染并返回图像，让模型能"看见"灯光、材质和取景——即使视口不可见也能用。 |
| **忙检测（失败开放）** | Blender 正在渲染时快速返回可操作的错误，而不是挂住。 |
| **工具注解** | `readOnlyHint` / `destructiveHint` 让客户端对安全工具跳过确认弹窗。 |
| **完整 traceback** | `execute_blender_code` 返回真实堆栈，模型能自己修错。 |
| **端点自愈** | `load_post` 处理器 + 周期性看门狗，加载文件后端点掉了会自动重启。 |

## 安装

### 1. 安装 Blender 插件

1. 下载 `addon.py`（或 `dist/` 里打包好的 zip）。
2. Blender 中：**编辑 > 偏好设置 > 插件 > 从磁盘安装…**，选择该文件。
3. 勾选启用 **Interface: MCP for Blender**。
4. 内嵌 MCP 服务器会**自动启动**，无需点任何按钮。

### 2. 让 MCP 客户端连接端点

最简单的用法**完全不需要 Python 环境**，只要连 HTTP 端点：

```json
{
  "servers": {
    "blendermcp": {
      "type": "http",
      "url": "http://localhost:9877/mcp"
    }
  }
}
```

<details>
<summary>Claude Desktop / Cursor（通过 uvx 的 stdio 桥接）</summary>

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["mcp-for-blender"]
    }
  }
}
```

Windows 下需要用 `cmd /c` 包一层：

```json
{
  "mcpServers": {
    "blender": {
      "command": "cmd",
      "args": ["/c", "uvx", "mcp-for-blender"]
    }
  }
}
```
</details>

## 环境变量

| 变量 | 默认值 | 含义 |
|---|---|---|
| `BLENDER_HOST` | `localhost` | Blender socket 服务器地址 |
| `BLENDER_PORT` | `9876` | 旧版 socket 服务器端口 |
| `DISABLE_TELEMETRY` | – | 设为 `true` 可完全关闭遥测 |

## 本分支新增的工具

| 工具 | 说明 |
|---|---|
| `render_scene` | 从相机渲染并返回图像（支持 `async`） |
| `get_task_status` | 轮询 `async=true` 启动的后台任务 |
| `cancel_task` | 丢弃正在运行的后台任务 |

其余工具（`get_scene_info`、`execute_blender_code`、Poly Haven、Hyper3D、Sketchfab、
Hunyuan3D、Poly Pizza 等）与上游一致，详见 [README.md](README.md)。

## 异步用法

任何可能超过一分钟的操作：

```jsonc
// 1. 启动任务
{ "name": "render_scene", "arguments": { "async": true, "request_id": "my-render-1" } }
// -> { "task_id": "ff09e147fe30", "state": "running" }

// 2. 轮询直到完成（渲染任务会直接返回图像）
{ "name": "get_task_status", "arguments": { "task_id": "ff09e147fe30" } }
```

## 常见问题

- **连不上** —— 确认插件已启用，端点应监听在 `127.0.0.1:9877`。**不要**同时在终端里跑 `uvx mcp-for-blender`。
- **提示 "Blender is currently rendering"** —— 这是正常的，忙检测在保护你。等渲染结束，或用 `async=true`。
- **超时** —— 长操作请用 `async=true`。
- **打开文件后端点消失** —— 通常约 5 秒内会自愈；若没有，重新启用插件。

## 安全提示

- `execute_blender_code` 会执行任意 Python，**使用前务必先保存工作**。
- Poly Haven 会下载模型/贴图/HDRI，不需要可在侧边栏关闭。
- 遥测是匿名的，可关闭（见上）。

---

## License

MIT — see [LICENSE](LICENSE). Original work © Siddharth Ahuja.
