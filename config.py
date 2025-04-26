import os
import json

class Config:
    def __init__(self):
        """初始化 Config 类"""
        # 默认夜神模拟器安装路径
        self.default_simulator_path = r"D:\Program Files\Nox\bin"
        # 默认券商APP包名
        self.broker_package_name = "com.hexin.plat.android"
        # 夜神模拟器主程序路径
        self.simulator_exe_path = ""
        # 内部字典，用于存储从 JSON 加载的完整配置
        self._config_data = {}

        # 尝试从配置文件加载
        self.load_config()

        # 检查路径是否存在 (这部分逻辑保持不变)
        if not os.path.exists(self.default_simulator_path):
            print(f"警告：模拟器路径不存在: {self.default_simulator_path}")
            # 尝试其他可能的路径
            possible_paths = [
                r"C:\Program Files\Nox\bin",
                r"C:\Program Files (x86)\Nox\bin",
                r"D:\Program Files\Nox\bin",
                r"D:\Program Files (x86)\Nox\bin",
                os.path.expanduser("~\\AppData\\Local\\Nox\\bin")
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    print(f"找到模拟器路径: {path}")
                    self.default_simulator_path = path
                    break
        
        # 设置模拟器主程序路径 (这部分逻辑保持不变)
        self.update_simulator_exe_path()

    def update_simulator_exe_path(self):
        """更新模拟器主程序路径"""
        try:
            normalized_path = os.path.normpath(self.default_simulator_path)
            if not os.path.exists(normalized_path):
                print(f"警告：模拟器bin目录不存在: {normalized_path}")
                return

            # 优先查找 bin 目录下的 Nox.exe
            nox_path_in_bin = os.path.join(normalized_path, "Nox.exe")
            if os.path.exists(nox_path_in_bin):
                self.simulator_exe_path = nox_path_in_bin
                print(f"找到模拟器主程序: {nox_path_in_bin}")
                return

            # 方法1：如果路径以bin结尾，直接获取父目录
            if normalized_path.endswith("\\bin") or normalized_path.endswith("/bin"):
                parent_dir = os.path.dirname(normalized_path)
                nox_path = os.path.join(parent_dir, "Nox.exe")
                if os.path.exists(nox_path):
                    self.simulator_exe_path = nox_path
                    print(f"找到模拟器主程序: {nox_path}")
                    return

            # 方法2：尝试直接在bin同级目录查找
            parent_dir = os.path.dirname(normalized_path)
            nox_path = os.path.join(parent_dir, "Nox.exe")
            if os.path.exists(nox_path):
                self.simulator_exe_path = nox_path
                print(f"找到模拟器主程序: {nox_path}")
                return
                
            # 方法3：尝试在bin的父目录查找
            grandparent_dir = os.path.dirname(parent_dir)
            nox_path = os.path.join(grandparent_dir, "Nox.exe")
            if os.path.exists(nox_path):
                self.simulator_exe_path = nox_path
                print(f"找到模拟器主程序: {nox_path}")
                return
                
            # 方法4：尝试其他常见位置
            possible_exe_paths = [
                normalized_path.replace("\\bin", ""),  # 移除bin
                normalized_path.replace("/bin", ""),   # 移除bin
                os.path.join(os.path.dirname(os.path.dirname(normalized_path)), "Nox.exe"),
                # 添加常见的安装位置
                r"D:\Program Files\Nox\Nox.exe",
                r"C:\Program Files\Nox\Nox.exe",
                r"C:\Program Files (x86)\Nox\Nox.exe"
            ]
            
            for path in possible_exe_paths:
                normalized_exe_path = os.path.normpath(path)
                if os.path.exists(normalized_exe_path):
                    self.simulator_exe_path = normalized_exe_path
                    print(f"找到模拟器主程序: {normalized_exe_path}")
                    return
            
            print(f"警告：无法找到夜神模拟器主程序，已尝试查找路径: {possible_exe_paths}")
            print(f"请手动设置正确的夜神模拟器bin目录路径")
        except Exception as e:
            print(f"更新模拟器主程序路径时出错: {str(e)}")

    def get_simulator_path(self):
        """获取模拟器安装路径"""
        # 仍然返回实例属性，但确保 save_config 会同步
        return self.default_simulator_path

    def get_simulator_exe_path(self):
        """获取模拟器主程序路径"""
        # 仍然返回实例属性，但确保 save_config 会同步
        return self.simulator_exe_path

    def get_broker_package_name(self, default=None): # 添加 default 参数
        """获取券商APP包名"""
        # 仍然返回实例属性，但确保 save_config 会同步
        # 如果 self.broker_package_name 为空或 None，则返回 default
        return self.broker_package_name if self.broker_package_name else default

    def set_simulator_path(self, path):
        """设置模拟器安装路径"""
        if os.path.exists(path):
            self.default_simulator_path = path
            # 更新主程序路径
            self.update_simulator_exe_path()
            self.save_config() # 保存时会更新 _config_data
            return True
        print(f"错误：路径不存在: {path}")
        return False

    def set_broker_package_name(self, package_name):
        """设置券商APP包名"""
        self.broker_package_name = package_name
        self.save_config() # 保存时会更新 _config_data

    def load_config(self):
        """从配置文件加载配置"""
        try:
            if os.path.exists("app_config.json"):
                with open("app_config.json", "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    self._config_data = loaded_config # 存储加载的完整数据

                    # 更新实例属性（如果存在于配置文件中）
                    if "simulator_path" in loaded_config and os.path.exists(loaded_config["simulator_path"]):
                        self.default_simulator_path = loaded_config["simulator_path"]
                    if "broker_package" in loaded_config:
                        self.broker_package_name = loaded_config["broker_package"]
                    if "simulator_exe_path" in loaded_config and os.path.exists(loaded_config["simulator_exe_path"]):
                        self.simulator_exe_path = loaded_config["simulator_exe_path"]
                    # 确保 _config_data 中有 coordinates，如果没有则添加默认值
                    if "coordinates" not in self._config_data:
                        self._config_data["coordinates"] = self._get_default_coordinates()

            else:
                # 如果配置文件不存在，初始化 _config_data 并保存
                print("配置文件 app_config.json 不存在，将创建默认配置。")
                self._config_data = {
                    "simulator_path": self.default_simulator_path,
                    "broker_package": self.broker_package_name,
                    "simulator_exe_path": self.simulator_exe_path,
                    "coordinates": self._get_default_coordinates()
                }
                self.save_config()

        except json.JSONDecodeError as json_err:
            print(f"加载配置文件失败：无效的 JSON 格式 - {str(json_err)}")
            self._initialize_default_config_data() # 加载失败时使用默认值
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            self._initialize_default_config_data() # 其他异常也使用默认值

    def _initialize_default_config_data(self):
        """初始化默认的 _config_data"""
        self._config_data = {
            "simulator_path": self.default_simulator_path,
            "broker_package": self.broker_package_name,
            "simulator_exe_path": self.simulator_exe_path,
            "coordinates": self._get_default_coordinates()
        }

    def _get_default_coordinates(self):
        """返回默认坐标字典"""
        return {
            "select_x": 201, "select_y": 785,
            "subscribe_x": 332, "subscribe_y": 783,
            "confirm_x": 197, "confirm_y": 916
        }

    def save_config(self):
        """保存配置到文件"""
        try:
            # 在保存前，确保 _config_data 反映了当前的实例属性状态
            self._config_data["simulator_path"] = self.default_simulator_path
            self._config_data["broker_package"] = self.broker_package_name
            self._config_data["simulator_exe_path"] = self.simulator_exe_path
            # 确保 coordinates 存在
            if "coordinates" not in self._config_data:
                self._config_data["coordinates"] = self._get_default_coordinates()

            with open("app_config.json", "w", encoding="utf-8") as f:
                json.dump(self._config_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")

    def get_coordinate(self, key, default=None):
        """
        从配置中获取指定的坐标值。

        Args:
            key (str): 坐标的键名 (例如 'select_x').
            default (any, optional): 如果键不存在时返回的默认值. Defaults to None.

        Returns:
            any: 坐标值或默认值.
        """
        # 从内部字典 _config_data 中安全地获取坐标
        coordinates = self._config_data.get('coordinates', {})
        return coordinates.get(key, default)

    # 可以选择性地添加 set_coordinate 方法，如果需要通过UI修改坐标
    # def set_coordinate(self, key, value):
    #     """设置指定坐标值并保存"""
    #     if 'coordinates' not in self._config_data:
    #         self._config_data['coordinates'] = {}
    #     self._config_data['coordinates'][key] = value
    #     self.save_config() # 立即保存更改