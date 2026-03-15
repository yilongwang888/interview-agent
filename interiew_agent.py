from utils import config,text_conversion,rag_function
from utils import tts_stt,agent
from langchain.text_splitter import RecursiveCharacterTextSplitter
import time
import os
import shutil
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage
from langchain.tools import Tool
from functools import partial

@tool
def generate_unique_timestamp():
    """
    @function:生成唯一的时间戳。输入始终为空字符串。

    @return:int: 唯一的时间戳，以毫秒为单位。
    """
    timestamp = int(time.time() * 1000) 
    return timestamp

@tool
def create_folder(folder_name):
    """
    @function:根据给定的文件夹名创建文件夹。

    @params:
    folder_name (str): 要创建的文件夹的名称。

    @return:str: 创建的文件夹的路径。
    """
    try:
        os.makedirs(os.path.join("chat_history", folder_name)) 
        return os.path.abspath(folder_name)
    except OSError as e:
        print(f"创建文件夹失败：{e}")
        return None

@tool
def delete_temp_folder():
    """
    @function:删除 chat_history 文件夹下的 temp 文件夹。输入始终为空字符串。

    @return:bool: 如果成功删除则返回 True，否则返回 False。
    """
    temp_folder = "chat_history/temp"  

    try:
        shutil.rmtree(temp_folder) 
        print("成功删除 temp 文件夹。")
        return True
    except Exception as e:
        print(f"删除 temp 文件夹失败：{e}")
        return False

@tool
def copy_chat_history(interview_id: str) -> str:
    """
    @function:将 chat_history/temp 文件夹中的 chat_history.txt 文件复制到 chat_history 文件夹下的以 interview_id 命名的子文件夹中。
              如果面试ID文件夹不存在，则返回相应的提示字符串。

    @params:
    interview_id (str): 面试的唯一标识符。

    @return: str: 操作结果的提示信息。
    """
    # 确定临时文件夹和面试文件夹路径
    temp_folder = os.path.join("chat_history", "temp")
    interview_folder = os.path.join("chat_history", interview_id)

    # 检查面试文件夹是否存在
    if not os.path.exists(interview_folder):
        return f"面试ID为 {interview_id} 的文件夹不存在。无法完成复制操作。"

    # 将 chat_history.txt 从临时文件夹复制到面试文件夹
    source_file = os.path.join(temp_folder, 'chat_history.txt')
    destination_file = os.path.join(interview_folder, 'chat_history.txt')

    shutil.copyfile(source_file, destination_file)

    return f"已将 chat_history.txt 复制到面试ID为 {interview_id} 的文件夹中。"

@tool
def read_chat_history(interview_id: str) -> str:
    """
    @function:读取指定面试ID文件夹下的聊天记录(chat_history.txt)内容。

    @params:
    interview_id (str): 面试的唯一标识符。

    @return:str: 聊天记录的内容。
    """
    # 确定面试文件夹路径
    interview_folder = os.path.join("chat_history", interview_id)

    # 检查面试文件夹是否存在
    if not os.path.exists(interview_folder):
        return f"面试ID为 {interview_id} 的文件夹不存在。无法读取聊天记录。"

    # 读取聊天记录文件内容
    chat_history_file = os.path.join(interview_folder, 'chat_history.txt')
    with open(chat_history_file, 'r', encoding='utf-8') as file:
        chat_history_content = file.read()

    return chat_history_content

@tool
def generate_markdown_file(interview_id: str, interview_feedback: str) -> str:
    """
    @function:将给定的面试反馈内容生成为 Markdown 文件，并保存到指定的面试ID文件夹中。

    @params:
    interview_id (str): 面试的唯一标识符。
    interview_feedback (str): 面试反馈的内容。

    @return:str: 操作结果的提示信息。
    """
    # 确定面试文件夹路径
    interview_folder = os.path.join("chat_history", interview_id)

    # 检查面试文件夹是否存在
    if not os.path.exists(interview_folder):
        return f"面试ID为 {interview_id} 的文件夹不存在。无法生成 Markdown 文件。"

    # 生成 Markdown 文件路径
    markdown_file_path = os.path.join(interview_folder, "面试报告.md")

    try:
        # 写入 Markdown 文件
        with open(markdown_file_path, 'w', encoding='utf-8') as file:
            # 写入标题和面试反馈
            file.write("# 面试报告\n\n")
            file.write("## 面试反馈：\n\n")
            file.write(interview_feedback)
            file.write("\n\n")

            # 读取 chat_history.txt 文件内容并写入 Markdown 文件
            chat_history_file_path = os.path.join(interview_folder, "chat_history.txt")
            if os.path.exists(chat_history_file_path):
                file.write("## 面试记录：\n\n")
                with open(chat_history_file_path, 'r', encoding='utf-8') as chat_file:
                    for line in chat_file:
                        file.write(line.rstrip('\n') + '\n\n')  # 添加换行符

        return f"已生成 Markdown 文件: {markdown_file_path}"
    except Exception as e:
        return f"生成 Markdown 文件时出错: {str(e)}"


