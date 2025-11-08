# GitHub MCP 配置指南

## 什么是 MCP？

Model Context Protocol (MCP) 是由 Anthropic 开发的开放标准，用于标准化 AI 系统与外部工具、系统和数据源的集成。

## 配置步骤

### 1. 创建 GitHub Personal Access Token (PAT)

1. 访问 GitHub Settings: https://github.com/settings/tokens
2. 点击 "Generate new token" -> "Generate new token (classic)"
3. 设置 Token 名称（例如：`MCP Access Token`）
4. 选择以下权限：
   - `repo` - 完整仓库访问权限
   - `read:org` - 读取组织信息（如果需要）
   - `read:user` - 读取用户信息
5. 点击 "Generate token"
6. **重要**：复制并保存 Token（只显示一次）

### 2. 在 Cursor 中配置 MCP

#### 方法一：通过 Cursor 设置

1. 打开 Cursor
2. 按 `Ctrl+Shift+P` (Windows) 或 `Cmd+Shift+P` (Mac)
3. 输入 "MCP" 或 "Model Context Protocol"
4. 选择配置 MCP 服务器

#### 方法二：手动编辑配置文件

配置文件位置：
- **Windows**: `%APPDATA%\Cursor\User\globalStorage\rooveterinaryinc.roo-cline\mcp.json`
- **Mac**: `~/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/mcp.json`
- **Linux**: `~/.config/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/mcp.json`

### 3. 配置文件内容

将以下配置添加到 MCP 配置文件中：

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "你的_GitHub_PAT_令牌"
      }
    }
  }
}
```

### 4. 使用官方 GitHub MCP 服务器

GitHub 官方 MCP 服务器：[github/github-mcp-server](https://github.com/github/github-mcp-server)

**安装方式：**
- 通过 npx: `@github/github-mcp-server`
- 或下载二进制文件
- 或使用 Docker

**功能包括：**
- 🔍 搜索仓库、代码、用户
- 📝 创建和管理 Issues、Pull Requests
- 🔐 安全扫描和漏洞管理
- ⭐ 管理星标仓库
- 🤖 GitHub Copilot 集成
- 📊 查看仓库统计和活动
- 🔒 只读模式支持
- 🎯 动态工具集发现（Beta）

### 5. 替代方案：使用 HTTP MCP 服务器

如果需要使用 HTTP 方式连接：

```json
{
  "mcpServers": {
    "github-remote": {
      "type": "http",
      "url": "https://api.github.com",
      "headers": {
        "Authorization": "Bearer 你的_GitHub_PAT_令牌",
        "Accept": "application/vnd.github.v3+json"
      }
    }
  }
}
```

### 6. 验证配置

1. 重启 Cursor
2. 在聊天界面中，MCP 工具应该可用
3. 尝试询问："搜索我的 GitHub 仓库"

## 安全注意事项

⚠️ **重要安全提示：**

1. **不要将 PAT 提交到 Git 仓库**
2. 使用环境变量存储敏感信息
3. 定期轮换 Token
4. 只授予必要的权限
5. 使用 `.gitignore` 排除配置文件（如果包含敏感信息）

## 故障排除

### 问题：MCP 服务器无法连接

**解决方案：**
- 检查 PAT 是否正确
- 确认 PAT 权限是否足够
- 检查网络连接
- 查看 Cursor 的日志输出

### 问题：找不到配置文件

**解决方案：**
- 确认 Cursor 版本 >= 1.101
- 手动创建配置文件目录
- 检查文件权限

### 问题：权限不足

**解决方案：**
- 重新生成 PAT，确保包含所需权限
- 检查仓库访问权限

## 参考资源

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [GitHub MCP 服务器](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
- [GitHub API 文档](https://docs.github.com/en/rest)

