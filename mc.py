import copy
import datetime
import logging
import random
import re
import socket
import sys
import time
from typing import Dict, Any
from apscheduler.schedulers.blocking import BlockingScheduler
from javascript import require, On
import importlib

# 导入新创建的模块
from functions import (
    config,
    DatabaseManager, RIALogin, RIAOnline, RIALogInfo, RIAMsgSend, RIALogCommon,
    GeometryUtils, SystemUtils, EasterEggManager,
    main_ai,
    keys, keys_set,
    get_kook_api_instance, send_kook_message, create_tables
)
from functions import logger, logger_com, logger_ai

logger.info('正在初始化...')

# 初始化数据库管理器
db_manager = DatabaseManager()

# 创建数据库表
create_tables()

# 初始化KOOK API
kook_api = get_kook_api_instance()

# 常量定义
WELCOME_MESSAGE = '向着星辰与深渊！欢迎来到冒险家协会'

# AI对话缓存
ai_conversation_cache: Dict[str, Any] = {}
caches: Dict[str, Any] = {}

# AI访问令牌（已废弃，保持兼容性）
ai_token = None
token = None

# 数据库模型和配置已移动到database.py模块
# 数据库连接自检
logger.info(f'数据库连接自检：\nRIA数据库：{db_manager.ria_db_exists}')

# 彩蛋管理器已移动到utils.py模块
easter_egg_manager = EasterEggManager()


# 全局变量声明（将在initialize_bot函数中初始化）
mc_bot = None
bot = None
start_time = None
blocks = None
entity = None


# noinspection PyUnresolvedReferences
class TimetableManager:
    """时间表管理器类"""

    def __init__(self):
        self.last_import_date: Dict[str, datetime.date] = {}
        self.info = None
        self.scheduler = BlockingScheduler()
        self.place = 'main'

        # 初始化调度器
        self.scheduler.add_job(self.update_aps, 'cron', hour='0', minute='1', id='check_scheduler')

        # 初始化时间表信息和当前位置
        self.import_timetable()
        self.place = find_closest_past_place(self.info.place_timetable)

    def import_timetable(self) -> None:
        """导入时间表信息，每天只导入一次"""
        today = datetime.datetime.now().date()

        # 检查是否已经在今天加载过模块
        if 'function' in self.last_import_date and self.last_import_date['function'] == today:
            return

        # 清空模块缓存
        if 'function' in sys.modules:
            del sys.modules['function']

        try:
            # 导入时间表模块
            self.info = importlib.import_module('functions.timetable_info')
            self.last_import_date['function'] = today
            logger.info(f"时间表模块已在 {today} 重新加载")
        except ImportError as e:
            logger.error(f"导入时间表模块失败: {e}")

    def transport_function(self, place2: str) -> None:
        """传送功能，检查位置并执行传送

        Args:
            place2: 目标位置名称
        """
        self.place = place2

        # 获取当前位置
        current_position_str = bot.entity.position.toString()
        current_position = GeometryUtils.str_to_tuple(current_position_str)

        # 获取目标位置
        target_position = self.info.place_map[place2]

        # 计算距离
        distance = GeometryUtils.distance_between_points(current_position, target_position)
        tolerance = 5  # 允许的位置误差

        if distance < tolerance:
            return
        else:
            bot.chat(f'/home {place2}')

    def register_aps(self) -> None:
        """注册时间表任务到调度器"""
        if not self.info or not hasattr(self.info, 'place_timetable'):
            logger.warning("时间表信息不完整，无法注册任务")
            return

        for place2, start in self.info.place_timetable.items():
            try:
                self.scheduler.add_job(
                    self.transport_function,
                    'cron',
                    hour=str(start.hour),
                    minute=str(start.minute),
                    id=place2,
                    args=(place2,)
                )
                logger.info(f"已注册传送任务: {place2} at {start.hour}:{start.minute}")
            except Exception as e:
                logger.error(f"注册传送任务失败 {place2}: {e}")

    def update_aps(self) -> None:
        """更新调度器任务，每天运行一次"""
        old_info = copy.deepcopy(self.info)
        self.import_timetable()

        # 如果时间表没有变化，则不需要更新
        if old_info == self.info:
            return

        # 删除除了检查调度器之外的所有任务
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            if job.id != 'check_scheduler':
                try:
                    self.scheduler.remove_job(job.id)
                except Exception as e:
                    logger.error(f"删除任务失败 {job.id}: {e}")

        # 重新注册任务
        self.register_aps()
        logger.info("时间表任务已更新")


