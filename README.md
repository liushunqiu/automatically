# 自动化交易系统

这是一个基于Python的自动化交易系统，用于自动控制模拟器执行申购流程。

## 项目结构

```
.
├── entity/              # 数据实体模型
│   ├── base_model.py    # 数据库基础模型
│   ├── user.py          # 用户模型
│   └── mydatabase.db    # SQLite数据库文件
├── ui/                  # 用户界面组件
│   ├── account_dialog.py # 账号管理对话框
│   └── settings_dialog.py # 设置对话框
├── workers/             # 后台工作线程
│   └── adb_worker.py    # ADB操作工作线程
├── app_config.json      # 应用配置文件
├── config.py            # 配置管理类
├── main.py              # 主程序入口
├── mydatabase.db        # SQLite数据库文件
├── requirements.txt     # 项目依赖
├── run.py               # 程序启动器（推荐使用）
├── simple_emulator.py   # 简化的模拟器控制模块
└── simulator.py         # 模拟器控制器
```

## 运行环境要求

- Python 3.x
- 夜神模拟器（Nox）已安装
- 网络连接通畅

## 安装依赖

在项目根目录下执行以下命令安装项目依赖：

```bash
pip install -r requirements.txt
```

如果遇到网络问题，可以使用国内镜像源：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 配置说明

运行前请确认`app_config.json`中的配置是否正确，尤其是以下配置项：

```json
{
  "simulator_path": "D:\\Program Files\\Nox\\bin",  // 模拟器bin目录路径
  "simulator_exe_path": "D:\\Program Files\\Nox\\bin\\Nox.exe", // 模拟器执行文件路径
  "broker_package": "com.hexin.plat.android",       // 券商APP包名
  "coordinates": {
    "select_x": 201,
    "select_y": 785,
    "subscribe_x": 332,
    "subscribe_y": 783,
    "confirm_x": 197,
    "confirm_y": 916
  }
}
```

## 运行程序

使用启动器运行程序（推荐）：

```bash
python run.py
```

或者直接运行主程序：

```bash
python main.py
```

程序启动后，界面中会提供以下功能：
1. 连接模拟器：检查并连接到夜神模拟器
2. 申购操作：输入账号密码后执行自动申购

## 常见问题

### 1. 模拟器无法连接

- 确认夜神模拟器已安装并且能正常启动
- 检查`app_config.json`中模拟器路径是否正确
- 确保ADB服务正常运行

### 2. 申购操作失败

- 确认账号密码正确
- 检查网络连接是否正常
- 观察模拟器界面，看是否有异常提示

### 3. 程序崩溃或不响应

- 检查Python版本是否为3.x
- 确认所有依赖都已安装完成
- 查看日志文件获取更多错误信息

## 核心模块说明

- `simple_emulator.py`: 简化的模拟器连接和控制核心功能，专注于稳定连接
- `simulator.py`: 模拟器控制器，提供高级接口和连接状态管理
- `workers/adb_worker.py`: ADB操作的异步处理线程，避免界面阻塞
- `main.py`: 主程序界面，提供完整的GUI操作界面

## 开发说明

本项目使用以下核心库：
- `PyQt6`: 用户界面
- `uiautomator2`: Android设备控制
- `peewee`: 数据库ORM
- `loguru`: 日志处理

## 联系支持

如有任何问题，请联系项目维护者获取支持。 