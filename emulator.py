import random
import subprocess
import time
import uiautomator2 as u2
import datetime
import re
import os  # 添加这行导入语句

from loguru import logger

from entity.user_subscription_record import UserSubscriptionRecord


class Emulator:
    # 初始化模拟器
    def __init__(self, path):
        logger.info("设置模拟器地址")
        self.__path = path
        self.device = None  # 保证属性总是存在

    # with 触发初始化模拟器
    def __enter__(self):
        # 确保模拟器已经启动并通过ADB连接
        logger.info("尝试通过ADB连接模拟器")
        if not self.check_adb_connection():
            logger.error("无法通过ADB连接模拟器")
            return self
        
        # 初始化uiautomator2
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
                logger.info("开始连接模拟器(尝试 {}/{})".format(attempt+1, max_retries))
                self.device = u2.connect("127.0.0.1:62001")
                logger.info("连接模拟器成功")
                break
            except Exception as e:
                logger.error("连接模拟器失败[{0}]", e)
                if attempt == max_retries - 1:
                    self.device = None
                time.sleep(2)
        return self

    # 自动销毁触发
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.device:
            logger.info("执行代码结束,准备关闭模拟器")
            # 执行关闭模拟器
            subprocess.run([self.__path, "quit", self.emulator_name])

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
        x = 0
        y = 0
        if number == '1':
            # 66, 723
            x = 66
            y = 723
        elif number == '2':
            # 205, 721
            x = 205
            y = 721
        elif number == '3':
            # 328, 720
            x = 328
            y = 720
        elif number == '4':
            # 64, 792
            x = 64
            y = 792
        elif number == '5':
            # 201, 785
            x = 201
            y = 785
        elif number == '6':
            # (332, 783)
            x = 332
            y = 783
        elif number == '7':
            # 66, 853
            x = 66
            y = 853
        elif number == '8':
            # 201, 846)
            x = 201
            y = 846
        elif number == '9':
            # 326, 852
            x = 326
            y = 852
        elif number == '0':
            # 197, 916
            x = 197
            y = 916
        return x, y

    # 时间匹配 周一至周三 申购的新债: 次日(T+1)傍晚 ，周四 申购的新债: 周末， 周五 申购的新债:下周一傍晚
    @staticmethod
    def date_match(subscription_date_str):
        # 获取当前日期
        current_date = datetime.date.today()
        # 获取当前日期是周几（0表示周一，1表示周二，以此类推）
        current_weekday = current_date.weekday()
        # 计算目标日期
        if current_weekday == 0:  # 当前日期是周一
            # 获取上周五的日期
            target_date = current_date - datetime.timedelta(days=3)
        elif current_weekday in (1, 2, 3):  # 当前日期是周二到周四
            # 获取周一到周三的日期
            target_date = current_date - datetime.timedelta(days=1)
        elif current_weekday == 6:  # 当前日期是周日
            target_date = current_date - datetime.timedelta(days=3)  # 其他情况，保持当前日期不变
        else:
            target_date = current_date
        logger.info("获取到日期：{}", target_date)
        # 获取当前日期和时间
        current_datetime = datetime.datetime.now()
        # 从当前日期和时间中提取年份
        current_year = current_datetime.year
        # 解析给定日期为日期对象
        subscription_date = datetime.datetime.strptime("{0}-{1}".format(current_year, subscription_date_str),
                                                       "%Y-%m-%d").date()
        logger.info("解析构造日期:{}", subscription_date)
        # 比较当前日期和给定日期
        if target_date == subscription_date:
            return True
        else:
            return False

    # 是否中签
    def is_winning(self, user):
        if not self.device:
            logger.error("模拟器未连接，无法进行中签查询")
            return
        # 将资金账号中间变为*号
        account_with_fix = self.mask_string(user.account)
        # 直接通过包名打开app---同花顺
        logger.info("准备打开同花顺app")
        self.device.app_start('com.hexin.plat.android')
        # 判断程序是否打开
        if not self.device.session("com.hexin.plat.android", attach=True):
            logger.error("app打开失败")
            return
        # 判断是否有弹窗
        self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/close_button"]').click_exists(
            timeout=5)
        # 点击交易
        self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').click_exists()
        logger.info("点击交易按钮")
        pattern = r"（(\d+-\d+)）.*?：(\d+)，.*?：(\d+)"
        # 遍历所有券商账号
        for i, v in enumerate(
                self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/txt_account_value"]').all()):
            # 判断对应的账号是否
            if account_with_fix != v.text.strip():
                continue
            logger.info("找到匹配账号【{}】,准备点击密码框", user.account)
            v.click()
            # 等待密码出现
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_edit_trade_password"]').click_exists(
                timeout=5)
            logger.info("点击密码框成功")
            logger.info("开始输入密码")
            # 输入密码
            for key in user.password:
                x, y = self.num_to_coordinate(key)
                self.device.click(x, y)
                # 每一次停留100-300毫秒
                time.sleep(random.uniform(0, 0.2))
            logger.info("输入密码成功")
            logger.info("准备点击登录按钮")
            # 点击登录
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_btn_login"]').click_exists(
                timeout=5)
            logger.info("点击登录按钮成功")
            time.sleep(random.uniform(1, 2))
            # 这里有可能存在中签弹窗的情况
            close_button = self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").exists()
            if close_button:
                logger.info("当前账号已中签,出现中签弹窗")
                self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").click()
            logger.info("准备点击新股/新债申购")
            # 点击新股/新债申购
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/icon_container"]/android.widget.LinearLayout[1]/android.widget.RelativeLayout[1]').click_exists()
            logger.info("点击新股/新债申购成功")
            time.sleep(random.uniform(1, 2))
            # 点击查询
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/navi_buttonbar"]/android.widget.RelativeLayout[2]').click()
            time.sleep(random.uniform(1, 2))
            # 遍历所有申购新债数据
            while True:
                index = 1
                # 判断当前是否存在申购信息
                frist_layout = self.device.xpath(
                    '//*[@resource-id="com.hexin.plat.android:id/listview"]/android.widget.RelativeLayout[{0}]'.format(
                        index))
                if not frist_layout.exists:
                    break
                # 获取当前该条申购信息
                # 解析前一天的配号 配号（10-25） 起始配号：5839826227，配号数量：1000
                allocation_number_info = self.device(
                    resourceId="com.hexin.plat.android:id/content_third").get_text()
                # 获取申购代码
                subscription_code = self.device(
                    resourceId="com.hexin.plat.android:id/tvstock_code").get_text()
                # 判断当前数据是否已经解析过了
                user_subscription_record = UserSubscriptionRecord.get_subscription_record_by_subscription_code(
                    subscription_code, user)
                if user_subscription_record:
                    logger.info("申购信息已解析完毕")
                    break
                # 周一至周三 申购的新债: 次日(T+1)傍晚 ，周四 申购的新债: 周末， 周五 申购的新债:下周一傍晚
                # 将解析出来的数据去请求外部接口判断是否中签
                # 判断今天是周几,然后获取申购日期对比
                match = re.search(pattern, allocation_number_info)
                if match:
                    start_number = match.group(2)
                    UserSubscriptionRecord.create_user_subscription_record(user, subscription_code, start_number)
                x, y = frist_layout.center()
                index += 1
                second_layout = self.device.xpath(
                    '//*[@resource-id="com.hexin.plat.android:id/listview"]/android.widget.RelativeLayout[{0}]'.format(
                        index))
                if second_layout.exists:
                    x1, y1 = second_layout.center()
                    self.device.swipe(x1, y1, x, y)
        self.device.app_stop('com.hexin.plat.android')

    # 自动申购
    def subscription(self, user):
        if not self.device:
            logger.error("模拟器未连接，无法进行申购")
            return
        # 将资金账号中间变为*号
        account_with_fix = self.mask_string(user.account)
        # 直接通过包名打开app---同花顺
        logger.info("准备打开同花顺app")
        self.device.app_start('com.hexin.plat.android')
        # 判断程序是否打开
        if not self.device.session("com.hexin.plat.android", attach=True):
            logger.error("app打开失败")
            return
        # 判断是否有弹窗
        self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/close_button"]').click_exists(
            timeout=5)
        # 点击交易
        self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').click_exists()
        logger.info("点击交易按钮")
        # 遍历所有券商账号
        for i, v in enumerate(
                self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/txt_account_value"]').all()):
            # 判断对应的账号是否
            if account_with_fix != v.text.strip():
                continue
            logger.info("找到匹配账号【{}】,准备点击密码框", user.account)
            v.click()
            # 等待密码出现
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_edit_trade_password"]').click_exists(
                timeout=5)
            logger.info("点击密码框成功")
            logger.info("开始输入密码")
            # 输入密码
            for key in user.password:
                x, y = self.num_to_coordinate(key)
                self.device.click(x, y)
                # 每一次停留100-300毫秒
                time.sleep(random.uniform(0, 0.2))
            logger.info("输入密码成功")
            logger.info("准备点击登录按钮")
            # 点击登录
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_btn_login"]').click_exists(
                timeout=5)
            logger.info("点击登录按钮成功")
            time.sleep(random.uniform(2, 3))
            # 这里有可能存在中签弹窗的情况
            self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").click_exists(timeout=3)
            # 同花顺有弹窗可以一键申购新债,直接申购
            self.device(resourceId="com.hexin.plat.android:id/option_apply").click_exists(timeout=3)
        self.device.app_stop('com.hexin.plat.android')

    # 增加ADB连接检查
    def check_adb_connection(self):
        max_retries = 5
        for attempt in range(max_retries):
            try:
                adb_path = os.path.join(os.path.dirname(self.__path), "adb.exe")
                result = subprocess.run(
                    [adb_path, "connect", "127.0.0.1:62001"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if "connected" in result.stdout:
                    logger.info("ADB连接成功")
                    return True
                logger.warning(f"ADB连接失败，尝试 {attempt+1}/{max_retries}")
                time.sleep(3)
            except Exception as e:
                logger.error(f"ADB连接异常: {str(e)}")
                time.sleep(3)
        return False

    # 自动销毁触发
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.device:
            logger.info("执行代码结束,准备关闭模拟器")
            # 执行关闭模拟器
            subprocess.run([self.__path, "quit", self.emulator_name])

    # 将账号中间设置为*号
    def mask_string(input_str):
        if len(input_str) < 8:
            return "字符串长度太短"
        first_4, last_4 = input_str[:4], input_str[-4:]
        middle_mask = "*" * (len(input_str) - 8)
        return f"{first_4}{middle_mask}{last_4}"

    # 数字转化为坐标
    def num_to_coordinate(number):
        x = 0
        y = 0
        if number == '1':
            # 66, 723
            x = 66
            y = 723
        elif number == '2':
            # 205, 721
            x = 205
            y = 721
        elif number == '3':
            # 328, 720
            x = 328
            y = 720
        elif number == '4':
            # 64, 792
            x = 64
            y = 792
        elif number == '5':
            # 201, 785
            x = 201
            y = 785
        elif number == '6':
            # (332, 783)
            x = 332
            y = 783
        elif number == '7':
            # 66, 853
            x = 66
            y = 853
        elif number == '8':
            # 201, 846)
            x = 201
            y = 846
        elif number == '9':
            # 326, 852
            x = 326
            y = 852
        elif number == '0':
            # 197, 916
            x = 197
            y = 916
        return x, y

    # 时间匹配 周一至周三 申购的新债: 次日(T+1)傍晚 ，周四 申购的新债: 周末， 周五 申购的新债:下周一傍晚
    def date_match(subscription_date_str):
        # 获取当前日期
        current_date = datetime.date.today()
        # 获取当前日期是周几（0表示周一，1表示周二，以此类推）
        current_weekday = current_date.weekday()
        # 计算目标日期
        if current_weekday == 0:  # 当前日期是周一
            # 获取上周五的日期
            target_date = current_date - datetime.timedelta(days=3)
        elif current_weekday in (1, 2, 3):  # 当前日期是周二到周四
            # 获取周一到周三的日期
            target_date = current_date - datetime.timedelta(days=1)
        elif current_weekday == 6:  # 当前日期是周日
            target_date = current_date - datetime.timedelta(days=3)  # 其他情况，保持当前日期不变
        else:
            target_date = current_date
        logger.info("获取到日期：{}", target_date)
        # 获取当前日期和时间
        current_datetime = datetime.datetime.now()
        # 从当前日期和时间中提取年份
        current_year = current_datetime.year
        # 解析给定日期为日期对象
        subscription_date = datetime.datetime.strptime("{0}-{1}".format(current_year, subscription_date_str),
                                                       "%Y-%m-%d").date()
        logger.info("解析构造日期:{}", subscription_date)
        # 比较当前日期和给定日期
        if target_date == subscription_date:
            return True
        else:
            return False

    # 是否中签
    def is_winning(self, user):
        if not self.device:
            logger.error("模拟器未连接，无法进行中签查询")
            return
        # 将资金账号中间变为*号
        account_with_fix = self.mask_string(user.account)
        # 直接通过包名打开app---同花顺
        logger.info("准备打开同花顺app")
        self.device.app_start('com.hexin.plat.android')
        # 判断程序是否打开
        if not self.device.session("com.hexin.plat.android", attach=True):
            logger.error("app打开失败")
            return
        # 判断是否有弹窗
        self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/close_button"]').click_exists(
            timeout=5)
        # 点击交易
        self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').click_exists()
        logger.info("点击交易按钮")
        # 遍历所有券商账号
        for i, v in enumerate(
                self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/txt_account_value"]').all()):
            # 判断对应的账号是否
            if account_with_fix != v.text.strip():
                continue
            logger.info("找到匹配账号【{}】,准备点击密码框", user.account)
            v.click()
            # 等待密码出现
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_edit_trade_password"]').click_exists(
                timeout=5)
            logger.info("点击密码框成功")
            logger.info("开始输入密码")
            # 输入密码
            for key in user.password:
                x, y = self.num_to_coordinate(key)
                self.device.click(x, y)
                # 每一次停留100-300毫秒
                time.sleep(random.uniform(0, 0.2))
            logger.info("输入密码成功")
            logger.info("准备点击登录按钮")
            # 点击登录
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_btn_login"]').click_exists(
                timeout=5)
            logger.info("点击登录按钮成功")
            time.sleep(random.uniform(2, 3))
            # 这里有可能存在中签弹窗的情况
            self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").click_exists(timeout=3)
            # 同花顺有弹窗可以一键申购新债,直接申购
            self.device(resourceId="com.hexin.plat.android:id/option_apply").click_exists(timeout=3)
        self.device.app_stop('com.hexin.plat.android')

    # 自动申购
    def subscription(self, user):
        if not self.device:
            logger.error("模拟器未连接，无法进行申购")
            return
        # 将资金账号中间变为*号
        account_with_fix = self.mask_string(user.account)
        # 直接通过包名打开app---同花顺
        logger.info("准备打开同花顺app")
        self.device.app_start('com.hexin.plat.android')
        # 判断程序是否打开
        if not self.device.session("com.hexin.plat.android", attach=True):
            logger.error("app打开失败")
            return
        # 判断是否有弹窗
        self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/close_button"]').click_exists(
            timeout=5)
        # 点击交易
        self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').click_exists()
        logger.info("点击交易按钮")
        # 遍历所有券商账号
        for i, v in enumerate(
                self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/txt_account_value"]').all()):
            # 判断对应的账号是否
            if account_with_fix != v.text.strip():
                continue
            logger.info("找到匹配账号【{}】,准备点击密码框", user.account)
            v.click()
            # 等待密码出现
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_edit_trade_password"]').click_exists(
                timeout=5)
            logger.info("点击密码框成功")
            logger.info("开始输入密码")
            # 输入密码
            for key in user.password:
                x, y = self.num_to_coordinate(key)
                self.device.click(x, y)
                # 每一次停留100-300毫秒
                time.sleep(random.uniform(0, 0.2))
            logger.info("输入密码成功")
            logger.info("准备点击登录按钮")
            # 点击登录
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_btn_login"]').click_exists(
                timeout=5)
            logger.info("点击登录按钮成功")
            time.sleep(random.uniform(2, 3))
            # 这里有可能存在中签弹窗的情况
            self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").click_exists(timeout=3)
            # 同花顺有弹窗可以一键申购新债,直接申购
            self.device(resourceId="com.hexin.plat.android:id/option_apply").click_exists(timeout=3)
        self.device.app_stop('com.hexin.plat.android')

    # 自动销毁触发
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.device:
            logger.info("执行代码结束,准备关闭模拟器")
            # 执行关闭模拟器
            subprocess.run([self.__path, "quit", self.emulator_name])

    # 将账号中间设置为*号
    def mask_string(input_str):
        if len(input_str) < 8:
            return "字符串长度太短"
        first_4, last_4 = input_str[:4], input_str[-4:]
        middle_mask = "*" * (len(input_str) - 8)
        return f"{first_4}{middle_mask}{last_4}"

    # 数字转化为坐标
    def num_to_coordinate(number):
        x = 0
        y = 0
        if number == '1':
            # 66, 723
            x = 66
            y = 723
        elif number == '2':
            # 205, 721
            x = 205
            y = 721
        elif number == '3':
            # 328, 720
            x = 328
            y = 720
        elif number == '4':
            # 64, 792
            x = 64
            y = 792
        elif number == '5':
            # 201, 785
            x = 201
            y = 785
        elif number == '6':
            # (332, 783)
            x = 332
            y = 783
        elif number == '7':
            # 66, 853
            x = 66
            y = 853
        elif number == '8':
            # 201, 846)
            x = 201
            y = 846
        elif number == '9':
            # 326, 852
            x = 326
            y = 852
        elif number == '0':
            # 197, 916
            x = 197
            y = 916
        return x, y

    # 时间匹配 周一至周三 申购的新债: 次日(T+1)傍晚 ，周四 申购的新债: 周末， 周五 申购的新债:下周一傍晚
    def date_match(subscription_date_str):
        # 获取当前日期
        current_date = datetime.date.today()
        # 获取当前日期是周几（0表示周一，1表示周二，以此类推）
        current_weekday = current_date.weekday()
        # 计算目标日期
        if current_weekday == 0:  # 当前日期是周一
            # 获取上周五的日期
            target_date = current_date - datetime.timedelta(days=3)
        elif current_weekday in (1, 2, 3):  # 当前日期是周二到周四
            # 获取周一到周三的日期
            target_date = current_date - datetime.timedelta(days=1)
        elif current_weekday == 6:  # 当前日期是周日
            target_date = current_date - datetime.timedelta(days=3)  # 其他情况，保持当前日期不变
        else:
            target_date = current_date
        logger.info("获取到日期：{}", target_date)
        # 获取当前日期和时间
        current_datetime = datetime.datetime.now()
        # 从当前日期和时间中提取年份
        current_year = current_datetime.year
        # 解析给定日期为日期对象
        subscription_date = datetime.datetime.strptime("{0}-{1}".format(current_year, subscription_date_str),
                                                       "%Y-%m-%d").date()
        logger.info("解析构造日期:{}", subscription_date)
        # 比较当前日期和给定日期
        if target_date == subscription_date:
            return True
        else:
            return False

    # 是否中签
    def is_winning(self, user):
        if not self.device:
            logger.error("模拟器未连接，无法进行中签查询")
            return
        # 将资金账号中间变为*号
        account_with_fix = self.mask_string(user.account)
        # 直接通过包名打开app---同花顺
        logger.info("准备打开同花顺app")
        self.device.app_start('com.hexin.plat.android')
        # 判断程序是否打开
        if not self.device.session("com.hexin.plat.android", attach=True):
            logger.error("app打开失败")
            return
        # 判断是否有弹窗
        self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/close_button"]').click_exists(
            timeout=5)
        # 点击交易
        self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').click_exists()
        logger.info("点击交易按钮")
        # 遍历所有券商账号
        for i, v in enumerate(
                self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/txt_account_value"]').all()):
            # 判断对应的账号是否
            if account_with_fix != v.text.strip():
                continue
            logger.info("找到匹配账号【{}】,准备点击密码框", user.account)
            v.click()
            # 等待密码出现
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_edit_trade_password"]').click_exists(
                timeout=5)
            logger.info("点击密码框成功")
            logger.info("开始输入密码")
            # 输入密码
            for key in user.password:
                x, y = self.num_to_coordinate(key)
                self.device.click(x, y)
                # 每一次停留100-300毫秒
                time.sleep(random.uniform(0, 0.2))
            logger.info("输入密码成功")
            logger.info("准备点击登录按钮")
            # 点击登录
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_btn_login"]').click_exists(
                timeout=5)
            logger.info("点击登录按钮成功")
            time.sleep(random.uniform(2, 3))
            # 这里有可能存在中签弹窗的情况
            self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").click_exists(timeout=3)
            # 同花顺有弹窗可以一键申购新债,直接申购
            self.device(resourceId="com.hexin.plat.android:id/option_apply").click_exists(timeout=3)
        self.device.app_stop('com.hexin.plat.android')

    # 自动申购
    def subscription(self, user):
        if not self.device:
            logger.error("模拟器未连接，无法进行申购")
            return
        # 将资金账号中间变为*号
        account_with_fix = self.mask_string(user.account)
        # 直接通过包名打开app---同花顺
        logger.info("准备打开同花顺app")
        self.device.app_start('com.hexin.plat.android')
        # 判断程序是否打开
        if not self.device.session("com.hexin.plat.android", attach=True):
            logger.error("app打开失败")
            return
        # 判断是否有弹窗
        self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/close_button"]').click_exists(
            timeout=5)
        # 点击交易
        self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').click_exists()
        logger.info("点击交易按钮")
        # 遍历所有券商账号
        for i, v in enumerate(
                self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/txt_account_value"]').all()):
            # 判断对应的账号是否
            if account_with_fix != v.text.strip():
                continue
            logger.info("找到匹配账号【{}】,准备点击密码框", user.account)
            v.click()
            # 等待密码出现
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_edit_trade_password"]').click_exists(
                timeout=5)
            logger.info("点击密码框成功")
            logger.info("开始输入密码")
            # 输入密码
            for key in user.password:
                x, y = self.num_to_coordinate(key)
                self.device.click(x, y)
                # 每一次停留100-300毫秒
                time.sleep(random.uniform(0, 0.2))
            logger.info("输入密码成功")
            logger.info("准备点击登录按钮")
            # 点击登录
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_btn_login"]').click_exists(
                timeout=5)
            logger.info("点击登录按钮成功")
            time.sleep(random.uniform(2, 3))
            # 这里有可能存在中签弹窗的情况
            self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").click_exists(timeout=3)
            # 同花顺有弹窗可以一键申购新债,直接申购
            self.device(resourceId="com.hexin.plat.android:id/option_apply").click_exists(timeout=3)
        self.device.app_stop('com.hexin.plat.android')

    # 自动销毁触发
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.device:
            logger.info("执行代码结束,准备关闭模拟器")
            # 执行关闭模拟器
            subprocess.run([self.__path, "quit", self.emulator_name])

    # 将账号中间设置为*号
    def mask_string(input_str):
        if len(input_str) < 8:
            return "字符串长度太短"
        first_4, last_4 = input_str[:4], input_str[-4:]
        middle_mask = "*" * (len(input_str) - 8)
        return f"{first_4}{middle_mask}{last_4}"

    # 数字转化为坐标
    def num_to_coordinate(number):
        x = 0
        y = 0
        if number == '1':
            # 66, 723
            x = 66
            y = 723
        elif number == '2':
            # 205, 721
            x = 205
            y = 721
        elif number == '3':
            # 328, 720
            x = 328
            y = 720
        elif number == '4':
            # 64, 792
            x = 64
            y = 792
        elif number == '5':
            # 201, 785
            x = 201
            y = 785
        elif number == '6':
            # (332, 783)
            x = 332
            y = 783
        elif number == '7':
            # 66, 853
            x = 66
            y = 853
        elif number == '8':
            # 201, 846)
            x = 201
            y = 846
        elif number == '9':
            # 326, 852
            x = 326
            y = 852
        elif number == '0':
            # 197, 916
            x = 197
            y = 916
        return x, y

    # 时间匹配 周一至周三 申购的新债: 次日(T+1)傍晚 ，周四 申购的新债: 周末， 周五 申购的新债:下周一傍晚
    def date_match(subscription_date_str):
        # 获取当前日期
        current_date = datetime.date.today()
        # 获取当前日期是周几（0表示周一，1表示周二，以此类推）
        current_weekday = current_date.weekday()
        # 计算目标日期
        if current_weekday == 0:  # 当前日期是周一
            # 获取上周五的日期
            target_date = current_date - datetime.timedelta(days=3)
        elif current_weekday in (1, 2, 3):  # 当前日期是周二到周四
            # 获取周一到周三的日期
            target_date = current_date - datetime.timedelta(days=1)
        elif current_weekday == 6:  # 当前日期是周日
            target_date = current_date - datetime.timedelta(days=3)  # 其他情况，保持当前日期不变
        else:
            target_date = current_date
        logger.info("获取到日期：{}", target_date)
        # 获取当前日期和时间
        current_datetime = datetime.datetime.now()
        # 从当前日期和时间中提取年份
        current_year = current_datetime.year
        # 解析给定日期为日期对象
        subscription_date = datetime.datetime.strptime("{0}-{1}".format(current_year, subscription_date_str),
                                                       "%Y-%m-%d").date()
        logger.info("解析构造日期:{}", subscription_date)
        # 比较当前日期和给定日期
        if target_date == subscription_date:
            return True
        else:
            return False

    # 是否中签
    def is_winning(self, user):
        if not self.device:
            logger.error("模拟器未连接，无法进行中签查询")
            return
        # 将资金账号中间变为*号
        account_with_fix = self.mask_string(user.account)
        # 直接通过包名打开app---同花顺
        logger.info("准备打开同花顺app")
        self.device.app_start('com.hexin.plat.android')
        # 判断程序是否打开
        if not self.device.session("com.hexin.plat.android", attach=True):
            logger.error("app打开失败")
            return
        # 判断是否有弹窗
        self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/close_button"]').click_exists(
            timeout=5)
        # 点击交易
        self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').click_exists()
        logger.info("点击交易按钮")
        # 遍历所有券商账号
        for i, v in enumerate(
                self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/txt_account_value"]').all()):
            # 判断对应的账号是否
            if account_with_fix != v.text.strip():
                continue
            logger.info("找到匹配账号【{}】,准备点击密码框", user.account)
            v.click()
            # 等待密码出现
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_edit_trade_password"]').click_exists(
                timeout=5)
            logger.info("点击密码框成功")
            logger.info("开始输入密码")
            # 输入密码
            for key in user.password:
                x, y = self.num_to_coordinate(key)
                self.device.click(x, y)
                # 每一次停留100-300毫秒
                time.sleep(random.uniform(0, 0.2))
            logger.info("输入密码成功")
            logger.info("准备点击登录按钮")
            # 点击登录
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_btn_login"]').click_exists(
                timeout=5)
            logger.info("点击登录按钮成功")
            time.sleep(random.uniform(2, 3))
            # 这里有可能存在中签弹窗的情况
            self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").click_exists(timeout=3)
            # 同花顺有弹窗可以一键申购新债,直接申购
            self.device(resourceId="com.hexin.plat.android:id/option_apply").click_exists(timeout=3)
        self.device.app_stop('com.hexin.plat.android')

    # 自动申购
    def subscription(self, user):
        if not self.device:
            logger.error("模拟器未连接，无法进行申购")
            return
        # 将资金账号中间变为*号
        account_with_fix = self.mask_string(user.account)
        # 直接通过包名打开app---同花顺
        logger.info("准备打开同花顺app")
        self.device.app_start('com.hexin.plat.android')
        # 判断程序是否打开
        if not self.device.session("com.hexin.plat.android", attach=True):
            logger.error("app打开失败")
            return
        # 判断是否有弹窗
        self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/close_button"]').click_exists(
            timeout=5)
        # 点击交易
        self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').click_exists()
        logger.info("点击交易按钮")
        # 遍历所有券商账号
        for i, v in enumerate(
                self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/txt_account_value"]').all()):
            # 判断对应的账号是否
            if account_with_fix != v.text.strip():
                continue
            logger.info("找到匹配账号【{}】,准备点击密码框", user.account)
            v.click()
            # 等待密码出现
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_edit_trade_password"]').click_exists(
                timeout=5)
            logger.info("点击密码框成功")
            logger.info("开始输入密码")
            # 输入密码
            for key in user.password:
                x, y = self.num_to_coordinate(key)
                self.device.click(x, y)
                # 每一次停留100-300毫秒
                time.sleep(random.uniform(0, 0.2))
            logger.info("输入密码成功")
            logger.info("准备点击登录按钮")
            # 点击登录
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_btn_login"]').click_exists(
                timeout=5)
            logger.info("点击登录按钮成功")
            time.sleep(random.uniform(2, 3))
            # 这里有可能存在中签弹窗的情况
            self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").click_exists(timeout=3)
            # 同花顺有弹窗可以一键申购新债,直接申购
            self.device(resourceId="com.hexin.plat.android:id/option_apply").click_exists(timeout=3)
        self.device.app_stop('com.hexin.plat.android')

    # 自动销毁触发
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.device:
            logger.info("执行代码结束,准备关闭模拟器")
            # 执行关闭模拟器
            subprocess.run([self.__path, "quit", self.emulator_name])

    # 将账号中间设置为*号
    def mask_string(input_str):
        if len(input_str) < 8:
            return "字符串长度太短"
        first_4, last_4 = input_str[:4], input_str[-4:]
        middle_mask = "*" * (len(input_str) - 8)
        return f"{first_4}{middle_mask}{last_4}"

    # 数字转化为坐标
    def num_to_coordinate(number):
        x = 0
        y = 0
        if number == '1':
            # 66, 723
            x = 66
            y = 723
        elif number == '2':
            # 205, 721
            x = 205
            y = 721
        elif number == '3':
            # 328, 720
            x = 328
            y = 720
        elif number == '4':
            # 64, 792
            x = 64
            y = 792
        elif number == '5':
            # 201, 785
            x = 201
            y = 785
        elif number == '6':
            # (332, 783)
            x = 332
            y = 783
        elif number == '7':
            # 66, 853
            x = 66
            y = 853
        elif number == '8':
            # 201, 846)
            x = 201
            y = 846
        elif number == '9':
            # 326, 852
            x = 326
            y = 852
        elif number == '0':
            # 197, 916
            x = 197
            y = 916
        return x, y

    # 时间匹配 周一至周三 申购的新债: 次日(T+1)傍晚 ，周四 申购的新债: 周末， 周五 申购的新债:下周一傍晚
    def date_match(subscription_date_str):
        # 获取当前日期
        current_date = datetime.date.today()
        # 获取当前日期是周几（0表示周一，1表示周二，以此类推）
        current_weekday = current_date.weekday()
        # 计算目标日期
        if current_weekday == 0:  # 当前日期是周一
            # 获取上周五的日期
            target_date = current_date - datetime.timedelta(days=3)
        elif current_weekday in (1, 2, 3):  # 当前日期是周二到周四
            # 获取周一到周三的日期
            target_date = current_date - datetime.timedelta(days=1)
        elif current_weekday == 6:  # 当前日期是周日
            target_date = current_date - datetime.timedelta(days=3)  # 其他情况，保持当前日期不变
        else:
            target_date = current_date
        logger.info("获取到日期：{}", target_date)
        # 获取当前日期和时间
        current_datetime = datetime.datetime.now()
        # 从当前日期和时间中提取年份
        current_year = current_datetime.year
        # 解析给定日期为日期对象
        subscription_date = datetime.datetime.strptime("{0}-{1}".format(current_year, subscription_date_str),
                                                       "%Y-%m-%d").date()
        logger.info("解析构造日期:{}", subscription_date)
        # 比较当前日期和给定日期
        if target_date == subscription_date:
            return True
        else:
            return False

    # 是否中签
    def is_winning(self, user):
        if not self.device:
            logger.error("模拟器未连接，无法进行中签查询")
            return
        # 将资金账号中间变为*号
        account_with_fix = self.mask_string(user.account)
        # 直接通过包名打开app---同花顺
        logger.info("准备打开同花顺app")
        self.device.app_start('com.hexin.plat.android')
        # 判断程序是否打开
        if not self.device.session("com.hexin.plat.android", attach=True):
            logger.error("app打开失败")
            return
        # 判断是否有弹窗
        self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/close_button"]').click_exists(
            timeout=5)
        # 点击交易
        self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').click_exists()
        logger.info("点击交易按钮")
        # 遍历所有券商账号
        for i, v in enumerate(
                self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/txt_account_value"]').all()):
            # 判断对应的账号是否
            if account_with_fix != v.text.strip():
                continue
            logger.info("找到匹配账号【{}】,准备点击密码框", user.account)
            v.click()
            # 等待密码出现
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_edit_trade_password"]').click_exists(
                timeout=5)
            logger.info("点击密码框成功")
            logger.info("开始输入密码")
            # 输入密码
            for key in user.password:
                x, y = self.num_to_coordinate(key)
                self.device.click(x, y)
                # 每一次停留100-300毫秒
                time.sleep(random.uniform(0, 0.2))
            logger.info("输入密码成功")
            logger.info("准备点击登录按钮")
            # 点击登录
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_btn_login"]').click_exists(
                timeout=5)
            logger.info("点击登录按钮成功")
            time.sleep(random.uniform(2, 3))
            # 这里有可能存在中签弹窗的情况
            self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").click_exists(timeout=3)
            # 同花顺有弹窗可以一键申购新债,直接申购
            self.device(resourceId="com.hexin.plat.android:id/option_apply").click_exists(timeout=3)
        self.device.app_stop('com.hexin.plat.android')

    # 自动申购
    def subscription(self, user):
        if not self.device:
            logger.error("模拟器未连接，无法进行申购")
            return
        # 将资金账号中间变为*号
        account_with_fix = self.mask_string(user.account)
        # 直接通过包名打开app---同花顺
        logger.info("准备打开同花顺app")
        self.device.app_start('com.hexin.plat.android')
        # 判断程序是否打开
        if not self.device.session("com.hexin.plat.android", attach=True):
            logger.error("app打开失败")
            return
        # 判断是否有弹窗
        self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/close_button"]').click_exists(
            timeout=5)
        # 点击交易
        self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').click_exists()
        logger.info("点击交易按钮")
        # 遍历所有券商账号
        for i, v in enumerate(
                self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/txt_account_value"]').all()):
            # 判断对应的账号是否
            if account_with_fix != v.text.strip():
                continue
            logger.info("找到匹配账号【{}】,准备点击密码框", user.account)
            v.click()
            # 等待密码出现
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_edit_trade_password"]').click_exists(
                timeout=5)
            logger.info("点击密码框成功")
            logger.info("开始输入密码")
            # 输入密码
            for key in user.password:
                x, y = self.num_to_coordinate(key)
                self.device.click(x, y)
                # 每一次停留100-300毫秒
                time.sleep(random.uniform(0, 0.2))
            logger.info("输入密码成功")
            logger.info("准备点击登录按钮")
            # 点击登录
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_btn_login"]').click_exists(
                timeout=5)
            logger.info("点击登录按钮成功")
            time.sleep(random.uniform(2, 3))
            # 这里有可能存在中签弹窗的情况
            self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").click_exists(timeout=3)
            # 同花顺有弹窗可以一键申购新债,直接申购
            self.device(resourceId="com.hexin.plat.android:id/option_apply").click_exists(timeout=3)
        self.device.app_stop('com.hexin.plat.android')

    # 自动销毁触发
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.device:
            logger.info("执行代码结束,准备关闭模拟器")
            # 执行关闭模拟器
            subprocess.run([self.__path, "quit", self.emulator_name])

    # 将账号中间设置为*号
    def mask_string(input_str):
        if len(input_str) < 8:
            return "字符串长度太短"
        first_4, last_4 = input_str[:4], input_str[-4:]
        middle_mask = "*" * (len(input_str) - 8)
        return f"{first_4}{middle_mask}{last_4}"

    # 数字转化为坐标
    def num_to_coordinate(number):
        x = 0
        y = 0
        if number == '1':
            # 66, 723
            x = 66
            y = 723
        elif number == '2':
            # 205, 721
            x = 205
            y = 721
        elif number == '3':
            # 328, 720
            x = 328
            y = 720
        elif number == '4':
            # 64, 792
            x = 64
            y = 792
        elif number == '5':
            # 201, 785
            x = 201
            y = 785
        elif number == '6':
            # (332, 783)
            x = 332
            y = 783
        elif number == '7':
            # 66, 853
            x = 66
            y = 853
        elif number == '8':
            # 201, 846)
            x = 201
            y = 846
        elif number == '9':
            # 326, 852
            x = 326
            y = 852
        elif number == '0':
            # 197, 916
            x = 197
            y = 916
        return x, y

    # 时间匹配 周一至周三 申购的新债: 次日(T+1)傍晚 ，周四 申购的新债: 周末， 周五 申购的新债:下周一傍晚
    def date_match(subscription_date_str):
        # 获取当前日期
        current_date = datetime.date.today()
        # 获取当前日期是周几（0表示周一，1表示周二，以此类推）
        current_weekday = current_date.weekday()
        # 计算目标日期
        if current_weekday == 0:  # 当前日期是周一
            # 获取上周五的日期
            target_date = current_date - datetime.timedelta(days=3)
        elif current_weekday in (1, 2, 3):  # 当前日期是周二到周四
            # 获取周一到周三的日期
            target_date = current_date - datetime.timedelta(days=1)
        elif current_weekday == 6:  # 当前日期是周日
            target_date = current_date - datetime.timedelta(days=3)  # 其他情况，保持当前日期不变
        else:
            target_date = current_date
        logger.info("获取到日期：{}", target_date)
        # 获取当前日期和时间
        current_datetime = datetime.datetime.now()
        # 从当前日期和时间中提取年份
        current_year = current_datetime.year
        # 解析给定日期为日期对象
        subscription_date = datetime.datetime.strptime("{0}-{1}".format(current_year, subscription_date_str),
                                                       "%Y-%m-%d").date()
        logger.info("解析构造日期:{}", subscription_date)
        # 比较当前日期和给定日期
        if target_date == subscription_date:
            return True
        else:
            return False

    # 是否中签
    def is_winning(self, user):
        if not self.device:
            logger.error("模拟器未连接，无法进行中签查询")
            return
        # 将资金账号中间变为*号
        account_with_fix = self.mask_string(user.account)
        # 直接通过包名打开app---同花顺
        logger.info("准备打开同花顺app")
        self.device.app_start('com.hexin.plat.android')
        # 判断程序是否打开
        if not self.device.session("com.hexin.plat.android", attach=True):
            logger.error("app打开失败")
            return
        # 判断是否有弹窗
        self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/close_button"]').click_exists(
            timeout=5)
        # 点击交易
        self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').click_exists()
        logger.info("点击交易按钮")
        # 遍历所有券商账号
        for i, v in enumerate(
                self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/txt_account_value"]').all()):
            # 判断对应的账号是否
            if account_with_fix != v.text.strip():
                continue
            logger.info("找到匹配账号【{}】,准备点击密码框", user.account)
            v.click()
            # 等待密码出现
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_edit_trade_password"]').click_exists(
                timeout=5)
            logger.info("点击密码框成功")
            logger.info("开始输入密码")
            # 输入密码
            for key in user.password:
                x, y = self.num_to_coordinate(key)
                self.device.click(x, y)
                # 每一次停留100-300毫秒
                time.sleep(random.uniform(0, 0.2))
            logger.info("输入密码成功")
            logger.info("准备点击登录按钮")
            # 点击登录
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_btn_login"]').click_exists(
                timeout=5)
            logger.info("点击登录按钮成功")
            time.sleep(random.uniform(2, 3))
            # 这里有可能存在中签弹窗的情况
            self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").click_exists(timeout=3)
            # 同花顺有弹窗可以一键申购新债,直接申购
            self.device(resourceId="com.hexin.plat.android:id/option_apply").click_exists(timeout=3)
        self.device.app_stop('com.hexin.plat.android')

    # 自动申购
    def subscription(self, user):
        if not self.device:
            logger.error("模拟器未连接，无法进行申购")
            return
        # 将资金账号中间变为*号
        account_with_fix = self.mask_string(user.account)
        # 直接通过包名打开app---同花顺
        logger.info("准备打开同花顺app")
        self.device.app_start('com.hexin.plat.android')
        # 判断程序是否打开
        if not self.device.session("com.hexin.plat.android", attach=True):
            logger.error("app打开失败")
            return
        # 判断是否有弹窗
        self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/close_button"]').click_exists(
            timeout=5)
        # 点击交易
        self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').click_exists()
        logger.info("点击交易按钮")
        # 遍历所有券商账号
        for i, v in enumerate(
                self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/txt_account_value"]').all()):
            # 判断对应的账号是否
            if account_with_fix != v.text.strip():
                continue
            logger.info("找到匹配账号【{}】,准备点击密码框", user.account)
            v.click()
            # 等待密码出现
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_edit_trade_password"]').click_exists(
                timeout=5)
            logger.info("点击密码框成功")
            logger.info("开始输入密码")
            # 输入密码
            for key in user.password:
                x, y = self.num_to_coordinate(key)
                self.device.click(x, y)
                # 每一次停留100-300毫秒
                time.sleep(random.uniform(0, 0.2))
            logger.info("输入密码成功")
            logger.info("准备点击登录按钮")
            # 点击登录
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_btn_login"]').click_exists(
                timeout=5)
            logger.info("点击登录按钮成功")
            time.sleep(random.uniform(2, 3))
            # 这里有可能存在中签弹窗的情况
            self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").click_exists(timeout=3)
            # 同花顺有弹窗可以一键申购新债,直接申购
            self.device(resourceId="com.hexin.plat.android:id/option_apply").click_exists(timeout=3)
        self.device.app_stop('com.hexin.plat.android')

    # 自动销毁触发
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.device:
            logger.info("执行代码结束,准备关闭模拟器")
            # 执行关闭模拟器
            subprocess.run([self.__path, "quit", self.emulator_name])

    # 将账号中间设置为*号
    def mask_string(input_str):
        if len(input_str) < 8:
            return "字符串长度太短"
        first_4, last_4 = input_str[:4], input_str[-4:]
        middle_mask = "*" * (len(input_str) - 8)
        return f"{first_4}{middle_mask}{last_4}"

    # 数字转化为坐标
    def num_to_coordinate(number):
        x = 0
        y = 0
        if number == '1':
            # 66, 723
            x = 66
            y = 723
        elif number == '2':
            # 205, 721
            x = 205
            y = 721
        elif number == '3':
            # 328, 720
            x = 328
            y = 720
        elif number == '4':
            # 64, 792
            x = 64
            y = 792
        elif number == '5':
            # 201, 785
            x = 201
            y = 785
        elif number == '6':
            # (332, 783)
            x = 332
            y = 783
        elif number == '7':
            # 66, 853
            x = 66
            y = 853
        elif number == '8':
            # 201, 846)
            x = 201
            y = 846
        elif number == '9':
            # 326, 852
            x = 326
            y = 852
        elif number == '0':
            # 197, 916
            x = 197
            y = 916
        return x, y

    # 时间匹配 周一至周三 申购的新债: 次日(T+1)傍晚 ，周四 申购的新债: 周末， 周五 申购的新债:下周一傍晚
    def date_match(subscription_date_str):
        # 获取当前日期
        current_date = datetime.date.today()
        # 获取当前日期是周几（0表示周一，1表示周二，以此类推）
        current_weekday = current_date.weekday()
        # 计算目标日期
        if current_weekday == 0:  # 当前日期是周一
            # 获取上周五的日期
            target_date = current_date - datetime.timedelta(days=3)
        elif current_weekday in (1, 2, 3):  # 当前日期是周二到周四
            # 获取周一到周三的日期
            target_date = current_date - datetime.timedelta(days=1)
        elif current_weekday == 6:  # 当前日期是周日
            target_date = current_date - datetime.timedelta(days=3)  # 其他情况，保持当前日期不变
        else:
            target_date = current_date
        logger.info("获取到日期：{}", target_date)
        # 获取当前日期和时间
        current_datetime = datetime.datetime.now()
        # 从当前日期和时间中提取年份
        current_year = current_datetime.year
        # 解析给定日期为日期对象
        subscription_date = datetime.datetime.strptime("{0}-{1}".format(current_year, subscription_date_str),
                                                       "%Y-%m-%d").date()
        logger.info("解析构造日期:{}", subscription_date)
        # 比较当前日期和给定日期
        if target_date == subscription_date:
            return True
        else:
            return False

    # 是否中签
    def is_winning(self, user):
        if not self.device:
            logger.error("模拟器未连接，无法进行中签查询")
            return
        # 将资金账号中间变为*号
        account_with_fix = self.mask_string(user.account)
        # 直接通过包名打开app---同花顺
        logger.info("准备打开同花顺app")
        self.device.app_start('com.hexin.plat.android')
        # 判断程序是否打开
        if not self.device.session("com.hexin.plat.android", attach=True):
            logger.error("app打开失败")
            return
        # 判断是否有弹窗
        self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/close_button"]').click_exists(
            timeout=5)
        # 点击交易
        self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').click_exists()
        logger.info("点击交易按钮")
        # 遍历所有券商账号
        for i, v in enumerate(
                self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/txt_account_value"]').all()):
            # 判断对应的账号是否
            if account_with_fix != v.text.strip():
                continue
            logger.info("找到匹配账号【{}】,准备点击密码框", user.account)
            v.click()
            # 等待密码出现
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_edit_trade_password"]').click_exists(
                timeout=5)
            logger.info("点击密码框成功")
            logger.info("开始输入密码")
            # 输入密码
            for key in user.password:
                x, y = self.num_to_coordinate(key)
                self.device.click(x, y)
                # 每一次停留100-300毫秒
                time.sleep(random.uniform(0, 0.2))
            logger.info("输入密码成功")
            logger.info("准备点击登录按钮")
            # 点击登录
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_btn_login"]').click_exists(
                timeout=5)
            logger.info("点击登录按钮成功")
            time.sleep(random.uniform(2, 3))
            # 这里有可能存在中签弹窗的情况
            self.device(resourceId="com.hexin.plat.android:id/iv_operate_cancel").click_exists(timeout=3)
            # 同花顺有弹窗可以一键申购新债,直接申购
            self.device(resourceId="com.hexin.plat.android:id/option_apply").click_exists(timeout=3)
        self.device.app_stop('com.hexin.plat.android')

    # 自动申购
    def subscription(self, user):
        if not self.device:
            logger.error("模拟器未连接，无法进行申购")
            return
        # 将资金账号中间变为*号
        account_with_fix = self.mask_string(user.account)
        # 直接通过包名打开app---同花顺
        logger.info("准备打开同花顺app")
        self.device.app_start('com.hexin.plat.android')
        # 判断程序是否打开
        if not self.device.session("com.hexin.plat.android", attach=True):
            logger.error("app打开失败")
            return
        # 判断是否有弹窗
        self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/close_button"]').click_exists(
            timeout=5)
        # 点击交易
        self.device.xpath('//*[@content-desc="交易"]/android.widget.ImageView[1]').click_exists()
        logger.info("点击交易按钮")
        # 遍历所有券商账号
        for i, v in enumerate(
                self.device.xpath('//*[@resource-id="com.hexin.plat.android:id/txt_account_value"]').all()):
            # 判断对应的账号是否
            if account_with_fix != v.text.strip():
                continue
            logger.info("找到匹配账号【{}】,准备点击密码框", user.account)
            v.click()
            # 等待密码出现
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_edit_trade_password"]').click_exists(
                timeout=5)
            logger.info("点击密码框成功")
            logger.info("开始输入密码")
            # 输入密码
            for key in user.password:
                x, y = self.num_to_coordinate(key)
                self.device.click(x, y)
                # 每一次停留100-300毫秒
                time.sleep(random.uniform(0, 0.2))
            logger.info("输入密码成功")
            logger.info("准备点击登录按钮")
            # 点击登录
            self.device.xpath(
                '//*[@resource-id="com.hexin.plat.android:id/weituo_btn_login"]').click_exists(
                timeout=5)
            logger.info("点击登录按钮成功")
            time.sleep(random.uniform(2, 3))
            # 这里有可能存在中
