import os
import sys
import json
from PyQt5.QtCore import Qt
from utils.scheduler import SCHEDULER
from utils.thread import NewTaskThread
from utils.email import EmailWindow, LookLog

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, \
    QDesktopWidget, QPushButton, QLineEdit, QLabel, QAbstractItemView, QMessageBox, QMenu

BASE_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
STATUS_MAPPING = {
    0: "初始化中",
    1: "待执行",
    2: "执行中",
    3: "执行完成",
    4: "初始化失败",
    5: "停止中",
    6: "已停止"
}

RUNNING = 1
STOPPING = 2
STOP = 3


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.select_input = None
        self.switch = STOP

        # 窗体标题
        self.setWindowTitle('斗鱼主播直播查询')
        # 窗体尺寸
        self.resize(1228, 450)
        # 窗体位置居中
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        # 创建窗体整体布局（垂直布局）
        layout = QVBoxLayout()

        layout.addLayout(self.init_header())
        layout.addLayout(self.init_select())
        layout.addLayout(self.init_table())
        layout.addLayout(self.init_bottom())
        self.setLayout(layout)

    # 第一区域
    def init_header(self):
        header_layout = QHBoxLayout()
        # 开始按钮
        start_btn = QPushButton("开始")
        start_btn.clicked.connect(self.click_start)
        header_layout.addWidget(start_btn)
        # 停止按钮
        stop_btn = QPushButton("停止")
        stop_btn.clicked.connect(self.click_stop)
        header_layout.addWidget(stop_btn)
        # 弹簧
        header_layout.addStretch()

        return header_layout

    # 第二区域
    def init_select(self):
        select_layout = QHBoxLayout()
        select_label = QLabel("房间号：")
        select_layout.addWidget(select_label)
        select_input = QLineEdit()
        self.select_input = select_input
        select_layout.addWidget(select_input)
        select_btn = QPushButton("查询")
        select_btn.clicked.connect(self.click_select_btn)
        select_layout.addWidget(select_btn)

        return select_layout

    # 第三区域
    def init_table(self):
        table_layout = QHBoxLayout()

        table = QTableWidget(0, 6)
        self.table = table
        # 设置表格不可编辑
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 表格title修改
        table_head = [
            {"field": "home_id", "text": "房间号", "width": 120},
            {"field": "name", "text": "主播名", "width": 210},
            {"field": "url", "text": "房间链接", "width": 380},
            {"field": "people", "text": "观看人数", "width": 120},
            {"field": "success", "text": "成功次数", "width": 80},
            {"field": "status", "text": "状态", "width": 100},

        ]
        for idx, info in enumerate(table_head):
            item = QTableWidgetItem()
            item.setText(info['text'])
            table.setHorizontalHeaderItem(idx, item)
            table.setColumnWidth(idx, info['width'])
        file_path = os.path.join(BASE_DIR, 'json', 'anchor.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()
        json_data = json.loads(data)
        # 查询当前表格中有多少行
        table_text_count = table.rowCount()
        for row_list in json_data:
            table.insertRow(table_text_count)
            for i, ele in enumerate(row_list):
                ele = STATUS_MAPPING[ele] if i == 5 else ele
                cell = QTableWidgetItem(str(ele))
                table.setItem(table_text_count, i, cell)
            table_text_count += 1

        table_layout.addWidget(table)

        # 添加右键功能
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self.table_right_menu)

        return table_layout

    # 第四部分
    def init_bottom(self):
        bottom_layout = QHBoxLayout()
        # 左下角状态
        self.show_text = show_text = QLabel("未检测")
        bottom_layout.addWidget(show_text)
        bottom_layout.addStretch()
        # 右侧按钮
        btn_reset = QPushButton("重新初始化")
        btn_reset.clicked.connect(self.click_reset)
        bottom_layout.addWidget(btn_reset)

        btn_reset = QPushButton("重新检测")
        bottom_layout.addWidget(btn_reset)

        btn_zero = QPushButton("次数清零")
        btn_zero.clicked.connect(self.click_zero)
        bottom_layout.addWidget(btn_zero)

        btn_del = QPushButton("删除选中数据")
        btn_del.clicked.connect(self.click_del)
        bottom_layout.addWidget(btn_del)

        btn_email = QPushButton("邮箱推送设置")
        btn_email.clicked.connect(self.click_email)
        bottom_layout.addWidget(btn_email)

        btn_ip = QPushButton("代理IP")
        bottom_layout.addWidget(btn_ip)
        return bottom_layout

    # 添加后查询，完成后添加到表单内
    def click_select_btn(self):
        print(self.switch)
        if self.switch != STOP:
            QMessageBox.warning(self,"错误","正在执行或正在停止中，请完成后操作")
            return
        # 获取输入框内容
        input_text = self.select_input.text()
        if not input_text:
            QMessageBox.warning(self, "错误", "请输入正确的房间号")
            return
        # 写入到表格中
        new_row_list = [input_text, "", "", 0, 0, 1]
        table_text_count = self.table.rowCount()
        self.table.insertRow(table_text_count)
        for i, ele in enumerate(new_row_list):
            ele = STATUS_MAPPING[ele] if i == 5 else ele
            cell = QTableWidgetItem(str(ele))
            self.table.setItem(table_text_count, i, cell)
        # 发动请求，通过爬虫爬取数据
        thread = NewTaskThread(table_text_count, input_text, self)
        thread.success.connect(self.task_success_callback)
        thread.error.connect(self.task_error_callback)
        thread.start()

    # 线程回调成功后更新数据
    def task_success_callback(self, row_num, input_text, name, url, peoples):
        # 更新主播名
        cell_name = QTableWidgetItem(name)
        self.table.setItem(row_num, 1, cell_name)
        # 主播链接
        cell_url = QTableWidgetItem(url)
        self.table.setItem(row_num, 2, cell_url)
        # 更新观看人数
        cell_peoples = QTableWidgetItem(peoples)
        self.table.setItem(row_num, 3, cell_peoples)
        # 更新状态
        cell_state = QTableWidgetItem(STATUS_MAPPING[1])
        cell_state.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.table.setItem(row_num, 5, cell_state)
        self.select_input.clear()

    # 线程回调的错误
    def task_error_callback(self, row_num, input_text, name, url):
        cell_state = QTableWidgetItem(STATUS_MAPPING[4])
        cell_state.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.table.setItem(row_num, 5, cell_state)

    # 重新检测
    def click_reset(self):
        if self.switch != STOP:
            QMessageBox.warning(self, "错误", "正在执行或正在停止中，请勿重复操作")
            return
        # 获取需要重新初始化的行
        select_row = self.table.selectionModel().selectedRows()
        if not select_row:
            QMessageBox.warning(self, "错误", "请选择要重新检测的行")
        for row_object in select_row:
            index = row_object.row()
        # 获取当前行的房间号
        home_num = self.table.item(index, 0).text().strip()
        # 更新状态
        cell_state = QTableWidgetItem(STATUS_MAPPING[2])
        cell_state.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.table.setItem(index, 5, cell_state)

        # 创建线程重新获取数据
        thread = NewTaskThread(index, home_num, self)
        thread.success.connect(self.task_success_callback)
        thread.error.connect(self.task_error_callback)
        thread.start()

    # 次数清零
    def click_zero(self):
        if self.switch != STOP:
            QMessageBox.warning(self, "错误", "正在执行或正在停止中，请勿重复操作")
            return
        select_row = self.table.selectionModel().selectedRows()
        if not select_row:
            QMessageBox.warning(self, "错误", "请选择次数清零的行")
        for row_object in select_row:
            index = row_object.row()
        # 更新状态
        cell_state = QTableWidgetItem(str(0))
        cell_state.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.table.setItem(index, 4, cell_state)

    # 删除选中项
    def click_del(self):
        if self.switch != STOP:
            QMessageBox.warning(self, "错误", "正在执行或正在停止中，请勿重复操作")
            return
        self.switch = RUNNING
        # 获取选中的行
        select_row = self.table.selectionModel().selectedRows()
        if not select_row:
            QMessageBox.warning(self, "错误", "请选择要删除的行")
        # 将表格倒序
        select_row.reverse()
        for row_object in select_row:
            index = row_object.row()
            # 删除
            self.table.removeRow(index)

    # 邮箱报警配置
    def click_email(self):
        email = EmailWindow()
        email.setWindowModality(Qt.ApplicationModal)
        email.exec()

    # 表单内右键
    def table_right_menu(self, pos):

        # 选中后才可操作
        select_item_list = self.table.selectedItems()
        if len(select_item_list) == 0:
            return
        menu = QMenu()
        item_copy = menu.addAction("复制")
        item_log = menu.addAction("查看日志")
        item_log_clear = menu.addAction("清除日志")
        action = menu.exec(self.table.mapToGlobal(pos))

        # 复制
        if action == item_copy:
            clipboard = QApplication.clipboard()
            clipboard.setText(select_item_list[0].text())

        if self.switch != STOP:
            QMessageBox.warning(self, "错误", "正在执行或正在停止中，请勿重复操作")
            return
        self.switch = RUNNING

        # 查看日志
        # 获取查看的行的房间号
        row_index = select_item_list[0].row()
        home_id = self.table.item(row_index, 0).text().strip()
        # 窗体
        log = LookLog(home_id)
        log.setWindowModality(Qt.ApplicationModal)
        log.exec()

        # 清除日志
        row_index = select_item_list[0].row()
        home_id = self.table.item(row_index, 0).text().strip()
        file_path = os.path.join("log", "{}.log".format(home_id))
        if file_path:
            os.remove(file_path)

    # 左下角状态更新
    def status_message(self, message):
        if message == "停止完成":
            self.switch = STOP
        self.show_text.setText(message)
        self.show_text.repaint()

    # 绑定开始按钮
    def click_start(self):
        if self.switch != STOP:
            QMessageBox.warning(self, "错误", "正在执行或正在停止中，请勿重复操作")
            return
        self.switch = RUNNING
        # 创建线程，每一行为一个线程
        SCHEDULER.start(
            BASE_DIR,
            self,
            self.start_callback,
            self.success_count_callback,
            self.stop_callback

        )

    # 更新左下角状态
    def start_callback(self, index):
        cell_state = QTableWidgetItem(STATUS_MAPPING[2])
        cell_state.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.table.setItem(index, 5, cell_state)
        # 更改做左下角状态
        self.status_message("检测中")

    def success_count_callback(self, index):
        # 获取表格内现有的成功次数
        new = int(self.table.item(index, 4).text().strip()) + 1
        # 更新数据
        cell_success = QTableWidgetItem(str(new))
        cell_success.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.table.setItem(index, 4, cell_success)

    def stop_callback(self, index):
        cell_state = QTableWidgetItem(STATUS_MAPPING[1])
        cell_state.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.table.setItem(index, 5, cell_state)
        # 更改做左下角状态
        self.status_message("停止中...")

    def click_stop(self):
        if self.switch != RUNNING:
            QMessageBox.warning(self, "错误", "正在执行或正在停止中，请勿重复操作")
            return
        self.switch =STOPPING
        SCHEDULER.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()
    sys.exit(app.exec())
