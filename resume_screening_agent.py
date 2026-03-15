from utils import tools,config,email

def main_function(pdf_path,person_email):
    if pdf_path is None:
        gr.Warning("请先上传 PDF 文件")
        return
    yield                                 
    try:
        score_list,evalu_list = tools.get_resume_evaluation(pdf_path,config.llm)
        tools.resume_evaluation(score_list)
        tools.resume_assessment_report(evalu_list,score_list,'radar_chart.png')
        email.auto_send_mail('2379849302@qq.com',person_email,'恭喜您通过我们公司的AI简历测评','AI测评结果','erhvpqwbcndtdjig','temp_report.pdf')
    except Exception as e:
        print("读取 PDF 失败：", e)    
    gr.Info("评估完成！")

import gradio as gr

# 自定义 CSS 样式 - 真正的网页端宽屏风格
custom_css = """
/* 全局背景 - 柔和浅蓝色 */
.gradio-container {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%) !important;
    min-height: 100vh;
    font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    padding: 40px 20px !important;
}

/* 主容器 - 真正的网页宽版 */
.main-card {
    background: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(12px);
    border-radius: 28px !important;
    border: 1px solid rgba(255, 255, 255, 0.5) !important;
    box-shadow: 0 15px 50px rgba(0, 105, 192, 0.15) !important;
    padding: 60px !important;
    max-width: 1100px !important; /* 大幅拉宽，适配网页 */
    margin: 0 auto !important;
}

/* 标题区域 */
.header-title {
    text-align: center;
    margin-bottom: 50px;
}
.header-title h1 {
    color: #0277bd !important;
    font-size: 2.4rem !important;
    font-weight: 700 !important;
    margin-bottom: 12px !important;
}
.header-title p {
    color: #607d8b !important;
    font-size: 1.15rem !important;
    margin: 0 !important;
}

/* 标签样式 */
label {
    color: #01579b !important;
    font-weight: 600 !important;
    font-size: 1.05rem !important;
    margin-bottom: 12px !important;
}

/* 文件上传区域 - 网页版大尺寸 */
.file-upload-area {
    background: rgba(227, 242, 253, 0.7) !important;
    border: 2px dashed #0288d1 !important;
    border-radius: 20px !important;
    padding: 60px !important;
    text-align: center !important;
    transition: all 0.3s ease !important;
    min-height: 280px !important; /* 保证网页端高度 */
    margin-bottom: 30px !important;
}
.file-upload-area:hover {
    background: rgba(187, 222, 251, 0.6) !important;
    border-color: #01579b !important;
    transform: translateY(-3px);
}

/* 输入框样式 */
.text-input-area {
    background: rgba(255, 255, 255, 0.98) !important;
    border: 1px solid #b3e5fc !important;
    border-radius: 12px !important;
    color: #333 !important;
    padding: 14px 18px !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
}
.text-input-area:focus {
    border-color: #0288d1 !important;
    box-shadow: 0 0 15px rgba(2, 136, 209, 0.28) !important;
    outline: none !important;
}

/* 按钮样式 - 网页版宽按钮 */
.eval-btn {
    background: linear-gradient(135deg, #0288d1 0%, #03a9f4 100%) !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 20px 60px !important;
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    color: white !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 8px 25px rgba(2, 136, 209, 0.35) !important;
    margin-top: 20px !important;
    width: 100% !important;
}
.eval-btn:hover {
    transform: translateY(-4px) !important;
    box-shadow: 0 12px 35px rgba(2, 136, 209, 0.45) !important;
}
.eval-btn:active {
    transform: translateY(-1px) !important;
}

/* 底部版权信息 */
.footer-text {
    text-align: center;
    color: #78909c !important;
    margin-top: 40px !important;
    font-size: 0.95rem !important;
}

/* 隐藏 Gradio 默认底部栏 */
.gradio-container .footer {
    display: none !important;
}
"""


with gr.Blocks(title="智能简历评估系统", css=custom_css) as demo:
    # 主卡片容器
    with gr.Column(elem_classes="main-card"):
        # 标题区域
        with gr.Column(elem_classes="header-title"):
            gr.Markdown("# 📄 智能简历评估系统")
            gr.Markdown("上传您的 PDF 简历，获取专业评估建议")
        
        # 文件上传
        file_input = gr.File(
            label="📎 上传简历 PDF", 
            file_types=[".pdf"], 
            type="filepath",
            elem_classes="file-upload-area"
        )
        
        # 补充信息
        text_input = gr.Textbox(
            label="📝 邮箱信息", 
            placeholder="请填写你的邮箱信息（便于后续发送结果给到您的邮箱）",
            lines=4,
            elem_classes="text-input-area"
        )
        
        # 评估按钮
        run_btn = gr.Button(
            "🚀 开始智能评估", 
            variant="primary",
            elem_classes="eval-btn"
        )
        
        # 隐藏输出
        dummy = gr.Textbox(visible=False)
    
    # 底部版权
    gr.Markdown(
        '<div class="footer-text">智能简历评估系统 © 王怡龙 2026 毕业设计 | 基于 Gradio 构建</div>'
    )

    # 绑定事件
    run_btn.click(
        main_function,
        inputs=[file_input, text_input], 
        outputs=dummy
    )

# 启动服务
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=6111, share=False)