# noinspection PyUnresolvedReferences
class GameUtils:
    """游戏工具类，管理Minecraft相关的游戏功能"""

    @staticmethod
    def check_transport_place() -> None:
        """检测机器人是否处在正确的位置，如果不在则传送"""
        try:
            current_position_str = bot.entity.position.toString()
            current_position = GeometryUtils.str_to_tuple(current_position_str)

            place = timetable_manager.place
            target_position = timetable_manager.info.place_map[place]

            distance = GeometryUtils.distance_between_points(current_position, target_position)
            tolerance = 5  # 允许的位置误差

            if distance >= tolerance:
                bot.chat(f'/home {place}')
                logger.info(f"位置偏离过大，传送到 {place}")
        except Exception as e:
            logger.error(f"检查传送位置失败: {e}")

    @staticmethod
    def find_bed_block():
        """查找床方块

        Returns:
            床方块对象或None
        """
        try:
            GameUtils.check_transport_place()
            beds = bot.findBlocks({'matching': 103})
            if beds and len(beds) > 0:
                return bot.blockAt(beds[0])
            return None
        except Exception as e:
            logger.error(f"查找床方块失败: {e}")
            return None

    @staticmethod
    def exit_game(reason: str) -> None:
        """安全退出游戏和程序

        Args:
            reason: 退出原因
        """
        reason_str = str(reason)
        logger.error(f'程序结束，原因：{reason_str}')
        print(f'程序结束，原因：{reason_str}')

        # 关闭数据库连接
        try:
            db_manager.close()
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")

        # 退出机器人
        try:
            bot.quit()
        except Exception as e:
            logger.error(f'bot.quit()失败: {e}')

        # 关闭调度器
        try:
            timetable_manager.scheduler.shutdown(wait=False)
        except Exception as e:
            logger.error(f"关闭调度器失败: {e}")

        # 使用SystemUtils安全退出
        SystemUtils.safe_exit()

    @staticmethod
    def check_entity_status() -> bool:
        """检查机器人实体状态

        Returns:
            True如果实体正常，False如果有问题
        """
        try:
            entity = bot.entity
            if entity is None:
                logger.error('机器人实体不存在')
                return False
            return True
        except Exception as e:
            logger.error(f'检查实体状态失败: {e}')
            return False

    @staticmethod
    def check_online_status() -> bool:
        """检查在线状态

        Returns:
            bool: 是否在线正常
        """
        try:
            if not GameUtils.check_entity_status():
                runtime = time.time() - minecraft_bot.start_time
                error_msg = f"登录失败，实体初始化为None，程序运行时间：{runtime}s"
                kook_api.send_message(config.KOOK_MAIN_CHANNEL, f"发送错误。原因: {error_msg}")

                # 如果运行时间超过10分钟仍未正常，退出程序
                if runtime > 600:
                    GameUtils.exit_game('长时间无法正常登录')
                    return False

                return False

            # 正常在线，记录玩家信息
            try:
                num = random.randint(1, 100)
                bot.look(num, 0)
                players = bot.players.valueOf()
                logger.info(f'当前在线玩家：{players.keys()}')

                # 使用DatabaseService的方法记录在线玩家
                for player_name, data_info in players.items():
                    db_service.record_online_player(player_name, data_info)

            except Exception as e:
                logger.error(f'记录在线玩家信息失败: {e}')

            return True

        except Exception as e:
            logger.error(f'检查在线状态失败: {e}')
            return False


