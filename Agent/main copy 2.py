#3.1 环境准备与库导入
#安装依赖：

#pip install openai requests beautifulsoup4 PyPDF2

#导入必要库并初始化模型客户端：
import os
import json
import time
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from openai import OpenAI
from datetime import datetime

# 设定模型名称，这里使用 qwen-plus，可根据实际情况替换
MODEL_NAME = "deepseek-v3-250324"
client = OpenAI(
    api_key="4ac4a3ad-8327-416a-9254-039d6db32b65",#os.environ.get("4ac4a3ad-8327-416a-9254-039d6db32b65"),
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)


# 3.2 定义工具函数

# 3.2.0 对话历史管理
def save_conversation(messages, file_path="conversation_history.json"):
    """保存对话历史到文件"""
    try:
        # 为每条消息添加时间戳
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "messages": messages
        }
        
        # 读取现有历史记录
        history = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        # 添加新对话
        history.append(conversation)
        
        # 保存更新后的历史记录
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
            
        return {"result": "对话历史保存成功", "error": None}
    except Exception as e:
        return {"result": None, "error": str(e)}

def load_conversation_history(file_path="conversation_history.json", max_history=5):
    """加载最近的对话历史"""
    try:
        if not os.path.exists(file_path):
            return {"result": [], "error": None}
            
        with open(file_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
            
        # 获取最近的对话记录
        recent_history = history[-max_history:] if len(history) > max_history else history
        
        # 提取消息内容
        all_messages = []
        for conversation in recent_history:
            all_messages.extend(conversation["messages"])
            
        return {"result": all_messages, "error": None}
    except Exception as e:
        return {"result": None, "error": str(e)}

# 3.2.1 执行Python代码
def exec_python_code(code: str):
    print(code)  # 打印代码便于调试
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

# 加载历史对话
history_result = load_conversation_history()
if history_result["error"] is None:
    messages = history_result["result"]
else:
    print(f"加载历史对话失败：{history_result['error']}")
    messages = []

# 如果没有历史对话，添加初始系统消息
if not messages:
    messages = [{
    "role": "system",
    "content": (
        "你是一个高效、灵活且坚持不懈的智能助手，能够自主分析并拆解用户提出的任务，"
        "始终通过执行Python代码的方式给出有效的解决方案。你具有对话历史记忆能力，"
        "可以理解和利用之前的对话内容来提供更连贯和个性化的回应。\n\n"
        "你拥有并必须调用的工具如下：\n"
        "1. exec_python_code：执行Python代码并返回执行结果或错误信息。\n"
        "2. google_search：使用Google搜索获取网页链接。\n"
        "3. fetch_webpage_content：抓取并解析指定URL的网页内容。\n"
        "4. parse_pdf：解析本地PDF文件中的文本内容。\n\n"
        "执行任务时，必须严格遵循以下原则：\n"
        "A. 每次调用工具前，都先给出明确的分步执行计划（步骤标题和目的）。\n"
        "B. 对于需要获取网络信息的任务：\n"
        "   - 首先使用google_search获取相关网页链接\n"
        "   - 然后使用fetch_webpage_content抓取具体内容\n"
        "   - 确保内容的相关性和时效性\n"
        "C. 对于需要处理PDF文档的任务：\n"
        "   - 使用parse_pdf提取文本内容\n"
        "   - 根据需求对文本进行进一步处理\n"
        "D. 若某个工具执行失败：\n"
        "   - 优先尝试其他可用工具或方法\n"
        "   - 必要时可使用exec_python_code实现替代方案\n"
        "特别注意：\n"
        "- 必须确保返回结果与用户任务高度相关\n"
        "- 对于网络内容，需验证其可靠性和时效性\n"
        "- 必须主动且深入地解决问题，不得泛泛而谈\n"
        "- 在处理大量文本时，注意提取关键信息并合理组织输出\n"
        "- 善于利用历史对话信息，保持回答的连贯性和个性化\n"
        "- 在回答问题时，考虑之前的交互内容，避免重复或矛盾的回应\n"
    )
}]
    
    
# 3.5 主循环：模型交互与工具调用
while True:
    # 获取用户输入
    user_question = input("$ ")
    if user_question.lower() in ['exit', 'quit']:
        # 保存最后的对话历史
        save_conversation(messages)
        break
        
    messages.append({"role": "user", "content": user_question})

    # 调用模型，模型有可能生成函数调用请求
    completion = client.chat.completions.create(
        model=MODEL_NAME, messages=messages, tools=tools
    )

    while True:
        # 将模型生成的消息加入对话历史
        messages.append(completion.choices[0].message)
        if completion.choices[0].message.content:
            print(completion.choices[0].message.content)
        if completion.choices[0].finish_reason == "stop":
            break
        # 如果模型请求调用工具
        for tool_call in completion.choices[0].message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            result = None
            if name == "exec_python_code":
                result = exec_python_code(args["code"])
            elif name == "baidu_search":
                result = baidu_search(args["query"], args.get("num_results", 5))
            elif name == "fetch_webpage_content":
                result = fetch_webpage_content(args["url"])
            elif name == "parse_pdf":
                result = parse_pdf(args["file_path"])
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })
        # 再次调用模型，让它基于工具返回结果生成最终回答
        completion = client.chat.completions.create(
            model=MODEL_NAME, messages=messages, tools=tools
        )
        
        # 每轮对话完成后保存对话历史
        save_result = save_conversation(messages)
        if save_result["error"] is not None:
            print(f"保存对话历史失败：{save_result['error']}")