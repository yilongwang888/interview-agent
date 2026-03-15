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