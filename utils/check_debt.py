import os
import logging
from notifier import DebtNotifier

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # 从环境变量获取企业微信webhook地址
    webhook_url = os.getenv('WECHAT_WEBHOOK_URL')
    if not webhook_url:
        logger.error("未设置企业微信webhook地址环境变量")
        return

    # 创建通知实例
    notifier = DebtNotifier(wechat_webhook_url=webhook_url)
    
    # 检查并发送通知
    if notifier.check_and_notify():
        logger.info("新债检查完成，已发送通知")
    else:
        logger.info("今日无新债可申购")

if __name__ == "__main__":
    main() 