# noinspection PyUnresolvedReferences,PyTypeChecker
class BotEventHandler:
    """机器人事件处理器类"""

    @staticmethod
    def handle_chat(this, username: str, message: str, *args) -> None:
        """处理聊天事件

        Args:
            this: 事件对象
            username: 用户名
            message: 消息内容
            *args: 其他参数
        """
        try:
            # 记录聊天日志
            logger_com.info(f'[{username}]: {message}')

            # 保存到数据库 - 使用DatabaseService的方法
            db_service.add_chat_log(username, message)

            # 忽略机器人自己的消息
            if username == bot.username:
                return

            # 检查彩蛋关键词
            easter_egg_result = easter_egg_manager.check(message)
            if easter_egg_result:
                BotEventHandler._handle_easter_egg(username, message, easter_egg_result)

        except Exception as e:
            logger.error(f"处理聊天事件失败: {e}")

    @staticmethod
    def _handle_easter_egg(username: str, message: str, easter_egg_result: Dict[str, Any]) -> None:
        """处理彩蛋触发

        Args:
            username: 触发用户
            message: 触发消息
            easter_egg_result: 彩蛋结果
        """
        try:
            keyword = easter_egg_result['egg']
            value = easter_egg_result['value']

            # 发送通知消息
            notification = f'{username} 发送了 {message}，触发了彩蛋关键词{keyword}，价值{value} O锭。'
            kook_api.send_message(config.KOOK_MAIN_CHANNEL, notification)
            logger.info(notification)

            # 游戏内通知和奖励
            bot.chat(f'{username}触发了彩蛋关键词-{keyword}-！恭喜{username}获得 O锭*{value} ！')
            bot.chat(f'/pay {username} {value}')

        except Exception as e:
            logger.error(f"处理彩蛋事件失败: {e}")

    @staticmethod
    def handle_login(this) -> None:
        """处理登录事件"""
        try:
            time.sleep(5)  # 等待服务器准备

            # 执行登录命令
            server_password = config.SERVER_PASSWORD
            if server_password:
                bot.chat(f"/login {server_password}")

            # 记录登录信息
            login_time = datetime.datetime.now()
            login_message = f'于 {login_time} 成功登录'
            logger.info(login_message)

            # 发送KOOK通知
            kook_notification = f'于 {login_time} 成功登录 RIA服务器'
            kook_api.send_message(config.KOOK_MAIN_CHANNEL, kook_notification)

            # 传送到指定位置
            time.sleep(1)
            if timetable_manager is not None:
                place = timetable_manager.place
                bot.chat(f'/home {place}')
                logger.info(f'传送指令已输入，目标位置: {place}')
            else:
                # 如果timetable_manager未初始化，使用默认位置
                default_place = 'main'
                bot.chat(f'/home {default_place}')
                logger.warning(f'时间表管理器未初始化，使用默认位置: {default_place}')

        except Exception as e:
            logger.error(f"处理登录事件失败: {e}")

    @staticmethod
    def handle_forced_move(this) -> None:
        """处理强制移动事件"""
        try:
            position = bot.entity.position
            logger.info(f"强制移动至 {position.toString()}")
        except Exception as e:
            logger.error(f"处理强制移动事件失败: {e}")

    @staticmethod
    def handle_health(this) -> None:
        """处理健康状态变化事件"""
        try:
            health_info = f"健康值: {bot.health}, 饱食度: {bot.food}"
            logger.info(health_info)
        except Exception as e:
            logger.error(f"处理健康状态事件失败: {e}")

    @staticmethod
    def handle_death(this) -> None:
        """处理死亡事件"""
        try:
            death_message = f"{bot.username} 游戏失败"
            logger.info(death_message)
            kook_api.send_message(config.KOOK_MAIN_CHANNEL, death_message)
        except Exception as e:
            logger.error(f"处理死亡事件失败: {e}")

    @staticmethod
    def handle_kicked(this, reason: str, *args) -> None:
        """处理被踢出事件

        Args:
            this: 事件对象
            reason: 被踢出原因
            *args: 其他参数
        """
        try:
            kick_message = f"被踢出服务器，原因: {reason}"
            logger.error(kick_message)
            GameUtils.exit_game(kick_message)
        except Exception as e:
            logger.error(f"处理被踢出事件失败: {e}")

    @staticmethod
    def handle_player_joined(this, player: Dict[str, Any]) -> None:
        """处理玩家加入事件

        Args:
            this: 事件对象
            player: 玩家信息
        """
        try:
            username = player.get('username')
            if not username or username == bot.username:
                return

            logger.info(f"{username} 加入了RIA")

            # 使用DatabaseService的方法记录玩家登录
            db_service.record_player_login(username)

            join_message = f"{username} 加入了RIA-零洲。"
            kook_api.send_message(config.KOOK_MAIN_CHANNEL, join_message)
            logger.info(join_message)

        except Exception as e:
            logger.error(f"处理玩家加入事件失败: {e}")

    @staticmethod
    def handle_player_left(this, player: Dict[str, Any]) -> None:
        """处理玩家离开事件

        Args:
            this: 事件对象
            player: 玩家信息
        """
        try:
            username = player.get('username')
            if not username or username == bot.username:
                return

            logger.info(f"{username} 离开了RIA")

            # 使用DatabaseService的方法记录玩家登出并获取在线时长
            duration_str = db_service.record_player_logout(username)

            # 如果在线时间超过1分钟，发送通知
            if duration_str:
                leave_message = f"{username} 离开了RIA，在线时长 {duration_str}"
                kook_api.send_message(config.KOOK_MAIN_CHANNEL, leave_message)
                logger.info(leave_message)

        except Exception as e:
            logger.error(f"处理玩家离开事件失败: {e}")

    @staticmethod
    def handle_message_str(this, message: str, *args) -> None:
        """处理消息字符串事件

        Args:
            this: 事件对象
            message: 消息内容
            *args: 其他参数
        """
        try:
            logger.info(message)

            # 保存到数据库 - 使用DatabaseService的方法
            db_service.add_common_log(message)

            if '请求传送到你的位置' in message:
                if bot.isSleeping:
                    bot.wake()
                    time.sleep(0.1)
                playername = message.replace('请求传送到你的位置', '').replace(' ', '')
                place = timetable_manager.place
                place_map_2 = timetable_manager.info.place_map_2
                if place == 'iron':
                    bot.chat("/m " + playername + " 你好，现在为凌晨，将延迟1s传送。")
                    bot.chat("/home main")
                    time.sleep(1.1)
                    bot.chat("/tpaccept")
                    time.sleep(0.1)

                    bot.chat(
                        "/m " + playername + f" 你好，我已接受传送请求。{WELCOME_MESSAGE}。这里是-->{place_map_2['main']}<--")
                    time.sleep(1.1)
                    bot.chat("/m " + playername + " 我还有事，先走了。")
                    time.sleep(0.1)
                    bot.chat('/back')
                    send_kook_message(config.KOOK_MAIN_CHANNEL, f'接受来自{playername}的传送请求')
                    logger.info(f'接受来自{playername}的传送请求')
                    return
                bot.chat("/tpaccept")
                time.sleep(0.1)
                bot.chat(
                    "/m " + playername + f" 你好，我已接受传送请求。{WELCOME_MESSAGE}。这里是-->{place_map_2[place]}<--")
                send_kook_message(config.KOOK_MAIN_CHANNEL, f'接受来自{playername}的传送请求')
                logger.info(f'接受来自{playername}的传送请求')
            elif f'{config.MINECRAFT_USERNAME} was slain by' in message:
                logger.info(f'{message}')
                send_kook_message(config.KOOK_MAIN_CHANNEL, f'{message}')
                # ss.send_group(message)
            elif '-> 你]' in message:  #:[xiaocheng -> 你]
                user = message.split('-> 你]')[0].replace(' ', '')[1:]
                msg = message.split('-> 你]')[1].replace(' ', '')
                logger.info(f'msg:{msg}')
                # 对msg的关键词搜查，用于调用知识库来回答问题
                keys_used_dict = dict()
                keys_cache = []
                for key_word in keys_set:
                    if key_word in msg:
                        # 需要考虑同一个关键词命中两次的问题
                        if keys[key_word] not in keys_cache:
                            keys_used_dict[key_word] = keys[key_word]
                            keys_cache.append(keys[key_word])
                del keys_cache
                logger_ai.info(f'{user}:{msg}')
                send_kook_message(config.KOOK_AI_CHANNEL, f'{user}:{msg}')
                global caches
                answer, caches = main_ai(user, msg, caches, reference=keys_used_dict)
                if '/pay' in answer:
                    answer = '请不要这么做。这并不好玩。'
                ans1 = re.split('\n', answer)

                def split_string(answer, chunk_size=90):
                    # 使用列表推导式来分割字符串
                    chunks = [answer[i:i + chunk_size] for i in range(0, len(answer), chunk_size)]
                    return chunks

                result = []
                for i in ans1:
                    aaa = split_string(i)
                    if aaa != []:
                        result.append(aaa[0])
                for iii in result:
                    bot.chat(f'/m {user} {iii}')
                    time.sleep(1.1)
                logger_ai.info(f'AI:{answer}')
                send_kook_message(config.KOOK_AI_CHANNEL, f'AI:{answer}')
            else:
                return

        except Exception as e:
            logger.error(f"处理消息字符串事件失败: {e}")

    @staticmethod
    def handle_spawn(this) -> None:
        """处理重生事件"""
        try:
            logger.info(f"----------{bot.username}----------重生")
            place = timetable_manager.place if timetable_manager else 'main'
            bot.chat(f'/home {place}')
            logger.info(f"重生后传送到 {place}")
        except Exception as e:
            logger.error(f"处理重生事件失败: {e}")

    @staticmethod
    def handle_entity_hurt(this, entity) -> None:
        """处理实体受伤事件

        Args:
            this: 事件对象
            entity: 受伤的实体
        """
        try:
            entity_name = getattr(entity, 'displayName', '未知实体')

            if hasattr(entity, 'type'):
                if entity.type == "mob":
                    hurt_message = f"{entity_name}受到来自怪物的伤害！"
                elif entity.type == "player":
                    hurt_message = f"{entity_name}受到来自玩家的伤害！"
                else:
                    hurt_message = f"{entity_name}受到伤害！"

                kook_api.send_message(config.KOOK_MAIN_CHANNEL, hurt_message)
                logger.info(hurt_message)

        except Exception as e:
            logger.error(f"处理实体受伤事件失败: {e}")

    @staticmethod
    def handle_error(this, error) -> None:
        """处理错误事件

        Args:
            this: 事件对象
            error: 错误信息
        """
        try:
            error_message = f"机器人发生错误: {error}"
            logger.error(error_message)
            GameUtils.exit_game(error_message)
        except Exception as e:
            logger.error(f"处理错误事件失败: {e}")

    @staticmethod
    def handle_end(this, *args) -> None:
        """处理程序结束事件

        Args:
            this: 事件对象
            *args: 其他参数
        """
        try:
            end_message = f"程序结束，参数: {args}"
            logger.info(end_message)
            print(end_message)
        except Exception as e:
            logger.error(f"处理程序结束事件失败: {e}")

    @staticmethod
    def clear_ender_chest() -> bool:
        """打开末影箱并清空背包物品

        Returns:
            bool: 操作是否成功
        """
        try:
            # 查找末影箱 (方块ID: 344)
            ender_chests = bot.findBlocks({'matching': 344})
            if not ender_chests or len(ender_chests) == 0:
                logger.warning('未找到末影箱！')
                return False

            block = bot.blockAt(ender_chests[0])

            # 尝试打开末影箱
            try:
                window = bot.openContainer(block)
            except Exception as e:
                logger.error(f'打开末影箱失败: {e}')
                return False

            # 将背包物品存入末影箱
            bag_slots = bot.inventory.slots
            deposited_count = 0

            for item in bag_slots:
                if item is not None:
                    try:
                        window.deposit(item.type, item.metadata, item.count, item.nbt)
                        logger.info(f'成功放入物品: {item.displayName} 共计{item.count}个')
                        deposited_count += 1
                    except Exception as e:
                        logger.warning(f'放入物品失败: {e}')

            window.close()
            logger.info(f'末影箱操作完成，共存入 {deposited_count} 种物品')
            return True

        except Exception as e:
            logger.error(f'清空末影箱操作失败: {e}')
            return False

    @staticmethod
    def transport_to_iron_farm() -> None:
        """传送到刷铁塔"""
        try:
            place = 'iron'
            bot.chat(f'/home {place}')
            time.sleep(1.3)
            bot.chat('/sit')

            message = '抵达刷铁塔'
            kook_api.send_message(config.KOOK_MAIN_CHANNEL, message)
            logger.info(message)

        except Exception as e:
            logger.error(f'传送到刷铁塔失败: {e}')

    @staticmethod
    def transport_to_main() -> None:
        """传送到主要位置并执行签到"""
        try:
            place = 'main'
            bot.chat(f'/home {place}')

            message = '抵达-云岫郡外交公馆'
            kook_api.send_message(config.KOOK_MAIN_CHANNEL, message)
            logger.info(message)

            # 坐下并签到
            bot.chat('/sit')
            bot.chat('/signin click')
            logger.info('签到完成')

            time.sleep(0.9)
            # 可选：清空末影箱
            # GameUtils.clear_ender_chest()

        except Exception as e:
            logger.error(f'传送到主要位置失败: {e}')

    @staticmethod
    def transport_to_community() -> None:
        """传送到社区位置"""
        try:
            place = 'community'
            bot.chat(f'/home {place}')

            message = '抵达-云岫郡外交公馆'
            kook_api.send_message(config.KOOK_MAIN_CHANNEL, message)
            logger.info(message)

        except Exception as e:
            logger.error(f'传送到社区失败: {e}')

    @staticmethod
    def auto_store_items() -> None:
        """自动存储物品到末影箱"""
        try:
            # 检查实体状态
            if not GameUtils.check_entity_status():
                return

            # 检查是否在睡觉
            if bot.isSleeping:
                return

            # 检查是否有末影箱
            ender_chests = bot.findBlocks({'matching': 344})
            if not ender_chests or len(ender_chests) == 0:
                return

            # 检查背包是否有特定物品需要存储
            bag_slots = bot.inventory.slots
            has_items_to_store = any(
                item is not None and '1141' in str(item)
                for item in bag_slots
            )

            if has_items_to_store:
                GameUtils.clear_ender_chest()

        except Exception as e:
            logger.error(f'自动存储物品失败: {e}')

    @staticmethod
    def auto_sleep() -> None:
        """自动睡觉功能"""
        try:
            # 检查实体状态
            if not GameUtils.check_entity_status():
                runtime = time.time() - minecraft_bot.start_time
                error_msg = f"登录失败，实体初始化为None，程序运行时间：{runtime}s"
                kook_api.send_message(config.KOOK_MAIN_CHANNEL, f"发送错误。原因: {error_msg}")
                return

            # 只在主要位置睡觉
            place = timetable_manager.place
            if place != 'main':
                return

            # 检查是否已经在睡觉或是白天
            if bot.isSleeping or bot.time.isDay:
                return

            # 尝试睡觉
            bed = GameUtils.find_bed_block()
            if bed:
                bot.sleep(bed)
                logger.info('自动睡觉成功')

        except Exception as e:
            logger.error(f'自动睡觉失败: {e}')


