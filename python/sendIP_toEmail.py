#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author  : Jinzhong Xu
# @Contact : jinzhongxu@csu.ac.cn
# @Time    : 2021/11/5 19:02
# @File    : send_message.py
# @Software: PyCharm

import json
import os
import socket
import base64
import os
import smtplib
import requests
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr


def get_temp_ip(current_ip):
    """
    检查是否IP改变和是否是重启状态
    :param current_ip: 当前 IP 地址
    :return: 是否发送邮件、当前 IP 地址、电脑是否是重启
    """
    reboot = False
    temp_ip_json_path = "/tmp/ip.json"
    if (not os.path.exists(temp_ip_json_path)) or (
            not os.path.getsize(temp_ip_json_path)
    ):
        reboot = True
        print("No {}, dump it.".format(temp_ip_json_path))
        with open(temp_ip_json_path, "w") as jo:
            json.dump(current_ip, jo)
            return True, current_ip, reboot

    else:
        with open(temp_ip_json_path, "r") as jo:
            origin_ip = json.load(jo)
        if origin_ip == current_ip:
            print("Current ip {} do not change, no need to send".format(current_ip))
            return False, current_ip, reboot
        else:
            print(
                "The ip updated from {} to {}, update it.".format(origin_ip, current_ip)
            )
            os.remove(temp_ip_json_path)
            with open(temp_ip_json_path, "w") as jo:
                json.dump(current_ip, jo)
                return True, current_ip, reboot


def get_global_ip():
    """
    获取电脑的外网 IP 地址
    :return: 外围 IP
    """
    # try:
    #     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #     s.connect(("8.8.8.8", 80))
    #     ip = s.getsockname()[0]
    # finally:
    #     s.close()
    ip = requests.get('https://checkip.amazonaws.com').text.strip()

    return ip


def get_status():
    """
    获取电脑状态，包括是否 IP 改变、是否重启
    :return: 是否发送通知邮件
    """
    global_ips = get_global_ip()
    whether_to_send, send_ip, reboot = get_temp_ip(global_ips)
    send_ip = json.dumps(send_ip)
    return whether_to_send, send_ip, reboot


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, "utf-8").encode(), addr))


def mail(
        # send email
        sender="xxxxxxxxx@qq.com",
        # send email empower code
        password="ZHpxxxg==",
        # recv email
        recipients=("xxxxxxxxxx@163.com", ),
        smtp_server="smtp.qq.com",
        port=465,
        subject="服务器 IP 改变",
        text="",
        attachment=("",),
):
    msg = MIMEMultipart()
    msg["From"] = _format_addr("Match <%s>" % sender)
    msg["To"] = _format_addr("管理员 <%s>" % ", ".join(list(recipients)))
    msg["Subject"] = Header(subject, "utf-8").encode()
    # 邮件正文是MIMEText:
    msg.attach(MIMEText(text, "plain", "utf-8"))

    attachment = list(attachment)
    if attachment != [""]:
        for i, file_path in enumerate(attachment):
            with open(file_path, "rb") as f:
                # 设置附件的MIME和文件名:
                file_dir, file_name = os.path.split(os.path.abspath(file_path))
                filename_extension = file_name.split(".")
                mime = MIMEBase("file", filename_extension[-1], filename=file_name)
                # 加上必要的头信息:
                mime.add_header("Content-Disposition", "attachment", filename=file_name)
                mime.add_header("Content-ID", f"<{i}>")
                mime.add_header("X-Attachment-Id", f"{i}")
                # 把附件的内容读进来:
                mime.set_payload(f.read())
                # 用Base64编码:
                encoders.encode_base64(mime)
                # 添加到MIMEMultipart:
                msg.attach(mime)

    server = smtplib.SMTP_SSL(smtp_server, port)
    # 控制打印日志
    # server.set_debuglevel(2)
    try:
        server.login(
            sender,
            base64.b64decode(password.encode(), altchars=None, validate=False).decode(),
        )
        server.sendmail(sender, list(recipients), msg.as_string())
        logs = f"{sender} 给 {'; '.join(recipients)} 的邮件发送成功"
    except smtplib.SMTPException:
        logs = "Error: 无法发送邮件"
    finally:
        server.quit()
    return logs


if __name__ == "__main__":
    whether_to_send, global_ips, reboot = get_status()
    if whether_to_send and reboot:
        mail(subject="服务器重启成功", text=f"重启后的IP:{global_ips}")
    elif whether_to_send and (not reboot):
        mail(text=f"新的IP:{global_ips}")
    else:
        print("wait and no send")
