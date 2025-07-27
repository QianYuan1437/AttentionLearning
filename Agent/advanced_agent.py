#3.1 环境准备与库导入
import os
import json
import time
import math
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from openai import OpenAI
from datetime import datetime

MODEL_NAME = "deepseek-v3-250324"
client = OpenAI(
    api_key="4ac4a3ad-8327-416a-9254-039d6db32b65",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)

#3.2 定义工具函数

# 3.2.0 对话历史管理
# 配置参数
CONVERSATION_CONFIG = {
    "max_history": 5,  # 默认保留的最大对话数量
    "max_context_messages": 10,  # 每个对话保留的最大消息数量
    "history_file": "conversation_history.json"
}

def generate_conversation_title(messages):
    """根据对话内容生成标题"""
    # 获取用户的第一条消息作为标题基础
    user_messages = []
    for msg in messages:
        if hasattr(msg, 'role') and msg.role == "user" and hasattr(msg, 'content'):
            user_messages.append(msg.content)
        elif isinstance(msg, dict) and msg.get("role") == "user":
            user_messages.append(msg.get("content", ""))
    
    if user_messages:
        # 取第一条用户消息的前30个字符作为标题
        title = user_messages[0][:30].strip()
        return title + ("..." if len(user_messages[0]) > 30 else "")
    return "新对话会话"

def save_conversation(messages, file_path=CONVERSATION_CONFIG["history_file"]):
    """保存对话历史到文件"""
    try:
        print("开始保存对话历史...")
        print(f"消息数量: {len(messages)}")
        
        # 序列化消息对象
        serialized_messages = []
        # 确保只保留最近的消息，并且不会超过配置的最大消息数量
        recent_messages = messages[-CONVERSATION_CONFIG["max_context_messages"]:] if len(messages) > CONVERSATION_CONFIG["max_context_messages"] else messages
        
        # 创建已处理消息ID的集合，用于去重
        processed_ids = set()
        
        for msg in recent_messages:
            # 检查消息是否为空或无效
            if not msg:
                continue
                
            # 获取消息ID（如果有）用于去重
            msg_id = id(msg) if not isinstance(msg, dict) else hash(str(msg))
            if msg_id in processed_ids:
                continue
            processed_ids.add(msg_id)
            
            # 基本消息属性
            if isinstance(msg, dict):
                # 处理字典类型的消息
                serialized_msg = {
                    "role": msg.get("role", ""),
                    "content": msg.get("content", "")
                }
                # 处理字典中的tool_calls
                if "tool_calls" in msg and isinstance(msg["tool_calls"], list):
                    tool_calls_data = []
                    for tool_call in msg["tool_calls"]:
                        if isinstance(tool_call, dict) and "function" in tool_call and "id" in tool_call:
                            tool_call_data = {
                                "function": {
                                    "name": str(tool_call["function"].get("name", "")),
                                    "arguments": str(tool_call["function"].get("arguments", ""))
                                },
                                "id": str(tool_call["id"])
                            }
                            tool_calls_data.append(tool_call_data)
                    if tool_calls_data:
                        serialized_msg["tool_calls"] = tool_calls_data
            else:
                # 处理对象类型的消息
                serialized_msg = {
                    "role": str(msg.role if hasattr(msg, 'role') else ""),
                    "content": str(msg.content if hasattr(msg, 'content') else "")
                }
                
                # 处理对象中的tool_calls
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    try:
                        tool_calls = msg.tool_calls
                        if isinstance(tool_calls, list):
                            tool_calls_data = []
                            for tool_call in tool_calls:
                                if hasattr(tool_call, 'function') and hasattr(tool_call, 'id'):
                                    tool_call_data = {
                                        "function": {
                                            "name": str(tool_call.function.name),
                                            "arguments": str(tool_call.function.arguments)
                                        },
                                        "id": str(tool_call.id)
                                    }
                                    tool_calls_data.append(tool_call_data)
                            if tool_calls_data:
                                serialized_msg["tool_calls"] = tool_calls_data
                    except Exception as e:
                        print(f"处理tool_calls时出错: {str(e)}")
                        # 如果tool_calls结构不完整，跳过该部分
                        pass
            
            # 只添加有效的消息（角色不为空）
            if serialized_msg["role"]:
                serialized_messages.append(serialized_msg)
                print(f"已处理消息: {serialized_msg['role']}")
        
        # 确保至少有一条用户消息用于生成标题
        user_messages = [msg for msg in messages if (isinstance(msg, dict) and msg.get("role") == "user") or 
                        (hasattr(msg, 'role') and msg.role == "user")]
        
        # 生成对话标题并添加时间戳
        title = ""
        if user_messages:
            # 获取第一条用户消息的内容
            first_user_msg = user_messages[0]
            user_content = ""
            if isinstance(first_user_msg, dict):
                user_content = first_user_msg.get("content", "")
            elif hasattr(first_user_msg, 'content'):
                user_content = first_user_msg.content
                
            # 生成标题
            if user_content:
                title = user_content[:30].strip()
                if len(user_content) > 30:
                    title += "..."
        
        # 如果没有有效的用户消息，使用默认标题
        if not title:
            title = "新对话会话"
            
        conversation = {
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "messages": serialized_messages
        }
        print(f"生成对话标题: {title}")
        
        # 读取现有历史记录
        history = []
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                print(f"已读取现有历史记录，共{len(history)}条对话")
            except json.JSONDecodeError:
                print("历史记录文件格式错误，将创建新的历史记录")
                history = []
        else:
            print("历史记录文件不存在，将创建新文件")
        
        # 添加新对话
        history.append(conversation)
        
        # 保存更新后的历史记录
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"对话历史已保存到文件: {file_path}")
            
        return {"result": "对话历史保存成功", "error": None}
    except Exception as e:
        error_msg = f"保存对话历史时发生错误: {str(e)}"
        print(error_msg)
        return {"result": None, "error": error_msg}