def find_closest_past_place(place_timetable: Dict[str, datetime.time]) -> str:
    """找到时间表中最接近当前时间的过去位置
    
    Args:
        place_timetable: 位置时间表字典
        
    Returns:
        最接近的位置名称
    """
    now = datetime.datetime.today().time().hour
    max_key = None
    max_time = -1

    # 遍历时间表，找到小于当前时间的最大小时数
    for place, time_obj in place_timetable.items():
        if 0 <= time_obj.hour <= now:
            if time_obj.hour > max_time:
                max_time = time_obj.hour
                max_key = place

    # 如果没有找到比当前时间小的时间，则选择最大的时间
    if max_key is None:
        for place, time_obj in place_timetable.items():
            if time_obj.hour == max(place_timetable.values()).hour:
                return place

    return max_key


# 时间表管理器将在initialize_bot函数中初始化
timetable_manager = None


# 几何计算工具类函数已移动到utils.py模块中的GeometryUtils类



class MinecraftBot:
    """Minecraft机器人管理类"""

    def __init__(self):
        self.js_threads = []
        self.start_time = time.time()
        self._initialize_mineflayer()
        self._create_bot()
        self._initialize_minecraft_data()

    def _initialize_mineflayer(self):
        """初始化mineflayer相关模块"""
        self.mineflayer = require("mineflayer", "latest")
        self.js_threads.append(self.mineflayer)
        self.Vec3 = require("vec3", 'latest').Vec3
        self.js_threads.append(self.Vec3)

    def _create_bot(self):
        """创建Minecraft机器人实例"""
        # 域名解析
        domain = config.MINECRAFT_HOST
        host = socket.gethostbyname(domain)
        port = config.MINECRAFT_PORT
        username = config.MINECRAFT_USERNAME
        auth = config.MINECRAFT_AUTH

        logger.info(f'登陆信息：\nplayer:{username}\nhost:{host}\nauth:{auth}')

        bot_config = {
            "host": host,
            "port": port,
            "username": username
        }

        if auth == 'True':
            bot_config.update({
                'auth': 'microsoft',
                'version': '1.18.2'
            })

        self.bot = self.mineflayer.createBot(bot_config)
        time.sleep(1)

    def _initialize_minecraft_data(self):
        """初始化Minecraft数据"""
        minecraft_data = require('minecraft-data', "latest")
        self.js_threads.append(minecraft_data)
        self.blocks = minecraft_data.blocks
        self.entities = minecraft_data.entities

    def get_bot(self):
        """获取机器人实例"""
        return self.bot

    def get_start_time(self):
        """获取启动时间"""
        return self.start_time


