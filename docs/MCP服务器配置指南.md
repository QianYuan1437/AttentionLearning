# MCP服务器配置完整指南

本文档详细记录了从创建Python环境到成功运行MCP服务器的完整过程，包括uv工具的安装和配置。

## 1. 环境准备

### 1.1 创建新的Python环境

首先，我们需要创建一个独立的Python环境来避免依赖冲突：

```bash
conda create -n mcp_env python=3.12 -y
conda activate mcp_env
```

### 1.2 安装uv工具

uv是一个快速的Python包安装和管理工具，我们将使用它来管理项目依赖：

```bash
pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 2. 项目配置

### 2.1 克隆项目代码

如果尚未克隆项目，请执行以下命令：

```bash
git clone https://github.com/arben-adm/sequential-thinking.git
```

### 2.2 安装项目依赖

进入项目根目录并安装所有必需的依赖项：

```bash
cd mcp-sequential-thinking-master
uv pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2.3 安装额外依赖

由于项目配置中缺少portalocker依赖，我们需要手动安装：

```bash
uv pip install portalocker -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 3. 解决常见问题

### 3.1 相对导入问题

在运行MCP服务器时，可能会遇到相对导入错误。为了解决这个问题，应该使用Python模块方式运行服务器：

```bash
python -m mcp_sequential_thinking.server
```

而不是直接运行server.py文件。

### 3.2 模块缺失问题

如果遇到`ModuleNotFoundError`错误，请确保在正确的环境中安装了所有依赖项：

```bash
# 检查依赖是否已安装
pip list | findstr portalocker

# 如果未安装，则安装它
pip install portalocker -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 4. 推荐的MCP服务器配置

在您的MCP客户端配置中，使用以下配置来启动服务器：

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "uv",
      "args": [
        "--directory",
        "D:/Code/0_MCP/mcp-sequential-thinking-master",
        "run",
        "python",
        "-m",
        "mcp_sequential_thinking.server"
      ]
    }
  }
}
```

这个配置解决了以下问题：
1. 使用`--directory`参数指向项目根目录
2. 通过`python -m`方式运行模块，避免相对导入错误
3. 保留了directory参数以符合项目结构要求

## 5. 验证服务器运行

执行上述配置后，MCP服务器应该能够成功启动，您将看到类似以下的日志输出：

```
INFO - Python version: 3.12.9
INFO - Current working directory: D:\Code\0_MCP\mcp-sequential-thinking-master
INFO - Starting Sequential Thinking MCP server
```

如果服务器成功启动而没有错误，则表示配置正确。