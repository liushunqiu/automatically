import time
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DebtNotifier:
    def __init__(self, wechat_webhook_url: str, proxies: Optional[Dict[str, str]] = None):
        """
        初始化通知类
        :param wechat_webhook_url: 企业微信机器人webhook地址
        :param proxies: 代理设置
        """
        self.wechat_webhook_url = wechat_webhook_url
        self.proxies = proxies or {}

    def has_debt(self) -> bool:
        """
        检查当天是否有可申购的新债
        :return: 如果有可申购的新债返回True，否则返回False
        """
        milliseconds_timestamp = int(time.time() * 1000)
        url = f'https://www.jisilu.cn/data/cbnew/pre_list/?___jsl=LST___t={milliseconds_timestamp}?rp=22&page=1'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, proxies=self.proxies)
            response.raise_for_status()
            dic_bond = response.json()
            
            num = 0
            for row in dic_bond['rows']:
                if not row['cell']['bond_id']:
                    break
                    
                progress_nm = row['cell']['progress_nm']
                today = datetime.strptime(time.strftime("%Y-%m-%d", time.localtime()), '%Y-%m-%d')
                bond_date = datetime.strptime(progress_nm[:10], '%Y-%m-%d')
                
                if today > bond_date:
                    break
                elif today == bond_date and '申购' in progress_nm:
                    num += 1
                    
            return num > 0
            
        except Exception as e:
            logger.error(f"检查新债时发生错误: {e}")
            return False

    def send_wechat_notification(self, message: str) -> bool:
        """
        发送企业微信通知
        :param message: 通知消息内容
        :return: 发送成功返回True，失败返回False
        """
        try:
            data = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }
            response = requests.post(
                self.wechat_webhook_url,
                json=data,
                proxies=self.proxies
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"发送企业微信通知失败: {e}")
            return False

    def check_and_notify(self) -> bool:
        """
        检查新债并发送通知
        :return: 如果发送通知成功返回True，否则返回False
        """
        if self.has_debt():
            message = "【新债申购提醒】\n今日有新债可以申购，请及时关注！"
            return self.send_wechat_notification(message)
        return False 