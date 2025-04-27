import random
import subprocess
import time
import datetime
import re
import os
import json

from loguru import logger

# 导入必要的库
try:
    import uiautomator2 as u2
    from entity.user_subscription_record import UserSubscriptionRecord
except ImportError:
    logger.warning("未能导入uiautomator2或实体类，可能会影响部分功能")
    # 创建一个空的UserSubscriptionRecord类作为替代
    class UserSubscriptionRecord:
        @staticmethod
        def get_subscription_record_by_subscription_code(*args, **kwargs):
            return None
        
        @staticmethod
        def create_user_subscription_record(*args, **kwargs):
            pass


class EmulatorImproved:
    # 初始化模拟器
    def __init__(self, path):
        logger.info("设置模拟器地址: {}", path)
        self.__path = path
        self.device = None  # 保证属性总是存在
        self.emulator_name = "Nox"  # 默认模拟器名称
        self.simulator_exe_path = None
        self.connected_port = None  # 记录成功连接的端口
        
        # 尝试读取配置文件以获取更准确的模拟器路径
        try:
            if os.path.exists('app_config.json'):
                with open('app_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'simulator_exe_path' in config:
                        self.simulator_exe_path = config['simulator_exe_path']
                        logger.info("从配置文件加载模拟器路径: {}", self.simulator_exe_path)
        except Exception as e:
            logger.error("读取配置文件失败: {}", str(e))

    # with 触发初始化模拟器
    def __enter__(self):
        # 确保模拟器已经启动并通过ADB连接
        logger.info("尝试通过ADB连接模拟器")
        if not self.check_adb_connection():
            logger.error("无法通过ADB连接模拟器")
            return self
        
        # 如果已有端口连接成功，使用该端口
        port = self.connected_port or "62001"
        
        # 初始化uiautomator2
        try:
            completed_process = subprocess.run(
                'python -m uiautomator2 init', 
                shell=True, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, 
                encoding='utf-8', 
                errors='ignore'
            )
            logger.info("执行uiautomator2初始化返回值=【{}】,正常输出=【{}】,错误=【{}】", 
                        completed_process.returncode,
                        completed_process.stdout,
                        completed_process.stderr)
            
            # 连接设备
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info("开始连接模拟器(尝试 {}/{}) 地址: 127.0.0.1:{}".format(attempt+1, max_retries, port))
                    self.device = u2.connect(f"127.0.0.1:{port}")
                    logger.info("连接模拟器成功")
                    break
                except Exception as e:
                    logger.error("连接模拟器失败[{0}]", e)
                    if attempt == max_retries - 1:
                        self.device = None
                    time.sleep(2)
        except Exception as e:
            logger.error("初始化uiautomator2失败: {}", str(e))
            
        return self

    # 自动销毁触发
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.device:
            logger.info("执行代码结束,准备关闭模拟器")
            # 执行关闭模拟器
            try:
                subprocess.run([self.__path, "quit", self.emulator_name])
            except Exception as e:
                logger.error("关闭模拟器失败: {}", str(e))

    # 将账号中间设置为*号
    @staticmethod
    def mask_string(input_str):
        if len(input_str) < 8:
            return "字符串长度太短"
        first_4, last_4 = input_str[:4], input_str[-4:]
        middle_mask = "*" * (len(input_str) - 8)
        return f"{first_4}{middle_mask}{last_4}"

    # 数字转化为坐标
    @staticmethod
    def num_to_coordinate(number):
        positions = {
            '1': (66, 723), '2': (205, 721), '3': (328, 720),
            '4': (64, 792), '5': (201, 785), '6': (332, 783),
            '7': (66, 853), '8': (201, 846), '9': (326, 852),
            '0': (197, 916)
        }
        return positions.get(number, (0, 0))  # 如果找不到对应数字，返回0,0

    def check_adb_connection(self):
        """检查ADB连接状态，如果未连接则尝试启动模拟器"""
        try:
            logger.info("===== 开始检查ADB连接状态 =====")
            
            # 夜神模拟器常用的端口
            nox_ports = ['62001', '62025', '62026', '5555', '62028']
            
            # 查找有效的ADB路径
            adb_path = self.find_adb_executable()
            if not adb_path:
                logger.error("无法找到ADB可执行文件，请确保安装了ADB工具")
                return False
            
            logger.info("使用ADB路径: {}", adb_path)
            
            # 重启ADB服务器
            logger.info("正在重启ADB服务器...")
            self.run_command(f'"{adb_path}" kill-server')
            time.sleep(2)  # 等待服务器关闭
            
            self.run_command(f'"{adb_path}" start-server')
            time.sleep(2)  # 等待服务器启动
            
            # 获取设备列表，检查是否有设备连接
            devices_output = self.run_command(f'"{adb_path}" devices')
            logger.info("设备列表: {}", devices_output)
            
            # 检查已知端口是否连接成功
            for port in nox_ports:
                device_id = f"127.0.0.1:{port}"
                if device_id in devices_output and "device" in devices_output:
                    logger.info(f"已连接到设备: {device_id}")
                    self.connected_port = port
                    return True
            
            # 没有已连接的设备，尝试启动模拟器并连接
            logger.info("未检测到已连接的设备，尝试启动模拟器...")
            
            # 检查模拟器是否已运行
            is_nox_running = self.is_nox_running()
            
            # 如果模拟器未运行，尝试启动它
            if not is_nox_running:
                if not self.start_nox_emulator():
                    logger.error("启动模拟器失败")
                    return False
            
            # 模拟器已启动或正在运行，尝试连接到所有可能的端口
            for port in nox_ports:
                logger.info(f"尝试连接到端口 {port}...")
                connect_output = self.run_command(f'"{adb_path}" connect 127.0.0.1:{port}')
                logger.info(f"连接到端口 {port} 结果: {connect_output}")
                
                if "connected to" in connect_output or "already connected" in connect_output:
                    logger.info(f"成功连接到端口 {port}")
                    self.connected_port = port
                    return True
            
            # 如果所有连接尝试都失败，返回失败
            logger.error("模拟器连接失败: 无法连接到任何已知端口")
            return False
                
        except Exception as e:
            logger.error("检查ADB连接时发生错误: {}", str(e))
            return False
    
    def find_adb_executable(self):
        """查找ADB可执行文件的位置"""
        # 如果self.__path是有效目录，尝试从该目录查找
        if os.path.isdir(self.__path):
            adb_path = os.path.join(self.__path, "adb.exe")
            if os.path.exists(adb_path):
                return adb_path
        
        # 如果self.__path是文件，尝试从其所在目录查找
        if os.path.isfile(self.__path):
            adb_path = os.path.join(os.path.dirname(self.__path), "adb.exe")
            if os.path.exists(adb_path):
                return adb_path
        
        # 尝试从常见位置查找
        adb_locations = [
            "adb.exe",  # 当前目录
            "D:\\rio.liu\\Nox\\bin\\adb.exe",  # 根据app_config.json提供的路径
            "D:\\Program Files\\Nox\\bin\\adb.exe",
            "C:\\Program Files\\Nox\\bin\\adb.exe",
            "C:\\Program Files (x86)\\Nox\\bin\\adb.exe",
            os.path.join(os.environ.get('ANDROID_HOME', ''), 'platform-tools', 'adb.exe')
        ]
        
        for path in adb_locations:
            if os.path.exists(path):
                return path
        
        return None
    
    def is_nox_running(self):
        """检查Nox模拟器进程是否在运行"""
        try:
            process_check = subprocess.run(
                'tasklist /FI "IMAGENAME eq Nox.exe"',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='ignore'
            )
            if "Nox.exe" in process_check.stdout:
                logger.info("夜神模拟器进程已运行")
                return True
            return False
        except Exception as e:
            logger.error("检查模拟器进程失败: {}", str(e))
            return False
    
    def start_nox_emulator(self):
        """尝试启动夜神模拟器"""
        # 尝试从多个可能的位置查找Nox.exe
        nox_locations = []
        
        # 优先使用从配置文件读取的路径
        if self.simulator_exe_path and os.path.exists(self.simulator_exe_path):
            nox_locations.append(self.simulator_exe_path)
        
        # 添加其他可能的位置
        nox_locations.extend([
            os.path.join(os.path.dirname(self.__path), "Nox.exe"),
            "D:\\rio.liu\\Nox\\bin\\Nox.exe",  # 根据app_config.json提供的路径
            "D:\\Program Files\\Nox\\bin\\Nox.exe",
            "C:\\Program Files\\Nox\\bin\\Nox.exe",
            "C:\\Program Files (x86)\\Nox\\bin\\Nox.exe"
        ])
        
        # 查找并启动模拟器
        nox_path = None
        for path in nox_locations:
            if os.path.exists(path):
                nox_path = path
                logger.info("找到夜神模拟器: {}", nox_path)
                break
        
        if nox_path:
            try:
                logger.info("正在启动夜神模拟器...")
                # 使用subprocess.Popen确保异步启动，不阻塞当前进程
                subprocess.Popen([nox_path], shell=True)
                logger.info("等待模拟器启动 (60秒)...")
                # 增加启动等待时间，确保模拟器完全启动
                time.sleep(60)
                return True
            except Exception as start_error:
                logger.error("启动模拟器时出错: {}", str(start_error))
                return False
        else:
            logger.error("未找到夜神模拟器可执行文件")
            return False
    
    def run_command(self, command):
        """执行shell命令并返回输出"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='ignore'
            )
            return result.stdout.strip()
        except Exception as e:
            logger.error("执行命令失败 ({}): {}", command, str(e))
            return ""
    
    def subscription(self, user):
        if not self.device:
            logger.error("模拟器未连接，无法进行申购")
            return False
        
        try:
            # 获取账号信息，支持字典或对象
            if isinstance(user, dict):
                account = user.get('account', '')
                password = user.get('password', '')
            else:
                account = getattr(user, 'account', '')
                password = getattr(user, 'password', '')
                
            if not account or not password:
                logger.error("账号或密码为空")
                return False
                
            logger.info("开始执行自动申购...")
            logger.info(f"为账号 {account} 执行申购操作")
            
            # 尝试建立稳定的uiautomator2连接
            try:
                # 确保设备连接可用
                if not self.device or not hasattr(self.device, 'app_start'):
                    logger.info("重新连接到设备...")
                    port = self.connected_port or "62001"
                    adb_path = self.find_adb_executable()
                    # 确保ADB服务器正在运行
                    if adb_path:
                        self.run_command(f'"{adb_path}" connect 127.0.0.1:{port}')
                    time.sleep(1)
                    self.device = u2.connect(f"127.0.0.1:{port}")
                    time.sleep(2)  # 等待连接稳定

                # 确保旧的uiautomator进程被关闭
                try:
                    self.run_command(f'"{adb_path}" shell "ps | grep uiautomator | xargs kill -9"')
                    time.sleep(1)
                except Exception:
                    pass
                
                # 检查目标应用是否已安装
                logger.info("检查同花顺app是否已安装")
                broker_package = 'com.hexin.plat.android'
                if not self.device.app_info(broker_package):
                    logger.error(f"{broker_package} 未安装")
                    return False

                # 将资金账号中间变为*号
                account_with_fix = self.mask_string(account)
                
                # 尝试通过多种方式启动app
                logger.info("准备打开同花顺app")
                try:
                    # 方法1: 使用u2的app_start
                    self.device.app_start(broker_package, wait=True)
                except Exception as e1:
                    logger.warning(f"使用app_start启动失败: {e1}")
                    try:
                        # 方法2: 使用shell命令启动
                        adb_path = self.find_adb_executable()
                        if adb_path:
                            start_cmd = f'"{adb_path}" shell am start -n {broker_package}/.InitPluginActivity'
                            self.run_command(start_cmd)
                    except Exception as e2:
                        logger.error(f"使用shell命令启动也失败: {e2}")
                        return False
                
                # 等待启动完成
                time.sleep(3)
                
                # 尝试建立会话
                try:
                    # 确认app是否成功启动
                    if not self.device.app_current()['package'] == broker_package:
                        logger.info("重试建立会话...")
                        self.device.session(broker_package, attach=True)
                except Exception as e:
                    logger.warning(f"建立会话失败: {e}")
                
                # 判断程序是否打开
                current_app = self.device.app_current()
                if current_app.get('package') != broker_package:
                    logger.error(f"app打开失败，当前应用是: {current_app.get('package')}")
                    return False
                
                logger.info("同花顺app已成功打开")
                
                # 判断是否有弹窗
                try:
                    if self.device(resourceId="com.hexin.plat.android:id/close_button").exists:
                        logger.info("关闭弹窗")
                        self.device(resourceId="com.hexin.plat.android:id/close_button").click()
                except Exception as e:
                    logger.warning(f"处理弹窗失败: {e}")
                
                # 点击交易
                try:
                    if self.device(text="交易").exists:
                        logger.info("点击交易按钮")
                        self.device(text="交易").click()
                    elif self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').exists:
                        logger.info("通过xpath点击交易按钮")
                        self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').click()
                    else:
                        logger.error("找不到交易按钮")
                        return False
                    
                    # 等待交易界面加载
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"点击交易按钮失败: {e}")
                    return False
                
                # 遍历所有券商账号 - 修复版本2.11.0的API调用
                try:
                    # 查找账号元素
                    account_selector = self.device(resourceId="com.hexin.plat.android:id/txt_account_value")
                    if not account_selector.exists:
                        logger.error("找不到账号列表")
                        return False
                    
                    # 获取账号数量和文本
                    account_count = account_selector.count
                    logger.info(f"找到 {account_count} 个账号")
                    
                    # 遍历所有账号
                    account_found = False
                    for i in range(account_count):
                        # 每次重新获取元素，避免stale引用
                        account_item = self.device(resourceId="com.hexin.plat.android:id/txt_account_value", instance=i)
                        if not account_item.exists:
                            continue
                            
                        element_text = account_item.get_text().strip()
                        logger.info(f"检查账号 {i+1}: {element_text}")
                        
                        if account_with_fix != element_text:
                            continue
                            
                        account_found = True
                        logger.info(f"找到匹配账号【{account}】,准备点击")
                        account_item.click()
                        time.sleep(1)
                        
                        # 等待密码输入框出现
                        if not self.device(resourceId="com.hexin.plat.android:id/weituo_edit_trade_password").exists:
                            logger.error("密码框未出现")
                            return False
                        
                        # 点击密码框
                        logger.info("点击密码框")
                        self.device(resourceId="com.hexin.plat.android:id/weituo_edit_trade_password").click()
                        time.sleep(1)
                        
                        logger.info("开始输入密码")
                        # 输入密码
                        for key in password:
                            x, y = self.num_to_coordinate(key)
                            logger.info(f"点击坐标: ({x}, {y})")
                            self.device.click(x, y)
                            # 每一次停留100-300毫秒
                            time.sleep(random.uniform(0.1, 0.3))
                        logger.info("输入密码成功")
                        
                        # 点击登录
                        logger.info("准备点击登录按钮")
                        login_btn = self.device(resourceId="com.hexin.plat.android:id/weituo_btn_login")
                        if login_btn.exists:
                            login_btn.click()
                            logger.info("点击登录按钮成功")
                        else:
                            logger.error("找不到登录按钮")
                            return False
                        
                        # 等待登录完成
                        time.sleep(random.uniform(2, 3))
                        
                        # 处理可能的中签弹窗
                        if self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").exists:
                            logger.info("关闭中签弹窗")
                            self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").click()
                        
                        # 查找并点击申购按钮
                        if self.device(resourceId="com.hexin.plat.android:id/option_apply").exists:
                            logger.info("点击一键申购按钮")
                            self.device(resourceId="com.hexin.plat.android:id/option_apply").click()
                            logger.info("申购操作完成")
                            return True
                        else:
                            logger.error("找不到申购按钮")
                            return False
                    
                    if not account_found:
                        logger.error("没有找到匹配的账号")
                        return False
                except Exception as e:
                    logger.error(f"处理账号列表时出错: {e}")
                    return False
            
            except Exception as e:
                logger.error(f"在处理UI操作时出错: {e}")
                return False
                
        except Exception as e:
            logger.error(f"申购过程中出错: {e}")
            return False
        finally:
            try:
                # 确保关闭app
                broker_package = 'com.hexin.plat.android'
                try:
                    self.device.app_stop(broker_package)
                except Exception:
                    # 如果u2方法失败，尝试使用adb命令
                    adb_path = self.find_adb_executable()
                    if adb_path:
                        self.run_command(f'"{adb_path}" shell am force-stop {broker_package}')
                logger.info("已关闭同花顺app")
            except Exception as e:
                logger.error(f"关闭同花顺app失败: {e}")


# 测试代码，用于直接运行此文件测试功能
if __name__ == "__main__":
    import logging
    from loguru import logger
    
    # 设置日志输出
    logger.add("emulator_test.log", rotation="1 MB")
    logger.info("开始测试EmulatorImproved类")
    
    # 创建实例并测试连接
    emulator = EmulatorImproved("D:\\rio.liu\\Nox\\bin")
    connection_result = emulator.check_adb_connection()
    print(f"连接结果: {connection_result}")
    
    # 使用with语句测试上下文管理
    if connection_result:
        with emulator as em:
            if em.device:
                print("成功连接到模拟器!")
            else:
                print("连接失败")
    
    print("测试完成") 