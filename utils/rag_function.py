from pathlib import Path
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain.schema import Document
from langchain.vectorstores import Chroma 


def spilt_doc_into_chunks(file_path:str):
    '''
    @function:将简历.md文件切分成文本块
    
    @parms:
    file_path: str 简历.md的路径

    @return: 返回文档切分结果 list
    '''
    with open(file_path,'r',encoding='utf-8') as file:
        markdown_text = file.read()
    docs = []
    headers_to_split_on = {
        ("#","Title 1"),
        ("##","Title 2"),
    }
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    split_docs = markdown_splitter.split_text(markdown_text)
    for split_doc in split_docs:
        metadata = split_doc.metadata
        title_str = f"# {metadata.get('Title 1', 'None')}\n## {metadata.get('Title 2', 'None')}\n"
        page_content = title_str + split_doc.page_content.strip()
        doc = Document(
            page_content=page_content,
            metadata=metadata
        )
        docs.append(doc)
    return docs


def building_vector_database(llm,embedding_model,documents,search_k):
    '''
    @function:基于求职者简历拆分结果构建向量数据库
    
    @params:
    llm: langchain_openai.chat_models.base.ChatOpenAI 大语言模型
    embedding_model: angchain_community.embeddings.modelscope_hub.ModelScopeEmbeddings 文本嵌入模型
    documents:langchain_core.documents.base.Document 经过拆分后的文本段
    search_k：int 召回系数

    @return:返回向量检索器
    '''
    vectorstore = Chroma.from_documents(documents=documents, embedding=embedding_model)
    retriever = vectorstore.as_retriever(search_kwargs={"k": search_k})
    return retriever