def register_event_handlers():
    """注册事件处理器"""
    global bot

    @On(bot, "chat")
    def handle_chat_event(this, username, message, *args):
        BotEventHandler.handle_chat(this, username, message, *args)

    @On(bot, "login")
    def handle_login_event(this):
        BotEventHandler.handle_login(this)
        time.sleep(1)

    @On(bot, "forcedMove")
    def handle_forced_move_event(this):
        BotEventHandler.handle_forced_move(this)

    @On(bot, "health")
    def handle_health_event(this):
        BotEventHandler.handle_health(this)

    @On(bot, "death")
    def handle_death_event(this):
        BotEventHandler.handle_death(this)

    @On(bot, "kicked")
    def handle_kicked_event(this, reason, *args):
        BotEventHandler.handle_kicked(this, reason, *args)

    @On(bot, "playerJoined")
    def handle_player_joined_event(this, player):
        BotEventHandler.handle_player_joined(this, player)

    @On(bot, "playerLeft")
    def handle_player_left_event(this, player):
        BotEventHandler.handle_player_left(this, player)

    @On(bot, "messagestr")
    def handle_message_str_event(this, message, *args):
        BotEventHandler.handle_message_str(this, message, *args)

    @On(bot, "spawn")
    def handle_spawn_event(this):
        BotEventHandler.handle_spawn(this)

    @On(bot, "entityHurt")
    def handle_entity_hurt_event(this, entity):
        BotEventHandler.handle_entity_hurt(this, entity)

    @On(bot, "error")
    def handle_error_event(this, error):
        BotEventHandler.handle_error(this, error)

    @On(bot, "end")
    def handle_end_event(this, *args):
        BotEventHandler.handle_end(this, *args)


