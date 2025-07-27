class APIConfig:
    """数据库相关信息配置"""

    DB_TYPE = "postgresql"
    DB_NAME = "postgres"
    DB_USER = "postgres"
    DB_PASSWORD = "HZQ20020114"
    DB_HOST = "localhost"
    DB_PORT = "5432"
    NEED_SQL_SAMPLE = True
    LOAD_CONVERSATION_HISTORY = False# 是否加载对话历史记录


    """API配置类 存储所有API相关的参数"""

    # # # 基于云服务器的本地大模型 API配置
    API_KEY = "12345678"
    BASE_URL = "http://nl2sql.cpolar.top/v1"
    # MODEL_ID = "/data/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"# /Qwen/Qwen2.5-14B-Instruct"
    MODEL_ID = "/data/models/Qwen/Qwen2.5-32B-Instruct" #"# /Qwen/Qwen2.5-14B-Instruct"
    API_SERVICE_URL = "http://nl2sql.cpolar.top/v1"

    # # #实验室环境下的本地大模型 API配置
    # API_KEY = "ollama"
    # BASE_URL = "http://lab32b.cpolar.top/v1"
    # MODEL_ID = "qwen2.5:32b"
    # API_SERVICE_URL = "http://lab32b.cpolar.top/v1"


    # # 阿里百炼 API配置
    # API_KEY = "sk-0291493417fd484da4a166407384c3d4"
    # BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    # MODEL_ID = "qwen2.5-14b-instruct-1m"
    # API_SERVICE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # # Volces火山引擎 API配置
    # API_KEY = "4ac4a3ad-8327-416a-9254-039d6db32b65"
    # BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
    # MODEL_ID = "deepseek-v3-250324"
    # API_SERVICE_URL = "https://ark.cn-beijing.volces.com/api/v3"

    # OpenAI 原始API配置
    OPENAI_API_KEY = "sk-aiazkgkerjhgemalkkmeptvtqxzjmsbxixthjemlqslqemty"
    OPENAI_BASE_URL = "https://api.siliconflow.cn/v1"
    # OPENAI_API_KEY = "ollama"
    # OPENAI_BASE_URL = "http://nl2sql2embed.cpolar.top/v1"



    # 向量数据库嵌入模型配置
    # EMBED_MODEL_ID = "text-embedding-ada-002"
    EMBED_API_KEY = "ollama"
    EMBED_BASE_URL = "http://nl2sql2embed.cpolar.top/v1"
    EMBED_MODEL_ID = "BAAI/bge-m3"
    # EMBED_MODEL_ID = "bge-m3"
    

    
