import os
import time
import subprocess

print("===== 尝试解决uiautomator2连接Nox模拟器问题 =====")

# 方法一：使用uiautomator2自带的命令行初始化
try:
    print("\n方法一：尝试使用uiautomator2命令行初始化设备...")
    subprocess.run("python -m uiautomator2 init 127.0.0.1:62001", shell=True)
    time.sleep(2)
    
    print("尝试连接设备...")
    import uiautomator2 as u2
    d = u2.connect("127.0.0.1:62001")
    print("连接成功！设备信息:", d.info)
    print("方法一成功！")
except Exception as e:
    print(f"方法一失败: {str(e)}")
    
    # 方法二：直接访问ATX-agent服务
    try:
        print("\n方法二：尝试直接访问ATX-agent服务...")
        import uiautomator2 as u2
        
        d = u2.connect("http://127.0.0.1:62001")
        print("连接成功！设备信息:", d.info)
        print("方法二成功！")
    except Exception as e:
        print(f"方法二失败: {str(e)}")
        
        # 方法三：先确保adb能正确连接
        try:
            print("\n方法三：重设ADB并强制安装ATX-agent...")
            
            # 先连接设备
            adb_path = "D:\\Program Files\\Nox\\bin\\nox_adb.exe"
            subprocess.run(f'"{adb_path}" connect 127.0.0.1:62001', shell=True)
            
            # 传递环境变量
            env = os.environ.copy()
            env["ANDROID_HOME"] = "D:\\Program Files\\Nox\\bin"
            
            # 执行初始化命令
            print("开始执行安装...")
            result = subprocess.run("python -m uiautomator2 init -f 127.0.0.1:62001", 
                                 shell=True, 
                                 env=env,
                                 capture_output=True,
                                 text=True)
            
            print(f"初始化输出: {result.stdout}")
            print(f"初始化错误: {result.stderr}")
            
            # 尝试连接
            import uiautomator2 as u2
            d = u2.connect("127.0.0.1:62001")
            print("连接成功！设备信息:", d.info)
            print("方法三成功！")
        except Exception as e:
            print(f"方法三失败: {str(e)}")
            
            print("\n所有方法都失败，建议使用Appium作为替代方案")
            print("1. 安装Appium: npm install -g appium")
            print("2. 安装uiautomator2驱动: appium driver install uiautomator2")
            print("3. 启动Appium服务器: appium")
            print("4. 使用Python客户端连接Appium")
            print("   pip install Appium-Python-Client")
            print("   然后使用Appium API连接设备")

print("\n开始尝试使用Appium连接设备...")
try:
    from appium import webdriver
    from appium.webdriver.common.appiumby import AppiumBy
    
    # Appium服务器连接信息
    desired_caps = {
        'platformName': 'Android',
        'deviceName': 'NoxPlayer',
        'udid': '127.0.0.1:62001',  # Nox模拟器地址
        'automationName': 'UiAutomator2',
        'newCommandTimeout': 3600
    }
    
    # 连接到Appium服务器
    driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
    print("Appium连接成功！")
    
    # 获取设备信息
    source = driver.page_source
    print(f"当前界面元素: {source[:200]}...")  # 只显示前200个字符
    
except Exception as e:
    print(f"Appium连接失败: {str(e)}")
    print("请确保Appium服务已启动，并检查设备连接")