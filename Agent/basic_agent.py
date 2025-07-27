#3.1 环境准备与库导入
import os
import json
import math  # 新增数学库导入
from openai import OpenAI

# 程序功能介绍
print("""
欢迎使用智能助手程序！
本程序提供以下功能：
1. 执行任意Python代码
2. 进行高精度数学计算
3. 通过OpenAI API进行智能对话

输入您的问题或指令，以'$'开头即可开始交互。
""")

#以下三个参数可以根据实际情况，从模型厂商处获取
MODEL_NAME = "deepseek-v3-250324"
client = OpenAI(
    api_key="4ac4a3ad-8327-416a-9254-039d6db32b65",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)

#3.2 定义通用工具函数
def exec_python_code(code: str):
    print(code)
    try:
        exec_env = {}
        exec(code, exec_env, exec_env)
        return {"result": exec_env, "error": None}
    except Exception as e:
        print("执行失败，原因：%s" % str(e))
        return {"result": None, "error": str(e)}

# 新增数学计算函数
def math_calculator(expression: str):
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

#3.3 更新工具接口定义
tools = [
    {
        "type": "function",
        "function": {
            "name": "exec_python_code",
            "description": "执行任意Python代码，并返回执行结果或报错信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的Python代码片段。"}
                },
                "required": ["code"]
            }
        },
        "strict": True
    },
    {  # 新增数学工具
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
    }
]

#3.4 更新系统提示
messages = [{
    "role": "system",
    "content": (
        "你是一个高效、灵活且坚持不懈的智能助手，能够自主分析并拆解用户提出的任务，"
        "通过调用工具函数给出准确解决方案。\n\n"
        "可用工具列表：\n"
        "1. exec_python_code：执行任意Python代码\n"
        "2. math_calculator：执行高精度数学计算（优先调用）\n\n"
        "必须遵守的执行规则：\n"
        "A. 涉及数学计算必须优先调用math_calculator\n"
        "B. 调用工具前必须给出分步执行计划\n"
        "C. 数学表达式必须使用math模块函数（如math.sqrt）\n"
        "D. 计算结果必须保留至少6位小数精度\n"
        "E. 遇到复杂计算需自动拆分步骤验证中间结果"
    )
}]

#3.5 修改主循环
while True:
    user_question = input("$ ")
    messages.append({"role": "user", "content": user_question})

    completion = client.chat.completions.create(
        model=MODEL_NAME, messages=messages, tools=tools
    )

    while True:
        messages.append(completion.choices[0].message)
        if completion.choices[0].message.content:
            print(completion.choices[0].message.content)
        if completion.choices[0].finish_reason == "stop":
            break
            
        # 处理工具调用
        for tool_call in completion.choices[0].message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            if name == "exec_python_code":
                result = exec_python_code(args["code"])
            elif name == "math_calculator": 
                result = math_calculator(args["expression"])
            else:
                result = {"error": "未知工具调用"}
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })

        completion = client.chat.completions.create(
            model=MODEL_NAME, messages=messages, tools=tools
        )