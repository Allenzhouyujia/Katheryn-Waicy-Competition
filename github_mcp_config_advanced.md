# GitHub MCP 高级配置

基于 [GitHub 官方 MCP 服务器](https://github.com/github/github-mcp-server)

## 安装方式

### 方式 1: 使用 npx (推荐)

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
        "GITHUB_PERSONAL_ACCESS_TOKEN": "你的Token"
      }
    }
  }
}
```

### 方式 2: 使用二进制文件

1. 从 [GitHub Releases](https://github.com/github/github-mcp-server/releases) 下载二进制文件
2. 配置：

```json
{
  "mcpServers": {
    "github": {
      "command": "/path/to/github-mcp-server",
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "你的Token"
      }
    }
  }
}
```

### 方式 3: 使用 Docker

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e", "GITHUB_PERSONAL_ACCESS_TOKEN=你的Token",
        "ghcr.io/github/github-mcp-server"
      ]
    }
  }
}
```

## 高级功能

### 1. 只读模式

防止意外修改仓库，只提供只读工具：

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@github/github-mcp-server",
        "--read-only"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "你的Token"
      }
    }
  }
}
```

或使用环境变量：
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@github/github-mcp-server"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "你的Token",
        "GITHUB_READ_ONLY": "1"
      }
    }
  }
}
```

### 2. 动态工具集发现 (Beta)

减少可用工具数量，避免模型混淆：

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@github/github-mcp-server",
        "--dynamic-toolsets"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "你的Token"
      }
    }
  }
}
```

或使用环境变量：
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@github/github-mcp-server"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "你的Token",
        "GITHUB_DYNAMIC_TOOLSETS": "1"
      }
    }
  }
}
```

### 3. 自定义工具描述

创建 `github-mcp-server-config.json` 文件（与二进制文件同目录）：

```json
{
  "TOOL_ADD_ISSUE_COMMENT_DESCRIPTION": "添加评论到 Issue",
  "TOOL_CREATE_BRANCH_DESCRIPTION": "在 GitHub 仓库中创建新分支"
}
```

或使用环境变量：
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@github/github-mcp-server"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "你的Token",
        "GITHUB_MCP_TOOL_ADD_ISSUE_COMMENT_DESCRIPTION": "添加评论到 Issue"
      }
    }
  }
}
```

### 4. 导出翻译

导出当前工具描述以便自定义：

```bash
./github-mcp-server --export-translations
cat github-mcp-server-config.json
```

## 可用工具类别

### 仓库操作
- 搜索仓库
- 获取仓库信息
- 创建/删除分支
- 管理文件

### Issues 管理
- 创建/更新 Issues
- 添加评论
- 管理标签
- 搜索 Issues

### Pull Requests
- 创建/更新 PR
- 合并 PR
- 查看 PR 评论
- 管理审查

### 代码搜索
- 搜索代码
- 搜索提交
- 查看文件内容

### 安全
- 安全扫描
- 漏洞管理
- 安全建议

### Copilot 集成
- 使用 Copilot 创建 PR
- 管理 Copilot Spaces

### 其他
- 用户搜索
- 星标管理
- GitHub 支持文档搜索

## 权限要求

GitHub Personal Access Token 需要以下权限：

**最小权限（只读模式）：**
- `public_repo` - 访问公共仓库
- `read:org` - 读取组织信息（可选）

**完整权限：**
- `repo` - 完整仓库访问
- `workflow` - 管理 GitHub Actions（可选）
- `write:org` - 写入组织信息（可选）

## 故障排除

### 问题：Token 无效

**解决方案：**
- 确认 Token 格式正确（以 `ghp_` 开头）
- 检查 Token 是否过期
- 验证权限是否足够

### 问题：工具不可用

**解决方案：**
- 检查是否使用了 `--read-only` 模式
- 确认 Token 权限
- 查看 Cursor 日志

### 问题：连接超时

**解决方案：**
- 检查网络连接
- 确认 GitHub API 可访问
- 检查防火墙设置

## 参考资源

- [GitHub MCP 服务器仓库](https://github.com/github/github-mcp-server)
- [GitHub API 文档](https://docs.github.com/en/rest)
- [MCP 协议文档](https://modelcontextprotocol.io/)

