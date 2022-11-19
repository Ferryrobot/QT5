import os
import json
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, \
    QDesktopWidget, QPushButton, QLineEdit, QLabel, QAbstractItemView, QMessageBox, QDialog, QTextEdit


class EmailWindow(QDialog):
    def __init__(self, *args, **kwargs):
        super(EmailWindow, self).__init__()
        self.field_dict = {}
        self.init_ui()

    def init_ui(self):
        """
        初始化对话框
        """
        self.setWindowTitle("邮件报警配置")
        self.resize(300, 270)
        layout = QVBoxLayout()
        date_list = [
            {"title": "SMTP服务器", "field": "smtp"},
            {"title": "发件人", "field": "from"},
            {"title": "密码", "field": "pwd"},
            {"title": "收件人(用逗号分割)", "field": "to"}
        ]
        # 读取文件中的配置
        old_Data_dict = {}
        field_path = os.path.join("json", "email.json")
        if os.path.exists(field_path):
            email_field = open(field_path, "r", encoding="utf-8")
            old_Data_dict = json.load(email_field)
            email_field.close()
        for item in date_list:
            lbl = QLabel()
            lbl.setText(item["title"])
            layout.addWidget(lbl)
            text = QLineEdit()
            layout.addWidget(text)
            field_text = item["field"]
            if old_Data_dict and field_text in old_Data_dict:
                text.setText(old_Data_dict[field_text])
            self.field_dict[item["field"]] = text
        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self.click_Save)
        layout.addWidget(btn_save)
        layout.addStretch()
        self.setLayout(layout)

    def click_Save(self):
        data_dict = {}
        for key, field in self.field_dict.items():
            value = field.text().strip()
            if not value:
                QMessageBox.warning(self, "错误", "配置错误")
            data_dict[key] = value
        # 保存数据
        field = open(os.path.join("json", "email.json"), "w", encoding="utf-8")
        json.dump(data_dict, field)
        field.close()
        self.close()


class LookLog(QDialog):
    def __init__(self, home_id, *args, **kwargs):
        super().__init__()
        self.home_id = home_id
        self.init_ui()
    def init_ui(self):
        """
        初始化对话框
        """
        self.setWindowTitle("日志信息")
        self.resize(500, 400)
        layout = QVBoxLayout()
        text = QTextEdit()
        text.setText("")
        layout.addWidget(text)
        self.setLayout(layout)

        # 显示日志
        file_path = os.path.join("log", "{}.log".format(self.home_id))
        if not file_path:
            return
        f = open(file_path, 'r', encoding="utf-8")
        context = f.read()
        text.setText(context)
