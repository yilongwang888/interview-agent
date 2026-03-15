import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.mime.multipart import MIMEMultipart

def auto_send_mail(sender,receiver,content,headercontent,autosouquan,pdf_path):
    '''
    @params:
    sender: str 发送者的邮箱
    receiver: str 收信者的邮箱
    content: str 正文内容
    headercontent: str 头标题内容
    autosouquan: str 发送者邮箱授权码
    pdf_path :str 评估pdf的位置
    '''

    # 配置环境 连接服务器
    server = 'smtp.qq.com'
    smtp = smtplib.SMTP_SSL(server, 465)
    smtp.login(sender, autosouquan)

    # 正文内容 即邮件显示内容
    msg = MIMEMultipart()
    msg.attach(MIMEText(content, 'plain', 'utf-8'))
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = Header(headercontent, 'utf-8')

    # 附件内容
    with open(pdf_path, 'rb') as f:
        att = MIMEText(f.read(), 'base64', 'utf-8')
    att['Content-Type'] = 'application/octet-stream'
    att.add_header('Content-Disposition', 'attachment',
                   filename=('utf-8', '', 'output.pdf'))
    msg.attach(att)

    # 发送
    smtp.sendmail(sender, receiver, msg.as_string())
    smtp.quit()

    print('发送成功')