def load_conversation_history(file_path="conversation_history.json", max_history=5):
    """加载最近的对话历史"""
    try:
        if not os.path.exists(file_path):
            return {"result": [], "error": None}
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误：{str(e)}")
            return {"result": [], "error": f"JSON解析错误：{str(e)}"}
            
        if not isinstance(history, list):
            return {"result": [], "error": "历史记录格式错误：不是有效的列表"}
            
        # 获取最近的对话记录
        recent_history = history[-max_history:] if len(history) > max_history else history
        
        # 提取消息内容
        all_messages = []
        for conversation in recent_history:
            if isinstance(conversation, dict) and "messages" in conversation:
                all_messages.extend(conversation["messages"])
            
        return {"result": all_messages, "error": None}
    except Exception as e:
        print(f"加载历史记录时发生错误：{str(e)}")
        return {"result": [], "error": str(e)}

# 3.2.1 执行Python代码
def exec_python_code(code: str):
    print(code)  # 打印代码便于调试
    
    # 分析代码中的import语句
    import_lines = [line.strip() for line in code.split('\n') if line.strip().startswith('import ') or line.strip().startswith('from ')]
    
    # 提取需要安装的包名
    packages_to_install = []
    for line in import_lines:
        if line.startswith('import '):
            packages = line[7:].split(',')
            packages_to_install.extend([pkg.strip().split(' ')[0] for pkg in packages])
        elif line.startswith('from '):
            package = line[5:].split(' ')[0]
            packages_to_install.append(package)
    
    # 检查并安装缺失的包
    import importlib
    import subprocess
    
    for package in set(packages_to_install):
        try:
            importlib.import_module(package)
        except ImportError:
            print(f"检测到缺失依赖: {package}, 正在尝试安装...")
            try:
                subprocess.check_call(['pip', 'install', package, '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple'])
                print(f"成功安装: {package}")
            except Exception as e:
                print(f"安装失败: {package}, 错误: {str(e)}")
                return {"result": None, "error": f"依赖安装失败: {package}"}
    
    try:
        exec_env = {}
        exec(code, exec_env, exec_env)
        return {"result": exec_env, "error": None}
    except Exception as e:
        print("执行失败，原因：%s" % str(e))
        return {"result": None, "error": str(e)}