def _find_most_relevant_block_from_cv(sentence: str,retriever) -> str:
    """
    @function:当你需要根据职位描述（JD）中的技能关键词去简历文本中找到相关内容时，就可以调用这个函数。

    @params:
    sentence (str): 包含技能关键词的句子。
    retriever: 已初始化好的向量检索器，调用方负责传入
    
    @return:str: 最相关的文本块。
    """
    try:
        most_relevant_docs = retriever.get_relevant_documents(sentence)
        print(len(most_relevant_docs))

        if most_relevant_docs:
            most_relevant_texts = [doc.page_content for doc in most_relevant_docs]
            most_relevant_text = "\n".join(most_relevant_texts)
            return most_relevant_text
        else:
            return "未找到相关文本块"
    except Exception as e:
        print(f"find_most_relevant_block_from_cv()发生错误：{e}")
        return "函数发生错误，未找到相关文本块"


def save_chat_history(chat_history, folder_name):
    """
    将聊天记录存储到指定的文件夹下的chat_history.txt文件中。

    Args:
        chat_history (list): 聊天记录列表，每个元素是一个AIMessage或HumanMessage对象。
        folder_name (str): 聊天记录文件夹的名称。

    Returns:
        str: 保存的文件路径，如果保存失败则返回None。
    """
    try:
        file_path = os.path.join(folder_name, "chat_history.txt")  # chat_history.txt文件路径
        with open(file_path, "w", encoding="utf-8") as file:
            for message in chat_history:
                if isinstance(message, AIMessage):
                    speaker = "面试官"
                elif isinstance(message, HumanMessage):
                    speaker = "应聘者"
                else:
                    continue  # 忽略不是面试官或应聘者的消息
                file.write(f"{speaker}: {message.content}\n")  # 将每条聊天记录写入文件，每条记录占一行
        return file_path  # 返回保存的文件路径
    except Exception as e:
        print(f"保存聊天记录失败：{e}")
        return None

def create_chat_agent(llm,system_prompt):
    """
    @function: 创建面试智能体agent

    @params: 
    llm: langchain_openai.chat_models.base.ChatOpenAI 大语言模型
    system_prompt : str 系统提示词

    @return: agent 返回面试智能体
    """
    
    tools = [generate_unique_timestamp, create_folder, copy_chat_history, read_chat_history, generate_markdown_file, Tool(
            name="find_most_relevant_block_from_cv",
            description="根据 JD 句子在简历里找最相关段落",
            func=partial(_find_most_relevant_block_from_cv, retriever=retriever)
        ),]
    
    #绑定prompt工作流
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    #Agent绑定工具
    llm_with_tools = llm.bind_tools(tools)

    #构建智能体
    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_to_openai_tool_messages(
                x["intermediate_steps"]
            ),
            "chat_history": lambda x: x["chat_history"],
        }
        | prompt
        | llm_with_tools
        | OpenAIToolsAgentOutputParser()
    )
    
    return agent
    
