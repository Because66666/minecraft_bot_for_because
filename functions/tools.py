"""工具模块

提供Flask应用、Socket.IO、头像下载等功能
"""

import threading
import time
import requests
import json
import os
from flask import Flask
from flask_socketio import SocketIO, emit
from sqlalchemy import text
from .config import config
from .database import (
    db, db_manager, db_service, RIALogInfo, RIALogCommon,
    RIAPlayers, engine
)
from .utils import FileUtils

# 初始化Flask应用
import os
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent.parent
template_dir = project_root / 'templates'
static_dir = project_root / 'static'

app = Flask(__name__, 
           template_folder=str(template_dir),
           static_folder=str(static_dir))
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SESSION_COOKIE_NAME'] = 'mc_bot_session'

# 初始化Flask-SQLAlchemy
db.init_app(app)

# 初始化Socket.IO
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    ping_timeout=config.PING_TIMEOUT,
    ping_interval=config.PING_INTERVAL,
    async_mode='threading'  # Windows环境下使用threading模式避免gevent-websocket问题
)


# 数据库模型已移动到database.py模块


class AvatarDownloader:
    """Minecraft玩家头像下载器
    
    负责从Mojang API获取玩家UUID，然后从Crafatar下载头像
    """
    
    def __init__(self):
        self.name_queue = []  # 待处理的玩家名队列
        self.id_queue = []    # 待下载头像的ID队列
        self.downloaded_names = []  # 已下载的玩家名列表
        self._running = False
    
    def add_player(self, player_name: str) -> None:
        """添加玩家到下载队列
        
        Args:
            player_name: 玩家名字
        """
        if player_name not in self.downloaded_names and player_name not in self.name_queue:
            self.name_queue.append(player_name)
    
    def _get_player_uuid(self) -> None:
        """获取玩家UUID的工作线程"""
        while self._running:
            if not self.name_queue:
                time.sleep(1)
                continue
            
            player_name = self.name_queue.pop(0)
            if player_name in self.downloaded_names:
                continue
            
            try:
                response = requests.get(
                    f'https://api.mojang.com/users/profiles/minecraft/{player_name}',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'id' in data:
                        self.id_queue.append({
                            'id': data['id'],
                            'name': player_name
                        })
                        self.downloaded_names.append(player_name)
            except Exception as e:
                print(f"获取玩家 {player_name} 的UUID失败: {e}")
            finally:
                time.sleep(1)  # 避免请求过于频繁
    
    def _download_avatar(self) -> None:
        """下载头像的工作线程"""
        while self._running:
            if not self.id_queue:
                time.sleep(1)
                continue
            
            player_data = self.id_queue.pop(0)
            player_id = player_data['id']
            player_name = player_data['name']
            
            try:
                response = requests.get(
                    f'https://crafatar.com/avatars/{player_id}',
                    timeout=10
                )
                if response.status_code == 200:
                    # 确保目录存在
                    os.makedirs(config.STATIC_IMG_PATH, exist_ok=True)
                    
                    avatar_path = os.path.join(config.STATIC_IMG_PATH, f'{player_name}.png')
                    with open(avatar_path, 'wb') as f:
                        f.write(response.content)
                    print(f"成功下载玩家 {player_name} 的头像")
            except Exception as e:
                print(f"下载玩家 {player_name} 的头像失败: {e}")
            finally:
                time.sleep(1)  # 避免请求过于频繁
    
    def start(self) -> None:
        """启动头像下载服务"""
        if self._running:
            return
        
        self._running = True
        uuid_thread = threading.Thread(target=self._get_player_uuid, daemon=True)
        avatar_thread = threading.Thread(target=self._download_avatar, daemon=True)
        
        uuid_thread.start()
        avatar_thread.start()
        
        print("头像下载服务已启动")
    
    def stop(self) -> None:
        """停止头像下载服务"""
        self._running = False
        print("头像下载服务已停止")


# 创建头像下载器实例
avatar_downloader = AvatarDownloader()

# 工具函数已移动到utils.py模块


@socketio.on('data_get')
def handle_data_get(max_id):
    """处理获取聊天数据的请求
    
    Args:
        max_id: 最大ID，用于获取新数据
    """
    if not isinstance(max_id, int):
        emit('error', {'message': 'max_id error!'})
        return

    try:
        # 获取新的聊天日志
        logs = (db_manager.session.query(RIALogInfo)
                .filter(RIALogInfo.id > max_id)
                .order_by(RIALogInfo.id.desc())
                .limit(10)
                .all())

        results = []
        for log in reversed(logs):
            try:
                # 检查log对象是否有效
                if not log or not hasattr(log, 'who_string') or log.who_string is None:
                    print(f"警告: 发现无效log对象，跳过处理")
                    continue
                
                # 检查头像是否存在，如果不存在则添加到下载队列
                if not FileUtils.check_player_avatar_exists(log.who_string):
                    avatar_downloader.add_player(log.who_string)
                    img_path = 'default.jpg'
                else:
                    img_path = FileUtils.get_player_avatar_path(log.who_string)
                
                result = log.to_dict()
                result['img_path'] = img_path
                results.append(result)
            except Exception as e:
                print(f"处理log对象失败: {e}, log信息: {getattr(log, 'id', 'unknown')}")
                continue

        if results:
            json_data = json.dumps(results)
            new_id = max(result['id'] for result in results)
            emit('message', {'data': json_data, 'new_id': new_id}, broadcast=True)
        else:
            emit('no_new_data', {'message': 'No new data'})
            
    except Exception as e:
        print(f"处理数据获取请求失败: {e}")
        emit('error', {'message': 'Internal server error'})


@socketio.on('data_get_com')
def handle_common_data_get(max_id):
    """处理获取通用日志数据的请求
    
    Args:
        max_id: 最大ID，用于获取新数据
    """
    if not isinstance(max_id, int):
        emit('error', {'message': 'max_id error!'})
        return

    try:
        # 获取新的通用日志
        logs = (db_manager.session.query(RIALogCommon)
                .filter(RIALogCommon.id > max_id)
                .order_by(RIALogCommon.id.desc())
                .limit(10)
                .all())

        results = []
        for log in reversed(logs):
            result = log.to_dict()
            results.append(result)

        if results:
            json_data = json.dumps(results)
            new_id = max(result['id'] for result in results)
            emit('message_com', {'data': json_data, 'new_id': new_id}, broadcast=True)
        else:
            emit('no_new_data', {'message': 'No new data'})
            
    except Exception as e:
        print(f"处理通用日志获取请求失败: {e}")
        emit('error', {'message': 'Internal server error'})


@socketio.on('update_old_log')
def handle_update_old_log(min_id):
    """处理获取历史聊天日志的请求
    
    Args:
        min_id: 最小ID，用于获取历史数据
    """
    if not isinstance(min_id, int):
        emit('error', {'message': 'min_id error!'})
        return

    try:
        # 获取历史聊天日志
        logs = (db_manager.session.query(RIALogInfo)
                .filter(RIALogInfo.id < min_id)
                .order_by(RIALogInfo.id.desc())
                .limit(10)
                .all())

        results = []
        for log in logs:
            try:
                # 检查log对象是否有效
                if not log or not hasattr(log, 'who_string') or log.who_string is None:
                    print(f"警告: 发现无效log对象，跳过处理")
                    continue
                
                # 检查头像是否存在
                if not FileUtils.check_player_avatar_exists(log.who_string):
                    avatar_downloader.add_player(log.who_string)
                    img_path = 'default.jpg'
                else:
                    img_path = FileUtils.get_player_avatar_path(log.who_string)
                
                result = log.to_dict()
                result['img_path'] = img_path
                results.append(result)
            except Exception as e:
                print(f"处理历史log对象失败: {e}, log信息: {getattr(log, 'id', 'unknown')}")
                continue

        if results:
            new_id = min(result['id'] for result in results)
            json_data = json.dumps(results)
            emit('update_old_log', {'data': json_data, 'new_id': new_id}, broadcast=True)
        else:
            emit('no_new_data', {'message': 'No new data'})
            
    except Exception as e:
        print(f"处理历史日志获取请求失败: {e}")
        emit('error', {'message': 'Internal server error'})


@socketio.on('update_old_log_com')
def handle_update_old_log_common(min_id):
    """处理获取历史通用日志的请求
    
    Args:
        min_id: 最小ID，用于获取历史数据
    """
    if not isinstance(min_id, int):
        emit('error', {'message': 'min_id error!'})
        return

    try:
        # 获取历史通用日志
        logs = (db_manager.session.query(RIALogCommon)
                .filter(RIALogCommon.id < min_id)
                .order_by(RIALogCommon.id.desc())
                .limit(10)
                .all())

        results = []
        for log in logs:
            result = log.to_dict()
            results.append(result)

        if results:
            new_id = min(result['id'] for result in results)
            json_data = json.dumps(results)
            emit('update_old_log_com', {'data': json_data, 'new_id': new_id}, broadcast=True)
        else:
            emit('no_new_data', {'message': 'No new data'})
            
    except Exception as e:
        print(f"处理历史通用日志获取请求失败: {e}")
        emit('error', {'message': 'Internal server error'})


@socketio.on('connect')
def handle_connect():
    # print('Client connected')
    emit('response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect')
def handle_disconnect():
    # print('Client disconnected')
    pass