class MessageManager:
    """消息管理器"""

    @staticmethod
    def check_bot_status() -> bool:
        """检查机器人状态
        
        Returns:
            bool: 机器人是否正常
        """
        try:
            if not GameUtils.check_entity_status():
                runtime = time.time() - minecraft_bot.start_time
                error_msg = f"登录失败，实体初始化为None，程序运行时间：{runtime}s"
                kook_api.send_message(config.KOOK_MAIN_CHANNEL, f"发送错误。原因: {error_msg}")

                if runtime > 600:
                    GameUtils.exit_game('长时间无法正常登录')
                    return False

                return False

            return True

        except Exception as e:
            logger.error(f'检查机器人状态失败: {e}')
            return False

    @staticmethod
    def send_pending_messages() -> None:
        """发送待发送的消息"""
        try:
            if not MessageManager.check_bot_status():
                return

            # 使用DatabaseService的方法获取待发送消息
            pending_messages = db_service.get_pending_messages()

            if not pending_messages:
                return

            # 发送消息
            for message in pending_messages:
                try:
                    # 处理编码问题
                    text = message.text
                    if isinstance(text, bytes):
                        text = text.decode('utf-8')

                    logger.info(f'发送消息: {text}')
                    bot.chat(text)

                    # 使用DatabaseService的方法删除已发送的消息
                    db_service.delete_message(message.id)

                    time.sleep(1)  # 避免发送过快

                except Exception as e:
                    logger.error(f'发送消息失败: {e}')
                    continue

        except Exception as e:
            logger.error(f'处理待发送消息失败: {e}')



