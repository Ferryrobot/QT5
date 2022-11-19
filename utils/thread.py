import time
import random
import requests
from bs4 import BeautifulSoup
from PyQt5.QtCore import QThread, pyqtSignal


class NewTaskThread(QThread):
    success = pyqtSignal([int, str, str, str, str])
    error = pyqtSignal([int, str, str, str])

    def __init__(self, row_num, home_id, *args, **kwargs):
        super(NewTaskThread, self).__init__(*args, **kwargs)
        self.row_num = row_num
        self.home_id = home_id

    def run(self):
        try:
            url = "https://www.douyu.com/" + self.home_id
            header = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 "}
            res = requests.get(url=url, headers=header)
            if res.status_code != 200:
                raise Exception("网络连接失败")
            soup = BeautifulSoup(res.text, "lxml")
            home_name = soup.h2.string.strip()
            follow = soup.select(".Title-anchorText")[0].string.strip()
            self.success.emit(self.row_num, self.home_id, home_name, url, follow)
        except Exception as e:
            title = "{}添加失败".format(self.home_id)
            self.error.emit(self.row_num, self.home_id, title, str(e))


class TaskThread(QThread):
    start_signal = pyqtSignal([int])
    count_signal = pyqtSignal([int])
    stop_signal = pyqtSignal(int)

    def __init__(self,scheduler, log_path, index, home_id,  *args, **kwargs):
        super(TaskThread, self).__init__(*args, **kwargs)
        self.scheduler = scheduler
        self.log_path = log_path
        self.index = index
        self.home_id = home_id

    def run(self):
        # 发送状态信号
        self.start_signal.emit(self.index)
        # 发送成功次数信号
        while True:

            if self.scheduler.terminate:
                self.stop_signal.emit(self.index)
                # 将线程从列表中移除
                self.scheduler.remove_thread(self)
                return
            time.sleep(random.randint(1, 3))
            self.count_signal.emit(self.index)
            f = open(self.log_path, "a", encoding="utf-8")
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "执行成功+1\n")




class StopThread(QThread):
    update_signal = pyqtSignal(str)
    def __init__(self,scheduler,*args,**kwargs):
        super(StopThread, self).__init__(*args,**kwargs)
        self.scheduler =scheduler


    def run(self):

        while True:
            running_thread_count = len(self.scheduler.thread_list)
            self.update_signal.emit("停止中(剩余{})".format(running_thread_count))
            if running_thread_count ==0:
                break
            time.sleep(1)
        self.update_signal.emit("停止完成")