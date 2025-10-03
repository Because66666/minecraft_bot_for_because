"""数据库操作模块

封装常用的数据库操作和模型定义
"""

import datetime
import threading
from typing import List, Optional
from sqlalchemy import Column, DateTime, Text, Integer, JSON, create_engine, desc
from sqlalchemy.orm import declarative_base, Session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from .config import config

# 数据库基类和实例
Base = declarative_base()
db = SQLAlchemy()

# 数据库引擎 - 添加连接池和超时配置
engine = create_engine(
    config.DATABASE_URI,
    pool_timeout=20,
    pool_recycle=-1,
    pool_pre_ping=True,
    connect_args={
        'timeout': 30,
        'check_same_thread': False
    }
)



class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.session = Session(bind=engine)
        
        # 数据库连接状态检查
        self.ria_db_exists = self._check_database_connection(engine)
    
    def _check_database_connection(self, engine):
        """检查数据库连接状态"""
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            return True
        except Exception:
            return False
    
    def add_and_commit(self, obj):
        """添加对象到数据库并提交，包含重试机制和事务安全性"""
        import time
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                # 创建新的session来避免事务冲突
                new_session = Session(bind=engine)
                try:
                    # 使用 merge 替代 add 来避免 SAWarning
                    merged_obj = new_session.merge(obj)
                    new_session.commit()
                    return merged_obj  # 返回合并后的对象
                finally:
                    new_session.close()
                    
            except Exception as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    print(f"数据库锁定，第 {attempt + 1} 次重试...")
                    time.sleep(retry_delay * (2 ** attempt))  # 指数退避
                    continue
                else:
                    print(f"数据库操作失败: {e}")
                    raise
    
    def close_sessions(self):
        """关闭所有数据库会话"""
        try:
            self.session.close()
        except Exception as e:
            print(f"关闭数据库会话时出错: {e}")
    
    def close(self):
        """清理资源，关闭数据库连接"""
        self.close_sessions()


# 数据库模型定义
class RIALogInfo(Base):
    """RIA聊天日志模型"""
    __tablename__ = 'RIA_log_info'
    
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    who_string = Column(Text, comment='玩家名字')
    log_string = Column(Text, comment='聊天内容')
    t = Column(DateTime, comment='记录时间')
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'who_string': self.who_string,
            'log_string': self.log_string,
            't': self.t.strftime("%H:%M") if self.t else None
        }


class RIALogCommon(Base):
    """RIA通用日志模型"""
    __tablename__ = 'RIA_log_common'
    
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    log_string = Column(Text, comment='日志内容')
    t = Column(DateTime, comment='记录时间')
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'log_string': self.log_string,
            't': self.t.strftime("%H:%M") if self.t else None
        }


class RIAMsgSend(Base):
    """RIA消息发送队列模型"""
    __tablename__ = 'RIA_msg_send'
    
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    text = Column(Text, comment='要发送的内容')



class RIAOnline(Base):
    """RIA在线人员记录模型"""
    __tablename__ = 'RIA_online'
    
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    player_name = Column(Text, comment='玩家名字')
    DataInfo = Column(JSON, comment='数据信息')
    t = Column(DateTime, comment='记录时间')



class UserRecord(Base, UserMixin):
    """用户记录模型"""
    __tablename__ = 'user_record'
    
    id = Column(Integer, primary_key=True)
    username = Column(Text, comment='用户名')


class RIAPlayers(Base, UserMixin):
    """RIA玩家模型"""
    __tablename__ = 'ria_players'
    
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    player_name = Column(Text, comment='玩家名字')
    email = Column(Text, comment='邮箱地址')


