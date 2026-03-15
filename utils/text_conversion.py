import fitz
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    @function: 从 PDF 中提取纯文本

    @params:
    pdf_path: str pdf文件的路径

    @return: str pdf文件的纯文本字符串
    """
    
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def parse_cv_to_md(llm, cv_file_path: str,output_file_path:str):
    """
    @function: 将给定的简历文件内容（支持 PDF）解析为 Markdown，并存储到指定路径下。

    @params:
    llm: langchain_openai.chat_models.base.ChatOpenAI 大语言模型
    file_path : str pdf文件位置
    output_file_path: str 输出md格式文件

    @return: None
    """
    try:
        if cv_file_path.lower().endswith('.pdf'):
            cv_content = extract_text_from_pdf(cv_file_path)
        else:
            with open(cv_file_path, 'r', encoding='utf-8') as cv_file:
                cv_content = cv_file.read().strip()

        if not cv_content:
            print("警告：简历内容为空，无法继续处理。")
            return None

        template = """
                   基于简历文本，按照约束，转换成Markdown格式：

                   简历文本：
                   [{cv_content}]

                   约束：
                   1、只用一级标题和二级标题分出来简历的大块和小块
                   2、一级标题从文本中自行提取，如个人基本信息，项目（比赛）经历，获奖情况，(sci)论文发表情况等
                   3、一级标题下的二级标题的内容详细一点
                   4、要求对简历文本的一二级标题详细分类，不要错过简历文本的任何信息,不要出现“其他情况详见简历文本”这类信息，获奖名称，论文名称等都要详细提取出来

                   Markdown：
                    """

        parser = StrOutputParser()
        prompt = PromptTemplate(template=template, input_variables=["cv_content"])
        chain = prompt | llm | parser

        result = chain.invoke({"cv_content": cv_content})

        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(result.strip("```").strip())
            output_file.write("\n\n")

        print(f"已存储最终 Markdown 文件到 {output_file_path}")
        return None

    except Exception as e:
        print(f"解析 CV 文件时出错: {str(e)}")
        return None


import json
from pathlib import Path
import fitz  
from docx import Document  
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

def extract_text(file_path: str) -> str:
    """
    @function: 统一入口：支持 txt / pdf / docx 转换为纯文本形式

    @params :
    file_path : 支持 txt / pdf / docx 文件路径

    @return: 返回完整的文本内容
    """
    path = file_path.lower()
    if path.endswith(".pdf"):
        doc = fitz.open(file_path)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text.strip()
    elif path.endswith(".docx"):
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    else:                       
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()


def parse_jd_to_json(llm, jd_file_path: str,output_file_path: str):
    """
    @function : 将给定的 JD 文件（txt/pdf/docx）解析为 JSON 并保存

    @params:
    llm : langchain_openai.chat_models.base.ChatOpenAI 大语言模型
    jd_file_path : str 公司招聘要求文件的位置，支持 txt / pdf / docx
    output_file_path: str 生成的招聘要求文件json的位置
    
    @return:    生成的 json 文件路径
    """
    try:
        jd_content = extract_text(jd_file_path)
        if not jd_content:
            print("警告：JD 内容为空")
            return None

        template = """
                 基于JD文本，按照约束，生成以下格式的 JSON 数据：
                 {{
                    "基本信息": {{
                    "职位": "职位名称",
                    "薪资": "薪资范围",
                    "地点": "工作地点",
                    "经验要求": "经验要求",
                    "学历要求": "学历要求",
                    "其他":""
                 }},
                "岗位职责": {{
                "具体职责": ["职责1", "职责2", ...]
                 }},
                "岗位要求": {{
                            "学历背景": "学历要求",
                            "工作经验": "工作经验要求",
                            "技能要求": ["技能1", "技能2", ...],
                            "个人特质": ["特质1", "特质2", ...]
                           }},
                           "专业技能/知识/能力": ["技能1", "技能2", ...],
                            "其他信息": {{}}
                           }}

                JD文本：
                [{jd_content}]

                约束：
                1、除了`专业技能/知识/能力`键，其他键的值都从原文中获取。
                2、保证JSON里的值全面覆盖JD原文，不遗漏任何原文，不知如何分类就放到`其他信息`里。
                3、`专业技能/知识/能力`键对应的值要求从JD全文中（尤其是岗位职责、技能要求部分）提取总结关键词或关键短句，不能有任何遗漏的硬技能。

                JSON：
                """
        parser = JsonOutputParser()
        prompt = PromptTemplate(
            template=template,
            input_variables=["jd_content"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = prompt | llm | parser
        result = chain.invoke({"jd_content": jd_content})

        print("专业技能/知识/能力 =>", result.get("专业技能/知识/能力"))

        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"已存储 JD JSON 到 {output_file_path}")
        return None

    except Exception as e:
        print(f"解析 JD 文件时出错: {str(e)}")
        return None

def read_json(file_path: str) -> dict:
    """
    读取 JSON 文件并返回其内容。

    参数:
        file_path (str): JSON 文件的路径。

    返回:
        dict: JSON 文件的内容。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        return data
    except Exception as e:
        print(f"读取 JSON 文件时出错: {str(e)}")
        return {}