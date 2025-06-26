import asyncio
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent


@register("astrbot_plugin_top_chehui", "mingrixiangnai", "撤回上一条触发机器人的消息", "1.0", "https://github.com/mingrixiangnai/top_chehui")
class AutoRecallHandler(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.recall_tasks = {}
        logger.info("自动撤回插件已加载")

    @filter.after_message_sent()
    async def after_message_sent(self, event: AstrMessageEvent):
        """处理触发机器人的消息，设置定时撤回任务"""
        if not self.config.auto_recall_enabled:
            return
            
        # 只处理 aiocqhttp (QQ) 平台
        if event.get_platform_name() != "aiocqhttp":
            return
            
        # 检查是否为群消息，非群消息不处理
        group_id = event.get_group_id()
        if not group_id:
            return 
            
        # 检查群白名单
        if self.config.group_whitelist and group_id not in self.config.group_whitelist:
            return
            
        # 获取消息ID
        assert isinstance(event, AiocqhttpMessageEvent)
        message_id = event.message_obj.message_id
        if not message_id:
            logger.warning("无法获取消息ID，撤回功能不可用")
            return
            
        # 创建撤回任务
        self.create_recall_task(event, message_id)

    def create_recall_task(self, event: AstrMessageEvent, message_id: str):
        """创建撤回消息的异步任务"""

        # 创建新任务
        task = asyncio.create_task(self.recall_message_after_delay(event, message_id))
        self.recall_tasks[message_id] = task

    async def recall_message_after_delay(self, event: AstrMessageEvent, message_id: str):
        """延迟一分钟后撤回消息"""
        try:
            await asyncio.sleep(60)  # 等待60秒，这里可以修改
            
            # 获取bot实例并调用撤回API
            assert isinstance(event, AiocqhttpMessageEvent)
            bot = event.bot
            await bot.delete_msg(message_id=int(message_id))
            
            logger.info(f"已自动撤回消息: {message_id}")
        except Exception as e:
            logger.error(f"撤回消息失败: {e}")
        finally:
            # 清理任务
            if message_id in self.recall_tasks:
                del self.recall_tasks[message_id]

    async def terminate(self):
        """插件卸载时取消所有撤回任务"""
        for task in self.recall_tasks.values():
            task.cancel()
        self.recall_tasks.clear()
        logger.info("自动撤回插件已卸载")
        