def run_agent(llm,system_prompt,retriever,voice):
    #初始化智能体
    agent = create_chat_agent(llm,system_prompt)
    tools = [generate_unique_timestamp, create_folder, copy_chat_history, read_chat_history, generate_markdown_file, Tool(
            name="find_most_relevant_block_from_cv",
            description="根据 JD 句子在简历里找最相关段落",
            func=partial(_find_most_relevant_block_from_cv, retriever=retriever)
        ),]
    #启动智能体
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    #问答历史
    chat_history = []

    user_input = "开始面试"
    print(user_input)

    while True:
        result = agent_executor.invoke({"input": user_input, "chat_history": chat_history})
        voice.Speech(result['output'])
        print(result['output'])
        chat_history.extend(
            [
                HumanMessage(content=user_input),
                AIMessage(content=result["output"]),
            ]
        )
        # 存储聊天记录到临时文件夹
        temp_folder = "chat_history/temp"  # 临时文件夹名称
        os.makedirs(temp_folder, exist_ok=True)  # 创建临时文件夹，如果不存在则创建
        save_chat_history(chat_history, temp_folder)

        # 获取用户下一条输入
        user_input = input("user: ")

        # 检查用户输入是否为 "exit"
        if user_input == "exit":
            print("用户输入了 'exit'，程序已退出。")
            break


cv_file_path = "test_data/wyl.pdf"
output_file_path = "test_data/wyl.md"
text_conversion.parse_cv_to_md(config.llm, cv_file_path,output_file_path)
docs = rag_function.spilt_doc_into_chunks('test_data/wyl.md')
retriever = rag_function.building_vector_database(config.llm,config.embedding_model,docs,4)
jd_file_path = "test_data/jd.txt"
output_file_path = "test_data/jd.json"
jd_json_file_path = text_conversion.parse_jd_to_json(config.llm, jd_file_path,output_file_path)
jd_json_file_path = "test_data/jd.json"
jd_dict = text_conversion.read_json(jd_json_file_path)
job_title = jd_dict.get('基本信息').get('职位')
job_key_skills = jd_dict.get('专业技能/知识/能力')
system_prompt = config.create_system_prompt(job_title,job_key_skills)

def interview_chat(message, history):
    """
    Gradio 4.x+ 聊天回调函数（使用全局变量）
    :param message: 用户当前输入
    :param history: 聊天历史（Gradio 4.x 格式：list[dict]）
    :return: 空字符串（清空输入框），更新后的聊天历史
    """
    # 使用全局变量获取无法拷贝的对象
    llm = GLOBAL_LLM
    system_prompt = GLOBAL_SYSTEM_PROMPT
    retriever = GLOBAL_RETRIEVER
    voice = GLOBAL_VOICE

    # 1. 初始化智能体
    agent = create_chat_agent(llm, system_prompt)
    tools = [
        generate_unique_timestamp, 
        create_folder, 
        copy_chat_history, 
        read_chat_history, 
        generate_markdown_file,
        Tool(
            name="find_most_relevant_block_from_cv",
            description="根据 JD 句子在简历里找最相关段落",
            func=partial(_find_most_relevant_block_from_cv, retriever=retriever)
        ),
    ]
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # 2. 转换Gradio 4.x 历史格式为智能体需要的格式（HumanMessage/AIMessage）
    agent_chat_history = []
    for msg in history:
        if msg["role"] == "user":
            agent_chat_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            agent_chat_history.append(AIMessage(content=msg["content"]))

    # 3. 调用智能体处理用户输入
    result = agent_executor.invoke({
        "input": message, 
        "chat_history": agent_chat_history
    })
    ai_response = result['output']

    # 4. 语音播放
    voice.Speech(ai_response)

    # 5. 更新聊天历史（Gradio 4.x 格式）
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": ai_response})

    # 6. 保存聊天记录（转换为智能体格式）
    temp_folder = "chat_history/temp"
    os.makedirs(temp_folder, exist_ok=True)
    
    save_history = []
    for msg in history:
        if msg["role"] == "user":
            save_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            save_history.append(AIMessage(content=msg["content"]))
    save_chat_history(save_history, temp_folder)

    return "", history


