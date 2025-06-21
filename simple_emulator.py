import os
import subprocess
import time
import json
from loguru import logger

try:
    import uiautomator2 as u2
except ImportError:
    logger.error("uiautomator2 未安装")
    u2 = None

class SimpleEmulator:
    """简化的模拟器控制类，专注于保持连接状态"""
    
    def __init__(self, path):
        self.path = path
        self.adb_path = os.path.join(path, "adb.exe")
        self.device = None
        self.connected_port = None
        self.is_connected = False
        
        # 从配置文件读取模拟器路径
        try:
            if os.path.exists('app_config.json'):
                with open('app_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.simulator_exe_path = config.get('simulator_exe_path')
        except Exception as e:
            logger.error("读取配置文件失败: {}", str(e))
            self.simulator_exe_path = None
    
    def run_command(self, command):
        """执行shell命令"""
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
    
    def check_adb_connection(self):
        """检查并建立ADB连接"""
        try:
            logger.info("检查ADB连接状态...")
            
            if not os.path.exists(self.adb_path):
                logger.error("ADB路径不存在: {}", self.adb_path)
                return False
            
            # 检查夜神模拟器是否运行
            if not self.is_nox_running():
                logger.info("夜神模拟器未运行，尝试启动...")
                if not self.start_nox_emulator():
                    return False
            
            # 尝试连接到常用端口
            ports = ['62001', '62025', '62026', '5555']
            for port in ports:
                if self.try_connect_port(port):
                    self.connected_port = port
                    logger.info("成功连接到端口: {}", port)
                    return True
            
            logger.error("无法连接到任何端口")
            return False
            
        except Exception as e:
            logger.error("检查ADB连接失败: {}", str(e))
            return False
    
    def try_connect_port(self, port):
        """尝试连接到指定端口"""
        try:
            # 断开可能的旧连接
            self.run_command(f'"{self.adb_path}" disconnect 127.0.0.1:{port}')
            time.sleep(0.5)
            
            # 连接
            result = self.run_command(f'"{self.adb_path}" connect 127.0.0.1:{port}')
            if "connected" in result or "already connected" in result:
                time.sleep(2)
                
                # 验证连接状态
                devices = self.run_command(f'"{self.adb_path}" devices')
                if f"127.0.0.1:{port}" in devices and "device" in devices and "offline" not in devices:
                    return True
            
            return False
        except Exception as e:
            logger.error("连接端口 {} 失败: {}", port, str(e))
            return False
    
    def is_nox_running(self):
        """检查夜神模拟器是否运行"""
        try:
            result = subprocess.run(
                'tasklist /FI "IMAGENAME eq Nox.exe"',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='ignore'
            )
            return "Nox.exe" in result.stdout
        except Exception:
            return False
    
    def start_nox_emulator(self):
        """启动夜神模拟器"""
        try:
            nox_locations = []
            
            if self.simulator_exe_path and os.path.exists(self.simulator_exe_path):
                nox_locations.append(self.simulator_exe_path)
            
            nox_locations.extend([
                os.path.join(os.path.dirname(self.path), "Nox.exe"),
                "D:\\Program Files\\Nox\\bin\\Nox.exe",
                "C:\\Program Files\\Nox\\bin\\Nox.exe",
                "C:\\Program Files (x86)\\Nox\\bin\\Nox.exe"
            ])
            
            nox_path = None
            for path in nox_locations:
                if os.path.exists(path):
                    nox_path = path
                    break
            
            if not nox_path:
                logger.error("未找到夜神模拟器")
                return False
            
            logger.info("启动夜神模拟器: {}", nox_path)
            subprocess.Popen([nox_path], shell=True)
            
            # 等待启动
            for i in range(30):  # 最多等待30秒
                time.sleep(2)
                if self.is_nox_running():
                    # 再等待几秒让模拟器完全启动
                    time.sleep(5)
                    return True
            
            logger.error("模拟器启动超时")
            return False
            
        except Exception as e:
            logger.error("启动模拟器失败: {}", str(e))
            return False
    
    def connect_device(self):
        """连接到uiautomator2设备"""
        if not u2:
            logger.error("uiautomator2 未安装")
            return False
        
        if not self.connected_port:
            logger.error("没有可用的ADB连接")
            return False
        
        try:
            logger.info("连接到uiautomator2设备...")
            self.device = u2.connect(f"127.0.0.1:{self.connected_port}")
            
            # 简单验证
            try:
                info = self.device.device_info
                if info:
                    self.is_connected = True
                    logger.info("uiautomator2连接成功")
                    return True
            except Exception as e:
                logger.warning("设备验证失败: {}", str(e))
            
            self.device = None
            self.is_connected = False
            return False
            
        except Exception as e:
            logger.error("连接uiautomator2失败: {}", str(e))
            self.device = None
            self.is_connected = False
            return False
    
    def ensure_connection(self):
        """确保连接可用"""
        if self.is_connected and self.device:
            try:
                # 简单测试连接是否还有效
                self.device.device_info
                return True
            except Exception:
                logger.warning("连接已断开，重新连接...")
                self.is_connected = False
                self.device = None
        
        # 重新建立连接
        if self.check_adb_connection():
            return self.connect_device()
        
        return False
    
    def wait_for_element(self, selector, timeout=10, description="元素"):
        """等待元素出现"""
        logger.info("等待{}出现...", description)
        for i in range(timeout):
            try:
                if selector.exists:
                    logger.info("{}已出现", description)
                    return True
                time.sleep(1)
            except Exception as e:
                logger.warning("检查{}时出错: {}", description, str(e))
                time.sleep(1)

        logger.error("等待{}秒后{}仍未出现", timeout, description)
        return False

    def handle_popups(self, max_attempts=10):
        """处理各种弹窗"""
        logger.info("处理启动弹窗...")
        popup_selectors = [
            ("close_button", self.device(resourceId="com.hexin.plat.android:id/close_button")),
            ("关闭", self.device(text="关闭")),
            ("取消", self.device(text="取消")),
            ("跳过", self.device(text="跳过")),
            ("稍后", self.device(text="稍后")),
            ("知道了", self.device(text="知道了")),
        ]

        for i in range(max_attempts):
            popup_found = False
            for name, selector in popup_selectors:
                try:
                    if selector.exists:
                        logger.info("关闭弹窗: {}", name)
                        selector.click()
                        time.sleep(1)
                        popup_found = True
                        break
                except Exception as e:
                    logger.warning("处理弹窗{}时出错: {}", name, str(e))

            if not popup_found:
                break

        logger.info("弹窗处理完成")

    def disconnect(self):
        """断开连接"""
        try:
            if self.device:
                self.device = None
            self.is_connected = False
            logger.info("连接已断开")
        except Exception as e:
            logger.error("断开连接失败: {}", str(e))
    
    def mask_string(self, input_str):
        """将账号中间设置为*号"""
        if len(input_str) < 8:
            return "字符串长度太短"
        first_4, last_4 = input_str[:4], input_str[-4:]
        middle_mask = "*" * (len(input_str) - 8)
        return f"{first_4}{middle_mask}{last_4}"

    def num_to_coordinate(self, number):
        """数字转化为坐标"""
        positions = {
            '1': (66, 723), '2': (205, 721), '3': (328, 720),
            '4': (64, 792), '5': (201, 785), '6': (332, 783),
            '7': (66, 853), '8': (201, 846), '9': (326, 852),
            '0': (197, 916)
        }
        return positions.get(number, (0, 0))

    def subscription(self, user):
        """执行申购操作"""
        if not self.ensure_connection():
            logger.error("无法建立设备连接")
            return False

        try:
            account = user.get('account') if isinstance(user, dict) else getattr(user, 'account', '')
            password = user.get('password') if isinstance(user, dict) else getattr(user, 'password', '')

            if not account or not password:
                logger.error("账号或密码为空")
                return False

            logger.info("开始为账号 {} 执行申购操作", account)

            # 检查同花顺app是否已安装
            broker_package = 'com.hexin.plat.android'
            if not self.device.app_info(broker_package):
                logger.error("{} 未安装", broker_package)
                return False

            # 将资金账号中间变为*号
            account_with_fix = self.mask_string(account)

            # 启动同花顺app
            logger.info("启动同花顺app")
            self.device.app_start(broker_package, wait=True)

            # 等待APP完全启动并验证
            logger.info("等待APP完全加载...")
            app_loaded = False
            for i in range(15):  # 最多等待15秒
                time.sleep(1)
                try:
                    current_app = self.device.app_current()
                    if current_app.get('package') == broker_package:
                        app_loaded = True
                        break
                except Exception:
                    continue

            if not app_loaded:
                logger.error("APP启动超时或失败")
                return False

            logger.info("同花顺app已成功打开")

            # 处理启动弹窗
            self.handle_popups()

            # 查找并点击交易按钮
            trade_selectors = [
                ("文本", self.device(text="交易")),
                ("xpath", self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]')),
                ("描述", self.device(description="交易")),
                ("资源ID", self.device(resourceId="com.hexin.plat.android:id/tab_trade")),
            ]

            trade_button_found = False
            for name, selector in trade_selectors:
                if self.wait_for_element(selector, timeout=20, description=f"交易按钮({name})"):
                    logger.info("点击交易按钮({})", name)
                    selector.click()
                    trade_button_found = True
                    break

            if not trade_button_found:
                logger.error("未找到交易按钮")
                return False

            # 等待交易界面加载
            logger.info("等待交易界面加载...")
            time.sleep(3)

            # 等待账号列表加载
            account_selector = self.device(resourceId="com.hexin.plat.android:id/txt_account_value")
            if not self.wait_for_element(account_selector, timeout=10, description="账号列表"):
                return False

            account_count = account_selector.count
            logger.info("找到 {} 个账号", account_count)

            account_found = False
            for i in range(account_count):
                account_item = self.device(resourceId="com.hexin.plat.android:id/txt_account_value", instance=i)
                if not account_item.exists:
                    continue

                element_text = account_item.get_text().strip()
                logger.info("检查账号 {}: {}", i+1, element_text)

                if account_with_fix != element_text:
                    continue

                account_found = True
                logger.info("找到匹配账号【{}】,准备点击", account)
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

                # 输入密码
                logger.info("开始输入密码")
                for key in password:
                    x, y = self.num_to_coordinate(key)
                    logger.info("点击坐标: ({}, {})", x, y)
                    self.device.click(x, y)
                    time.sleep(0.2)

                # 点击登录
                login_btn = self.device(resourceId="com.hexin.plat.android:id/weituo_btn_login")
                if login_btn.exists:
                    login_btn.click()
                    logger.info("点击登录按钮成功")
                    time.sleep(3)
                else:
                    logger.error("找不到登录按钮")
                    return False

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
            logger.error("申购操作失败: {}", str(e))
            return False
        finally:
            try:
                # 确保关闭app
                broker_package = 'com.hexin.plat.android'
                self.device.app_stop(broker_package)
                logger.info("已关闭同花顺app")
            except Exception as e:
                logger.error("关闭同花顺app失败: {}", str(e))