class DatabaseService:
    """数据库服务类"""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.online_player_set = set()
        self.lock = threading.Lock()
    
    def add_chat_log(self, username: str, message: str) -> None:
        """添加聊天日志
        
        Args:
            username: 用户名
            message: 消息内容
        """
        try:
            log = RIALogInfo(
                who_string=username,
                log_string=message,
                t=datetime.datetime.now()
            )
            # 使用DatabaseManager的安全方法
            self.db_manager.add_and_commit(log)
        except Exception as e:
            print(f"添加聊天日志失败: {e}")
    
    def add_common_log(self, message: str) -> None:
        """添加通用日志
        
        Args:
            message: 日志消息
        """
        try:
            log = RIALogCommon(
                log_string=message,
                t=datetime.datetime.now()
            )
            # 使用DatabaseManager的安全方法
            self.db_manager.add_and_commit(log)
        except Exception as e:
            print(f"添加通用日志失败: {e}")
    
    def get_recent_chat_logs(self, limit: int = 20) -> List[RIALogInfo]:
        """获取最近的聊天日志
        
        Args:
            limit: 限制数量
            
        Returns:
            聊天日志列表
        """
        try:
            # 使用独立session进行查询
            from sqlalchemy.orm import Session
            
            temp_session = Session(bind=engine)
            try:
                return (temp_session.query(RIALogInfo)
                       .order_by(desc(RIALogInfo.t))
                       .limit(limit)
                       .all())
            finally:
                temp_session.close()
        except Exception as e:
            print(f"获取聊天日志失败: {e}")
            return []
    
    def get_recent_common_logs(self, limit: int = 20) -> List[RIALogCommon]:
        """获取最近的通用日志
        
        Args:
            limit: 限制数量
            
        Returns:
            通用日志列表
        """
        try:
            # 使用独立session进行查询
            from sqlalchemy.orm import Session
            
            temp_session = Session(bind=engine)
            try:
                return (temp_session.query(RIALogCommon)
                       .order_by(desc(RIALogCommon.t))
                       .limit(limit)
                       .all())
            finally:
                temp_session.close()
        except Exception as e:
            print(f"获取通用日志失败: {e}")
            return []
    
    def add_message_to_send_queue(self, text: str) -> None:
        """添加消息到发送队列
        
        Args:
            text: 要发送的文本
        """
        try:
            msg = RIAMsgSend(text=text)
            # 使用DatabaseManager的安全方法
            self.db_manager.add_and_commit(msg)
        except Exception as e:
            print(f"添加发送消息失败: {e}")
    

    def record_online_player(self, player_name: str, data_info: dict) -> None:
        """记录在线玩家信息
        
        Args:
            player_name: 玩家名字
            data_info: 玩家数据信息
        """
        try:
            online_record = RIAOnline(
                player_name=player_name,
                DataInfo=data_info,
                t=datetime.datetime.now()
            )
            self.db_manager.add_and_commit(online_record)
        except Exception as e:
            print(f"记录在线玩家失败: {e}")
    
    def get_pending_messages(self) -> List[RIAMsgSend]:
        """获取所有待发送的消息
        
        Returns:
            待发送消息列表
        """
        try:
            from sqlalchemy.orm import Session
            
            temp_session = Session(bind=engine)
            try:
                return temp_session.query(RIAMsgSend).all()
            finally:
                temp_session.close()
        except Exception as e:
            print(f"获取待发送消息失败: {e}")
            return []
    
    def delete_message(self, message_id: int) -> bool:
        """删除指定的消息
        
        Args:
            message_id: 消息ID
            
        Returns:
            是否删除成功
        """
        try:
            from sqlalchemy.orm import Session
            
            temp_session = Session(bind=engine)
            try:
                message = temp_session.query(RIAMsgSend).filter(RIAMsgSend.id == message_id).first()
                if message:
                    temp_session.delete(message)
                    temp_session.commit()
                    return True
                return False
            finally:
                temp_session.close()
        except Exception as e:
            print(f"删除消息失败: {e}")
            return False


# 创建数据库表
def create_tables():
    """创建所有数据库表"""
    Base.metadata.create_all(engine)
    print("数据库表创建完成")


# 全局数据库管理器实例
db_manager = DatabaseManager()
db_service = DatabaseService(db_manager)