def launch_interview_interface(llm=None, system_prompt=None, retriever=None, voice=None): 
    global GLOBAL_LLM, GLOBAL_SYSTEM_PROMPT, GLOBAL_RETRIEVER, GLOBAL_VOICE 
    GLOBAL_LLM = llm if llm is not None else GLOBAL_LLM
    GLOBAL_SYSTEM_PROMPT = system_prompt if system_prompt is not None else GLOBAL_SYSTEM_PROMPT
    GLOBAL_RETRIEVER = retriever if retriever is not None else GLOBAL_RETRIEVER
    GLOBAL_VOICE = voice if voice is not None else MockVoice() 

    custom_css = """
    @import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap");
    
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }
    
    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        background: linear-gradient(135deg, #e0f2fe 0%, #bfdbfe 50%, #93c5fd 100%) !important;
        min-height: 100vh !important;
        overflow-x: hidden !important;
        position: relative !important;
    }
    
    body::before {
        content: '';
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: 
            radial-gradient(circle at 20% 80%, rgba(147, 197, 253, 0.25) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(96, 165, 250, 0.2) 0%, transparent 50%),
            radial-gradient(circle at 40% 40%, rgba(59, 130, 246, 0.15) 0%, transparent 50%);
        animation: float 25s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }
    
    @keyframes float {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        33% { transform: translate(30px, -30px) rotate(120deg); }
        66% { transform: translate(-20px, 20px) rotate(240deg); }
    }
    
    .gradio-container {
        max-width: 68% !important;
        width: 68% !important;
        margin: 20px auto !important;
        padding: 0 !important;
        background: transparent !important;
        position: relative !important;
        z-index: 1;
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 24px;
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.08);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-card:hover {
        border-color: rgba(255, 255, 255, 0.2);
        box-shadow: 
            0 16px 56px rgba(0, 0, 0, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.12);
        transform: translateY(-2px);
    }
    
    .neon-title {
        background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 50%, #93c5fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: shimmer 4s ease-in-out infinite;
        background-size: 200% 200%;
        text-shadow: 0 0 30px rgba(59, 130, 246, 0.3);
    }
    
    @keyframes shimmer {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .glow-button {
        background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
        border: none;
        border-radius: 16px;
        padding: 16px 40px;
        font-weight: 700;
        font-size: 1rem;
        color: white;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 
            0 6px 24px rgba(59, 130, 246, 0.5),
            0 0 0 rgba(59, 130, 246, 0);
        position: relative;
        overflow: hidden;
        letter-spacing: 0.5px;
    }
    
    .glow-button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        transition: left 0.6s ease;
    }
    
    .glow-button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 
            0 12px 36px rgba(59, 130, 246, 0.7),
            0 0 30px rgba(59, 130, 246, 0.4);
    }
    
    .glow-button:hover::before {
        left: 100%;
    }
    
    .glow-button:active {
        transform: translateY(-1px) scale(0.98);
    }
    
    .status-glow {
        animation: statusPulse 2.5s ease-in-out infinite;
    }
    
    @keyframes statusPulse {
        0%, 100% { 
            box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.8);
        }
        50% { 
            box-shadow: 0 0 0 12px rgba(34, 197, 94, 0);
        }
    }
    
    .floating-icon {
        animation: iconFloat 3.5s ease-in-out infinite;
    }
    
    @keyframes iconFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-6px); }
    }
    
    .gradient-border {
        position: relative;
        background: rgba(255, 255,255, 0.06);
        border-radius: 16px;
        overflow: hidden;
    }
    
    .gradient-border::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        border-radius: 16px;
        padding: 2.5px;
        background: linear-gradient(135deg, #6366f1, #8b5cf6, #d946ef, #6366f1);
        background-size: 300% 300%;
        animation: borderGlow 5s ease infinite;
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        pointer-events: none;
    }
    
    @keyframes borderGlow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    textarea {
        background: #ffffff !important;
        border: 2px solid rgba(0, 0, 0, 0.15) !important;
        border-radius: 16px !important;
        padding: 16px 20px !important;
        font-size: 1rem !important;
        color: #000000 !important;
        transition: all 0.3s ease !important;
        line-height: 1.5 !important;
        resize: none !important;
    }
    
    textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 6px rgba(99, 102, 241, 0.2) !important;
        background: #ffffff !important;
        outline: none !important;
    }
    
    textarea::placeholder {
        color: rgba(0, 0, 0, 0.5) !important;
    }
    
    .status-input {
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        letter-spacing: 0.3px;
    }
    
    .chat-container {
        background: rgba(255, 255, 255, 0.06) !important;
        border-radius: 24px !important;
        overflow: hidden !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4) !important;
    }
    
    .chat-container [data-testid="chatbot"] {
        padding: 24px !important;
        height: 100% !important;
        overflow-y: auto !important;
    }
    
    .chat-container [data-testid="chatbot"] > div {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    .chat-container [data-testid="chatbot"] > div > div {
        display: flex !important;
        flex-direction: column !important;
        gap: 20px !important;
    }
    
    .chat-container [data-testid="chatbot"] > div > div > div {
        display: flex !important;
        align-items: flex-start !important;
        gap: 16px !important;
        animation: messageSlide 0.5s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .chat-container [data-testid="chatbot"] > div > div > div[data-testid*="assistant"] {
        flex-direction: row !important;
    }
    
    .chat-container [data-testid="chatbot"] > div > div > div[data-testid*="user"] {
        flex-direction: row-reverse !important;
    }
    
    .chat-container [data-testid="chatbot"] > div > div > div > div:first-child {
        width: 52px !important;
        height: 52px !important;
        min-width: 52px !important;
        min-height: 52px !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 1.6rem !important;
        flex-shrink: 0 !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
        border: 3px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    .chat-container [data-testid="chatbot"] > div > div > div[data-testid*="assistant"] > div:first-child {
        background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%) !important;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.4) !important;
    }
    
    .chat-container [data-testid="chatbot"] > div > div > div[data-testid*="user"] > div:first-child {
        background: linear-gradient(135deg, #93c5fd 0%, #e0f2fe 100%) !important;
        box-shadow: 0 0 20px rgba(147, 197, 253, 0.4) !important;
    }
    
    .chat-container [data-testid="chatbot"] > div > div > div > div:last-child {
        padding: 18px 26px !important;
        border-radius: 20px !important;
        max-width: 72% !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2) !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    .chat-container [data-testid="chatbot"] > div > div > div[data-testid*="assistant"] > div:last-child {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.95) 0%, rgba(96, 165, 250, 0.95) 100%) !important;
        border-left: 4px solid #3b82f6 !important;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.25) !important;
    }
    
    .chat-container [data-testid="chatbot"] > div > div > div[data-testid*="user"] > div:last-child {
        background: linear-gradient(135deg, rgba(147, 197, 253, 0.95) 0%, rgba(225, 245, 254, 0.95) 100%) !important;
        border-right: 4px solid #93c5fd !important;
        box-shadow: 0 6px 20px rgba(147, 197, 253, 0.25) !important;
    }
    
    .chat-container [data-testid="chatbot"] > div > div > div > div:last-child > p {
        color: #1e293b !important;
        font-size: 1.05rem !important;
        line-height: 1.7 !important;
        font-weight: 500 !important;
        margin: 0 !important;
    }
    
    @keyframes messageSlide {
        from {
            opacity: 0;
            transform: translateY(20px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    .custom-textbox {
    width: 100% !important;
    height: 80px !important;
    resize: none !important;
    border-radius: 16px !important;
    padding: 16px 20px !important;
   }

    """

    with gr.Blocks(title="AI虚拟面试") as demo: 
        
        gr.HTML("""
        <div class="glass-card" style="
            padding: 36px 44px;
            margin-bottom: 24px;
            text-align: center;
            position: relative;
            overflow: hidden;
        ">
            <div style="
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
                animation: rotate 25s linear infinite;
            "></div>
            <h1 class="neon-title" style="
                margin: 0;
                font-size: 2.6rem;
                font-weight: 800;
                letter-spacing: -1px;
                position: relative;
                z-index: 1;
            "> 🙋‍♂️AI虚拟面试🙋‍♂️</h1>
            <p style="
                margin: 12px 0 0 0;
                font-size: 1.1rem;
                color: #000000;
                font-weight: 500;
                position: relative;
                z-index: 1;
                letter-spacing: 0.5px;
            ">专业 · 高效 · 个性化的AI面试体验</p>
        </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=3):
                gr.HTML("""
                <div class="glass-card" style="
                    padding: 16px 24px;
                ">
                    <div style="display: flex; gap: 24px; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                        <div style="display: flex; gap: 24px; align-items: center;">
                            <span class="floating-icon" style="
                                font-size: 1.3rem;
                                padding: 10px 16px;
                                background: rgba(99, 102, 241, 0.25);
                                border-radius: 12px;
                                color: #8b5cf6;
                            ">💬</span>
                            <span style="
                                font-size: 0.95rem;
                                color: #000000;
                                font-weight: 600;
                                letter-spacing: 0.3px;
                            ">输入回答</span>
                        </div>
                        <div style="display: flex; gap: 24px; align-items: center;">
                            <span class="floating-icon" style="
                                font-size: 1.3rem;
                                padding: 10px 16px;
                                background: rgba(217, 70, 239, 0.25);
                                border-radius: 12px;
                                color: #d946ef;
                            ">🚪</span>
                            <span style="
                                font-size: 0.95rem;
                                color: #000000;
                                font-weight: 600;
                                letter-spacing: 0.3px;
                            ">exit结束</span>
                        </div>
                        <div style="display: flex; gap: 24px; align-items: center;">
                            <span class="floating-icon" style="
                                font-size: 1.3rem;
                                padding: 10px 16px;
                                background: rgba(16, 185, 129, 0.25);
                                border-radius: 12px;
                                color: #10b981;
                            ">🤔</span>
                            <span style="
                                font-size: 0.95rem;
                                color: #000000;
                                font-weight: 600;
                                letter-spacing: 0.3px;
                            ">深度追问</span>
                        </div>
                    </div>
                </div>
                """)
            
            with gr.Column(scale=1):
                gr.HTML("""
                <div class="gradient-border" style="
                    padding: 14px 20px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                ">
                    <div style="
                        width: 16px;
                        height: 16px;
                        background: #22c55e;
                        border-radius: 50%;
                        class: status-glow
                    "></div>
                """)
                status_text = gr.Textbox(
                    value="✅ 系统就绪",
                    label="",
                    interactive=False,
                    show_label=False,
                    container=False,
                    scale=0,
                    elem_classes="status-input"
                )
                gr.HTML("</div>")
        
        gr.HTML('<div class="chat-container">')
        chatbot = gr.Chatbot(
            label="",
            value=[{"role": "assistant", "content": "你好！欢迎参加本次面试，我是你的智能面试官。请先做一下自我介绍吧。"}],
            height=700,
            show_label=False,
            elem_classes="chat-container"
        )
        gr.HTML('</div>')
        
        # 关键修改1：替换HTML文本框为Gradio原生Textbox，确保能获取输入内容
        with gr.Row(elem_classes="glass-card"):
            gr.HTML("<div style='width:100%; padding: 20px 24px;'>")  # 新增
            msg_input = gr.Textbox(
                placeholder="请输入你的回答，输入 exit 结束面试...",
                lines=4,
                elem_id="user-input",
                elem_classes="custom-textbox"  # 新增自定义类名，用CSS控制样式
            )
            # 关键修改2：使用Gradio原生按钮，移除HTML按钮，确保点击事件生效
            submit_btn = gr.Button("🚀 发送", elem_classes="glow-button")
        
        gr.HTML("""
        <div style="
            text-align: center;
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.9rem;
            padding: 16px;
            font-weight: 600;
            margin-top: 12px;
            letter-spacing: 0.5px;
        ">
            <span style="
                background: linear-gradient(135deg, #3b82f6, #60a5fa);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-weight: 700;
            ">© 2026 毕业设计 wyl</span> | 专业AI面试解决方案
        </div>
        """)

        # 关键修改3：修复生成器函数的逻辑错误，正确更新状态文本
        def wrapped_chat(msg, chatbot_history): 
            # 检查空输入
            if not msg or msg.strip() == "":
                yield "", chatbot_history, "❌ 输入不能为空！"
                return
            
            # 更新状态为思考中
            yield "", chatbot_history, "🤔 思考中..." 
            # 调用核心聊天函数
            new_msg, new_chatbot = interview_chat(msg, chatbot_history) 
            # 更新状态为等待回答
            yield new_msg, new_chatbot, "✅ 等待回答..." 

        # 关键修改4：绑定按钮点击和回车事件到正确的组件
        submit_btn.click(
            fn=wrapped_chat, 
            inputs=[msg_input, chatbot], 
            outputs=[msg_input, chatbot, status_text]
        )
        msg_input.submit(
            fn=wrapped_chat, 
            inputs=[msg_input, chatbot], 
            outputs=[msg_input, chatbot, status_text]
        )

# 运行界面
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7870, 
        share=False,
        css=custom_css,  # 移到这里
        theme=gr.themes.Soft(  # 移到这里
        primary_hue="indigo",
        secondary_hue="purple",
        neutral_hue="slate",
    )
    )