# 3.2.2 百度搜索获取网页链接
def baidu_search(query: str, num_results: int = 5) -> list:
    try:
        search_url = f"https://www.baidu.com/s?wd={query}&rn={num_results}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        search_results = []
        for result in soup.find_all('div', class_='result')[:num_results]:
            link_tag = result.find('a', class_='c-showurl') or result.find('a', class_='c-link')
            if link_tag and link_tag.get('href'):
                link = link_tag.get('href')
                if link.startswith('http'):
                    search_results.append(link)
        return {"result": search_results, "error": None}
    except Exception as e:
        return {"result": None, "error": str(e)}

# 3.2.3 抓取并解析网页内容
def fetch_webpage_content(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        # 移除脚本和样式元素
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        # 清理文本
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return {"result": text, "error": None}
    except Exception as e:
        return {"result": None, "error": str(e)}

# 3.2.4 解析PDF文件
def parse_pdf(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return {"result": text, "error": None}
    except Exception as e:
        return {"result": None, "error": str(e)}

# 3.2.5 数学计算工具
def math_calculator(expression: str):
    """执行高精度数学计算，支持复数、三角函数、指数对数等运算"""
    print(f"正在计算表达式：{expression}")  # 调试输出
    try:
        # 创建安全计算环境，允许访问math模块
        allowed_env = {"math": math, "__builtins__": {}}
        result = eval(expression, {"__builtins__": None}, allowed_env)
        return {"result": result, "error": None}
    except Exception as e:
        error_msg = f"数学计算错误：{str(e)}"
        print(error_msg)
        return {"result": None, "error": error_msg}
    
# 3.3 工具接口定义：告诉模型有哪些可调用工具

tools = [
    {
        "type": "function",
        "function": {
            "name": "exec_python_code",
            "description": "执行任意Python代码，并返回执行结果或报错信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要执行的Python代码片段。"
                    }
                },
                "required": ["code"]
            }
        },
        "strict": True
    },
    {
        "type": "function",
        "function": {
            "name": "math_calculator",
            "description": "执行高精度数学计算，支持复数、三角函数、指数对数等运算，保证计算准确率。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "需要计算的数学表达式，例如：'(2**3 + math.sqrt(25)) * math.pi'"
                    }
                },
                "required": ["expression"]
            }
        },
        "strict": True
    },
    {
        "type": "function",
        "function": {
            "name": "baidu_search",
            "description": "使用百度搜索获取网页链接。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询关键词。"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "返回结果数量，默认为5。",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        },
        "strict": True
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_webpage_content",
            "description": "抓取并解析指定URL的网页内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要抓取的网页URL。"
                    }
                },
                "required": ["url"]
            }
        },
        "strict": True
    },
    {
        "type": "function",
        "function": {
            "name": "parse_pdf",
            "description": "解析本地PDF文件中的文本内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "PDF文件的本地路径。"
                    }
                },
                "required": ["file_path"]
            }
        },
        "strict": True
    }
]

