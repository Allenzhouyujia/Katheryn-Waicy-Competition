# 快速设置 GitHub MCP

## 步骤 1: 获取 GitHub Personal Access Token

1. 访问：https://github.com/settings/tokens/new
2. 设置名称：`Cursor MCP Token`
3. 选择权限：
   - ✅ `repo` (完整仓库访问)
   - ✅ `read:org` (读取组织信息，可选)
   - ✅ `read:user` (读取用户信息)
4. 点击 "Generate token"
5. **复制 Token**（只显示一次！）

## 步骤 2: 在 Cursor 中配置

### 方法 A: 通过 Cursor 设置界面

1. 打开 Cursor
2. `Ctrl+Shift+P` (Windows) 或 `Cmd+Shift+P` (Mac)
3. 输入：`MCP: Configure MCP Servers`
4. 添加新服务器：
   - **名称**: `github`
   - **命令**: `npx`
   - **参数**: `-y`, `@github/github-mcp-server`
   - **环境变量**: 
     - `GITHUB_PERSONAL_ACCESS_TOKEN` = `你的Token`

### 方法 B: 手动编辑配置文件

配置文件位置：
- Windows: `%APPDATA%\Cursor\User\globalStorage\rooveterinaryinc.roo-cline\mcp.json`
- Mac: `~/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/mcp.json`

创建或编辑 `mcp.json`：

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@github/github-mcp-server"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_你的Token在这里"
      }
    }
  }
}
```

## 步骤 3: 重启 Cursor

重启后，MCP 服务器应该可用。

## 测试

在 Cursor 聊天中尝试：
- "搜索我的 GitHub 仓库"
- "列出我的仓库"
- "查看 Katheryn-Waicy-Competition 仓库的信息"

## 安全提示

⚠️ **重要**：
- 不要将包含真实 Token 的 `mcp.json` 提交到 Git
- 使用环境变量或 Cursor 的加密存储
- Token 已添加到 `.gitignore` 中

