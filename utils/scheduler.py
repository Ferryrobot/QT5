import os
from .thread import TaskThread
from .thread import StopThread


class Scheduler(object):
    def __init__(self):
        self.thread_list = []
        self.window = None
        self.terminate = False

    def start(self, base_dir, window, fn_start, fn_count, fn_stop):

        self.window = window
        self.terminate = False
        # 获取有多少行，为每行创建线程
        for index in range(window.table.rowCount()):
            home_id = window.table.item(index, 0).text().strip()
            status = window.table.item(index, 5).text().strip()

            log_file_path = os.path.join(base_dir, "log")

            if not log_file_path:
                os.mkdir(os.path.join(log_file_path))
            log_path = os.path.join(log_file_path, "{}.log".format(home_id))

            if status != "待执行":
                continue

            thread = TaskThread(self,log_path, index, home_id, window)
            thread.start_signal.connect(fn_start)
            thread.count_signal.connect(fn_count)
            thread.stop_signal.connect(fn_stop)
            thread.start()
            # 将线程添加到列表
            self.thread_list.append(thread)
    def stop(self):
        self.terminate = True
        # 创建线程，检测thread_list内剩余线程，并更新到窗体左下角中
        # self.window.status_message()
        thread_stop = StopThread(self,self.window)
        thread_stop.update_signal.connect(self.window.status_message)
        thread_stop.start()

    def remove_thread(self,thread):
        self.thread_list.remove(thread)

SCHEDULER = Scheduler()