# 初始化全局变量
minecraft_bot = None
timetable_manager = None


def initialize_bot():
    """初始化机器人和相关组件"""
    global minecraft_bot, timetable_manager, mc_bot, bot, start_time, blocks, entity

    try:
        # 创建机器人实例
        minecraft_bot = MinecraftBot()
        mc_bot = minecraft_bot
        bot = mc_bot.get_bot()
        start_time = mc_bot.get_start_time()
        blocks = mc_bot.blocks
        entity = mc_bot.entities

        # 创建时间表管理器
        timetable_manager = TimetableManager()

        # 注册事件处理器
        register_event_handlers()

        # 配置调度任务
        setup_scheduled_tasks()

        logger.info('机器人初始化完成')

    except Exception as e:
        logger.error(f'机器人初始化失败: {e}')
        raise


def setup_scheduled_tasks():
    """设置定时任务"""
    try:
        # 添加定时任务
        timetable_manager.scheduler.add_job(
            GameUtils.check_online_status,
            'cron',
            hour='*',
            id='check_players'
        )


        timetable_manager.scheduler.add_job(
            MessageManager.check_bot_status,
            'cron',
            minute='*',
            id='check_online_status'
        )

        timetable_manager.scheduler.add_job(
            MessageManager.send_pending_messages,
            'cron',
            second='*',
            id='send_pending_messages',
            misfire_grace_time=1,
            max_instances=1
        )

        # 可选的传送任务（注释掉，可根据需要启用）
        # timetable_manager.scheduler.add_job(
        #     GameUtils.transport_to_iron_farm,
        #     'cron',
        #     hour=1,
        #     id='to_iron'
        # )
        # 
        # timetable_manager.scheduler.add_job(
        #     GameUtils.transport_to_main,
        #     'cron',
        #     hour=14,
        #     id='to_main'
        # )
        # 
        # timetable_manager.scheduler.add_job(
        #     GameUtils.transport_to_community,
        #     'cron',
        #     hour=7,
        #     id='to_community'
        # )
        # 
        # timetable_manager.scheduler.add_job(
        #     GameUtils.auto_sleep,
        #     'cron',
        #     minute='*',
        #     id='auto_sleep'
        # )

        logger.info('定时任务配置完成')

    except Exception as e:
        logger.error(f'定时任务配置失败: {e}')
        raise


def main():
    """主函数"""
    try:
        logger.info('正在启动Minecraft机器人...')

        # 初始化机器人
        initialize_bot()

        # 启动调度器
        timetable_manager.scheduler.start()

    except KeyboardInterrupt:
        logger.info('收到中断信号，正在关闭程序...')
    except Exception as e:
        logger.error(f'程序运行出错: {e}')
    finally:
        # 清理资源
        cleanup()


def cleanup():
    """清理资源"""
    try:
        logger.info('正在清理资源...')

        # 关闭数据库连接
        if db_manager:
            db_manager.close()

        # 停止调度器
        if timetable_manager and timetable_manager.scheduler.running:
            timetable_manager.scheduler.shutdown()

        logger.info('程序结束...特征编码：naisncxai9euqwuenasod')

    except Exception as e:
        logger.error(f'清理资源时出错: {e}')
    finally:
        # 关闭日志系统
        logging.shutdown()


if __name__ == '__main__':
    main()