# 3.4 精心设计的 Prompt：引导模型自主决策
messages = [{
    "role": "system",
    "content": (
        "你是一个高效、灵活且坚持不懈的智能助手，能够自主分析并拆解用户提出的任务，"
        "始终通过执行Python代码的方式给出有效的解决方案。\n\n"
        "你拥有并必须调用的工具如下：\n"
        "1. exec_python_code：执行Python代码并返回执行结果或错误信息。\n"
        "2. baidu_search：使用百度搜索获取网页链接。\n"
        "3. fetch_webpage_content：抓取并解析指定URL的网页内容。\n"
        "4. parse_pdf：解析本地PDF文件中的文本内容。\n\n"
        "执行任务时，必须严格遵循以下原则：\n"
        "A. 每次调用工具前，都先给出明确的分步执行计划（步骤标题和目的）。\n"
        "B. 对于需要获取网络信息的任务：\n"
        "   - 首先使用baidu_search获取相关网页链接\n"
        "   - 然后使用fetch_webpage_content抓取具体内容\n"
        "   - 确保内容的相关性和时效性\n"
        "C. 对于需要处理PDF文档的任务：\n"
        "   - 使用parse_pdf提取文本内容\n"
        "   - 根据需求对文本进行进一步处理\n"
        "D. 若某个工具执行失败：\n"
        "   - 优先尝试其他可用工具或方法\n"
        "   - 必要时可使用exec_python_code实现替代方案\n"
        "E. 对于时间相关的查询：\n"
        "   - 必须使用exec_python_code获取实时的系统时间\n"
        "   - 确保返回的时间信息是准确且实时的\n"
        "特别注意：\n"
        "- 必须确保返回结果与用户任务高度相关\n"
        "- 对于网络内容，需验证其可靠性和时效性\n"
        "- 必须主动且深入地解决问题，不得泛泛而谈\n"
        "- 在处理大量文本时，注意提取关键信息并合理组织输出\n"
        "- 涉及时间的查询必须返回实时准确的信息\n"
    )
}]

# 3.5 主循环：模型交互与工具调用
def display_conversation_info():
    """显示当前对话配置信息"""
    print(f"\n当前对话配置：")
    print(f"- 最大历史记录数：{CONVERSATION_CONFIG['max_history']}")
    print(f"- 单次对话最大消息数：{CONVERSATION_CONFIG['max_context_messages']}")
    print(f"- 历史记录文件：{CONVERSATION_CONFIG['history_file']}\n")

while True:
    # 获取用户输入
    user_question = input("$ ")
    
    # 处理配置相关命令
    if user_question.startswith("/config"):
        try:
            cmd_parts = user_question.split()
            if len(cmd_parts) == 3:
                key = cmd_parts[1]
                value = int(cmd_parts[2])
                if key in ["max_history", "max_context_messages"]:
                    CONVERSATION_CONFIG[key] = value
                    print(f"已更新配置：{key} = {value}")
                    display_conversation_info()
                    continue
        except (ValueError, IndexError):
            pass
        print("配置命令格式：/config [max_history|max_context_messages] <数值>")
        continue
    elif user_question == "/status":
        display_conversation_info()
        continue
    
    # 如果是时间相关的查询，先获取当前时间
    if any(keyword in user_question.lower() for keyword in ["时间", "日期", "几号", "星期", "周"]):
        current_time = datetime.now()
        time_info = f"\n### 当前日期和时间\n{current_time.strftime('%Y年%m月%d日 %H:%M:%S')} {['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'][current_time.weekday()]}\n\n"
        user_question = time_info + user_question
    
    messages.append({"role": "user", "content": user_question})

    # 调用模型获取回复
    completion = client.chat.completions.create(
        model=MODEL_NAME, messages=messages, tools=tools
    )

    while True:
        messages.append(completion.choices[0].message)
        if completion.choices[0].message.content:
            print(completion.choices[0].message.content)
        if completion.choices[0].finish_reason == "stop":
            # 保存对话历史
            save_conversation(messages)
            break
            
        # 处理工具调用
        for tool_call in completion.choices[0].message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            if name == "exec_python_code":
                result = exec_python_code(args["code"])
            elif name == "baidu_search":
                result = baidu_search(args["query"], args.get("num_results", 5))
            elif name == "fetch_webpage_content":
                result = fetch_webpage_content(args["url"])
            elif name == "parse_pdf":
                result = parse_pdf(args["file_path"])
            elif name == "math_calculator":
                result = math_calculator(args["expression"])
            else:
                result = {"error": "未知工具调用"}
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })

        # 继续对话
        completion = client.chat.completions.create(
            model=MODEL_NAME, messages=messages, tools=tools
        )