import sys
import os
import subprocess
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
                             QMessageBox, QLabel, QHBoxLayout, QTextEdit, QDialog,
                             QFormLayout, QSpinBox, QDialogButtonBox, QTabWidget,
                             QLineEdit, QFileDialog, QGridLayout, QMenuBar, QMenu,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
import json
from config import Config
from simulator import SimulatorController # 假设模拟器控制逻辑在 SimulatorController 中
from entity.user import User
from workers.adb_worker import AdbWorker # 从 workers 子目录导入

# --- 从 ui 目录导入对话框 ---
from ui.account_dialog import AccountDialog
from ui.settings_dialog import SettingsDialog


# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))


class MainWindow(QMainWindow):
    """主窗口类"""
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        self.setWindowTitle("自动申购助手")
        self.setGeometry(100, 100, 800, 600) # 设置窗口初始大小

        # 初始化配置和模拟器对象
        self.config = Config()
        self.simulator = SimulatorController() # 使用 SimulatorController
        self.adb_path = self.simulator.adb_path # 从 SimulatorController 获取 adb_path
        self.adb_worker = None # 初始化adb工作线程为空

        # --- 修改顺序：先初始化UI，再初始化数据库 ---
        # 创建UI界面 (移到前面)
        self.init_ui()

        # 初始化数据库和表 (移到后面)
        self.init_database()
        # --- 顺序修改结束 ---

        # 启动时检查模拟器连接状态
        self.check_emulator_status()

    def init_database(self):
        """初始化数据库连接和创建表"""
        try:
            # 确保 User 模型关联的数据库已初始化
            # Peewee 通常在模型定义时处理数据库连接
            User.create_table(safe=True) # safe=True 表示如果表已存在则不会报错
            self.log_message("数据库初始化成功")
        # except peewee.PeeweeException as db_err: # 捕获更具体的异常
        except Exception as e: # 保留通用异常捕获作为后备
            self.log_message(f"数据库初始化失败: {e}")
            QMessageBox.critical(self, "数据库错误", f"无法初始化数据库: {str(e)}")

    def init_ui(self):
        """初始化用户界面"""
        # --- 菜单栏 ---
        menu_bar = self.menuBar()
        settings_menu = menu_bar.addMenu("设置")

        manage_accounts_action = settings_menu.addAction("账号管理")
        manage_accounts_action.triggered.connect(self.open_account_dialog)

        configure_action = settings_menu.addAction("配置")
        configure_action.triggered.connect(self.open_settings_dialog)

        # --- 主布局 ---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # --- 状态标签 ---
        self.status_label = QLabel("状态：初始化中...") # 初始状态可以更明确
        main_layout.addWidget(self.status_label)

        # --- 按钮区域 ---
        button_layout = QHBoxLayout()
        self.connect_btn = QPushButton("连接模拟器")
        self.connect_btn.clicked.connect(self.connect_emulator)
        button_layout.addWidget(self.connect_btn)

        self.subscribe_btn = QPushButton("开始自动申购")
        self.subscribe_btn.clicked.connect(self.start_subscription)
        self.subscribe_btn.setEnabled(False) # 初始状态不可用
        button_layout.addWidget(self.subscribe_btn)

        main_layout.addLayout(button_layout)

        # --- 日志区域 ---
        self.log_output = QTextEdit() # 初始化 self.log_output
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output)

    def log_message(self, message):
        """在日志区域显示消息"""
        # 确保 self.log_output 存在
        if hasattr(self, 'log_output'):
            self.log_output.append(message)
            QApplication.processEvents() # 处理事件，确保界面更新
        else:
            print(f"日志控件未初始化，无法记录: {message}") # 添加备用打印

    def update_status_label(self, message):
        """
        更新状态栏标签的文本。

        Args:
            message (str): 要显示在状态栏上的消息。
        """
        # 确保 self.status_label 存在
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"状态：{message}")
            QApplication.processEvents() # 确保界面更新
        else:
            print(f"状态标签未初始化，无法更新: {message}") # 添加备用打印

    def check_emulator_status(self):
        """检查模拟器连接状态"""
        # 使用 self.simulator 的方法检查状态
        self.update_status_label("正在检查连接...") # 现在这个方法存在了
        self.log_message("正在检查模拟器连接状态...")
        # 启动后台线程执行检查
        self.run_adb_command('check') # AdbWorker 需要能处理 'check' 命令

    def connect_emulator(self):
        """连接到模拟器"""
        # 这里的连接逻辑可能需要调整，取决于 AdbWorker 和 SimulatorController 的设计
        if not self.adb_path:
            QMessageBox.warning(self, "配置错误", "请先在设置中配置夜神模拟器bin目录。")
            return

        self.update_status_label("正在连接...")
        self.log_message("尝试连接模拟器...")
        self.connect_btn.setEnabled(False) # 连接期间禁用按钮
        # 启动后台线程执行连接
        self.run_adb_command('connect') # AdbWorker 需要能处理 'connect' 命令

    def start_subscription(self):
        """开始执行自动申购流程"""
        if not self.adb_path:
            QMessageBox.warning(self, "配置错误", "请先在设置中配置夜神模拟器bin目录。")
            return

        # 获取所有账号信息
        try:
            users = list(User.select()) # 获取所有用户并转为列表
            if not users:
                QMessageBox.warning(self, "无账号", "请先在账号管理中添加至少一个账号。")
                return

            self.log_message(f"准备为 {len(users)} 个账号执行自动申购流程...")
            self.subscribe_btn.setEnabled(False) # 执行期间禁用按钮

            # --- 实现多账号循环 ---
            self.current_user_index = 0
            self.users_to_process = users
            self.process_next_user() # 开始处理第一个用户

        # except peewee.PeeweeException as db_err: # 捕获具体数据库异常
        except Exception as e:
            self.log_message(f"获取账号信息失败: {e}")
            QMessageBox.critical(self, "数据库错误", f"无法获取账号信息: {str(e)}")
            self.subscribe_btn.setEnabled(True) # 出错时恢复按钮

    # --- 多账号处理辅助函数 ---
    def process_next_user(self):
        """处理下一个用户的申购任务"""
        if self.current_user_index < len(self.users_to_process):
            user = self.users_to_process[self.current_user_index]
            self.log_message(f"开始为账号 {user.account} ({user.user_name or 'N/A'}) 执行申购...")

            # --- 使用 get_coordinate 方法获取坐标 ---
            select_x = self.config.get_coordinate('select_x', 201) # 提供默认值以防万一
            select_y = self.config.get_coordinate('select_y', 785)
            subscribe_x = self.config.get_coordinate('subscribe_x', 332)
            subscribe_y = self.config.get_coordinate('subscribe_y', 783)
            confirm_x = self.config.get_coordinate('confirm_x', 197)
            confirm_y = self.config.get_coordinate('confirm_y', 916)
            # --- 坐标获取修改结束 ---

            params = {
                'account': user.account,
                'password': user.password,
                'user_name': user.user_name,
                # 使用获取到的坐标值
                'select_x': select_x,
                'select_y': select_y,
                'subscribe_x': subscribe_x,
                'subscribe_y': subscribe_y,
                'confirm_x': confirm_x,
                'confirm_y': confirm_y,
                # 传递券商包名给 AdbWorker
                'broker_package': self.config.get_broker_package_name() # 直接获取包名
            }
            # 确保 AdbWorker 能接收并处理 'subscribe' 命令及这些参数
            self.run_adb_command('subscribe', params)
        else:
            self.log_message("所有账号申购流程执行完毕。")
            self.subscribe_btn.setEnabled(True) # 所有任务完成后恢复按钮

    def run_adb_command(self, cmd_type, params=None):
        """启动后台线程执行ADB命令"""
        if self.adb_worker and self.adb_worker.isRunning():
            self.log_message("请等待当前操作完成...")
            # 可以考虑禁用按钮，防止重复点击
            return

        if not self.adb_path:
             self.log_message("错误：ADB路径未设置。请在设置中配置。")
             # 根据命令类型决定是否恢复按钮状态
             if cmd_type in ['connect', 'check']:
                 self.connect_btn.setEnabled(True)
             elif cmd_type == 'subscribe':
                 # 如果是多账号模式启动失败，需要恢复按钮
                 if self.current_user_index == 0:
                     self.subscribe_btn.setEnabled(True)
             return

        # 传递 adb_path, cmd_type, params 给 AdbWorker
        self.adb_worker = AdbWorker(self.adb_path, cmd_type, params)
        self.adb_worker.update_signal.connect(self.log_message)
        self.adb_worker.finished_signal.connect(self.on_adb_finished)
        self.adb_worker.start()

    def on_adb_finished(self, success, message):
        """ADB命令执行完成后的处理"""
        self.log_message(f"操作完成 (成功: {success}): {message}")

        current_cmd_type = self.adb_worker.cmd_type if self.adb_worker else None
        self.adb_worker = None # 清理工作线程引用

        if current_cmd_type == 'connect':
            self.connect_btn.setEnabled(True) # 恢复连接按钮
            if success:
                self.update_status_label("已连接")
                self.subscribe_btn.setEnabled(True) # 连接成功后启用申购按钮
            else:
                self.update_status_label("连接失败")
                self.subscribe_btn.setEnabled(False)
        elif current_cmd_type == 'check':
            self.connect_btn.setEnabled(True) # 检查完成后恢复连接按钮
            if success:
                self.update_status_label("已连接")
                self.subscribe_btn.setEnabled(True)
            else:
                self.update_status_label("未连接")
                self.subscribe_btn.setEnabled(False)
        elif current_cmd_type == 'subscribe':
             # 处理下一个账号
             if success:
                 self.log_message(f"账号 {self.users_to_process[self.current_user_index].account} 申购操作成功。")
             else:
                 # 记录失败信息，但继续处理下一个账号
                 self.log_message(f"账号 {self.users_to_process[self.current_user_index].account} 申购操作失败: {message}")

             self.current_user_index += 1
             # 稍微延迟一下再处理下一个，给模拟器反应时间
             QTimer.singleShot(1000, self.process_next_user) # 延迟1秒

    def open_account_dialog(self):
        """打开账号管理对话框"""
        # AccountDialog 现在是从 ui.account_dialog 导入的
        dialog = AccountDialog(self)
        dialog.exec() # 使用 exec() 使其成为模态对话框

    def open_settings_dialog(self):
        """打开设置对话框"""
        current_path = self.config.get_simulator_path()
        # 从 Config 获取当前包名，如果为空则使用默认值 "com.hexin.plat.android"
        current_package = self.config.get_broker_package_name(default="com.hexin.plat.android")

        # SettingsDialog 现在是从 ui.settings_dialog 导入的
        dialog = SettingsDialog(self, path=current_path, broker_package=current_package)
        if dialog.exec(): # 如果用户点击OK
            new_path, new_package = dialog.get_settings()
            # 检查路径或包名是否真的改变了
            path_changed = new_path != current_path
            package_changed = new_package != current_package

            if path_changed or package_changed:
                if path_changed:
                    # 使用 set_simulator_path，它内部会调用 save_config
                    if self.config.set_simulator_path(new_path):
                        # 更新 simulator 实例和 adb_path
                        self.simulator = SimulatorController() # 重新初始化以读取新路径
                        self.adb_path = self.simulator.adb_path
                        self.log_message("模拟器路径已更新并保存。")
                    else:
                        self.log_message("设置模拟器路径失败，请检查路径是否有效。")
                if package_changed:
                    # 使用 set_broker_package_name，它内部会调用 save_config
                    self.config.set_broker_package_name(new_package)
                    self.log_message("券商APP包名已更新并保存。")

                # 不再需要单独调用 self.config.save_config()，因为 setter 内部会调用
                # self.log_message("设置已保存。") # 可以移除或修改日志信息

                # 如果路径改变，重新检查连接状态
                if path_changed:
                    self.check_emulator_status()
            else:
                self.log_message("设置未更改。")
        else:
            self.log_message("设置操作已取消。")

    def closeEvent(self, event):
        """关闭窗口前的处理"""
        if self.adb_worker and self.adb_worker.isRunning():
            reply = QMessageBox.question(self, '确认退出',
                                       "当前有操作正在进行中，确定要强制退出吗？",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
# --- 主程序入口 ---
if __name__ == '__main__':
    print("脚本开始执行...") # 添加启动打印语句
    try:
        app = QApplication(sys.argv)
        print("QApplication 已创建")

        main_win = MainWindow()
        print("MainWindow 实例已创建")

        main_win.show()
        print("MainWindow.show() 已调用")

        print("启动事件循环 app.exec()...")
        exit_code = app.exec()
        print(f"事件循环结束，退出码: {exit_code}")
        sys.exit(exit_code)

    except Exception as e:
        print("\n--- 程序启动时发生未捕获的异常 ---")
        import traceback
        traceback.print_exc() # 打印详细的错误堆栈信息
        print("------------------------------------\n")
        input("按 Enter 键退出...") # 暂停窗口，以便查看错误信息
        sys.exit(1) # 以错误码退出