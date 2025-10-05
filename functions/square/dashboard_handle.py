"""仪表板数据处理模块

处理每日仪表板数据，包括在线人数变化曲线和玩家发言统计
"""

import datetime
import sys
import os
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    # 尝试相对导入（当作为模块导入时）
    from ..database import (
        engine, RIALogInfo, RIAOnline, DashboardDaily, 
        DatabaseManager, DatabaseService
    )
except ImportError:
    # 如果相对导入失败，使用绝对导入（当直接运行时）
    from functions.database import (
        engine, RIALogInfo, RIAOnline, DashboardDaily, 
        DatabaseManager, DatabaseService
    )


class DashboardHandler:
    """仪表板数据处理器"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.db_service = DatabaseService(self.db_manager)
    
    def process_yesterday_data(self, target_date: Optional[datetime.date] = None) -> bool:
        """处理昨日数据并存储到dashboard_daily表
        
        Args:
            target_date: 目标日期，默认为昨天
            
        Returns:
            是否处理成功
        """
        if target_date is None:
            target_date = datetime.date.today() - datetime.timedelta(days=1)
        
        try:
            # 检查是否已经处理过该日期的数据
            if self._is_date_processed(target_date):
                print(f"日期 {target_date} 的数据已经处理过")
                return True
            
            # 获取昨日在线人数变化数据
            online_curve_data = self._get_online_curve_data(target_date)
            
            # 获取昨日玩家发言统计
            player_chat_stats = self._get_player_chat_stats(target_date)
            
            # 创建仪表板记录
            dashboard_record = DashboardDaily(
                date=datetime.datetime.combine(target_date, datetime.time.min),
                online_curve_data=online_curve_data,
                player_chat_stats=player_chat_stats
            )
            
            # 保存到数据库
            self.db_manager.add_and_commit(dashboard_record)
            
            print(f"成功处理日期 {target_date} 的仪表板数据")
            return True
            
        except Exception as e:
            print(f"处理昨日数据失败: {e}")
            return False
    
    def _is_date_processed(self, target_date: datetime.date) -> bool:
        """检查指定日期是否已经处理过
        
        Args:
            target_date: 目标日期
            
        Returns:
            是否已处理
        """
        try:
            temp_session = Session(bind=engine)
            try:
                start_datetime = datetime.datetime.combine(target_date, datetime.time.min)
                end_datetime = datetime.datetime.combine(target_date, datetime.time.max)
                
                existing_record = temp_session.query(DashboardDaily).filter(
                    and_(
                        DashboardDaily.date >= start_datetime,
                        DashboardDaily.date <= end_datetime
                    )
                ).first()
                
                return existing_record is not None
            finally:
                temp_session.close()
        except Exception as e:
            print(f"检查日期处理状态失败: {e}")
            return False
    
    def _get_online_curve_data(self, target_date: datetime.date) -> Dict:
        """获取指定日期的在线人数变化曲线数据
        
        Args:
            target_date: 目标日期
            
        Returns:
            在线人数变化数据
        """
        try:
            temp_session = Session(bind=engine)
            try:
                # 设置时间范围
                start_datetime = datetime.datetime.combine(target_date, datetime.time.min)
                end_datetime = datetime.datetime.combine(target_date, datetime.time.max)
                
                # 查询该日期的在线记录
                online_records = temp_session.query(RIAOnline).filter(
                    and_(
                        RIAOnline.t >= start_datetime,
                        RIAOnline.t <= end_datetime
                    )
                ).order_by(RIAOnline.t).all()
                
                # 按小时统计在线人数
                hourly_stats = defaultdict(set)
                
                for record in online_records:
                    hour = record.t.hour
                    if record.player_name:
                        hourly_stats[hour].add(record.player_name)
                
                # 构建24小时的数据点
                curve_data = {
                    'hours': list(range(24)),
                    'online_counts': [],
                    'peak_hour': 0,
                    'peak_count': 0,
                    'total_unique_players': len(set(
                        record.player_name for record in online_records 
                        if record.player_name
                    ))
                }
                
                max_count = 0
                peak_hour = 0
                
                for hour in range(24):
                    count = len(hourly_stats[hour])
                    curve_data['online_counts'].append(count)
                    
                    if count > max_count:
                        max_count = count
                        peak_hour = hour
                
                curve_data['peak_hour'] = peak_hour
                curve_data['peak_count'] = max_count
                
                return curve_data
                
            finally:
                temp_session.close()
                
        except Exception as e:
            print(f"获取在线人数变化数据失败: {e}")
            return {
                'hours': list(range(24)),
                'online_counts': [0] * 24,
                'peak_hour': 0,
                'peak_count': 0,
                'total_unique_players': 0
            }
    
    def _get_player_chat_stats(self, target_date: datetime.date) -> Dict:
        """获取指定日期的玩家发言统计
        
        Args:
            target_date: 目标日期
            
        Returns:
            玩家发言统计数据
        """
        try:
            temp_session = Session(bind=engine)
            try:
                # 设置时间范围
                start_datetime = datetime.datetime.combine(target_date, datetime.time.min)
                end_datetime = datetime.datetime.combine(target_date, datetime.time.max)
                
                # 查询该日期的聊天记录
                chat_records = temp_session.query(RIALogInfo).filter(
                    and_(
                        RIALogInfo.t >= start_datetime,
                        RIALogInfo.t <= end_datetime,
                        RIALogInfo.who_string.isnot(None)
                    )
                ).all()
                
                # 统计每个玩家的发言次数
                player_stats = defaultdict(int)
                total_messages = 0
                
                for record in chat_records:
                    if record.who_string and record.who_string.strip():
                        player_stats[record.who_string] += 1
                        total_messages += 1
                
                # 排序并获取前10名最活跃的玩家
                sorted_players = sorted(
                    player_stats.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
                
                top_players = sorted_players[:10]
                
                # 构建统计数据
                chat_stats = {
                    'total_messages': total_messages,
                    'total_players': len(player_stats),
                    'top_players': [
                        {'player_name': player, 'message_count': count}
                        for player, count in top_players
                    ],
                    'all_players': dict(player_stats),
                    'average_messages_per_player': (
                        total_messages / len(player_stats) 
                        if len(player_stats) > 0 else 0
                    )
                }
                
                return chat_stats
                
            finally:
                temp_session.close()
                
        except Exception as e:
            print(f"获取玩家发言统计失败: {e}")
            return {
                'total_messages': 0,
                'total_players': 0,
                'top_players': [],
                'all_players': {},
                'average_messages_per_player': 0
            }
    
    def get_dashboard_data(self, target_date: Optional[datetime.date] = None) -> Optional[Dict]:
        """获取指定日期的仪表板数据
        
        Args:
            target_date: 目标日期，默认为昨天
            
        Returns:
            仪表板数据或None
        """
        if target_date is None:
            target_date = datetime.date.today() - datetime.timedelta(days=1)
        
        try:
            temp_session = Session(bind=engine)
            try:
                start_datetime = datetime.datetime.combine(target_date, datetime.time.min)
                end_datetime = datetime.datetime.combine(target_date, datetime.time.max)
                
                dashboard_record = temp_session.query(DashboardDaily).filter(
                    and_(
                        DashboardDaily.date >= start_datetime,
                        DashboardDaily.date <= end_datetime
                    )
                ).first()
                
                if dashboard_record:
                    return dashboard_record.to_dict()
                else:
                    return None
                    
            finally:
                temp_session.close()
                
        except Exception as e:
            print(f"获取仪表板数据失败: {e}")
            return None
    
    def process_multiple_days(self, start_date: datetime.date, end_date: datetime.date) -> int:
        """批量处理多天的数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            成功处理的天数
        """
        success_count = 0
        current_date = start_date
        
        while current_date <= end_date:
            if self.process_yesterday_data(current_date):
                success_count += 1
            current_date += datetime.timedelta(days=1)
        
        print(f"批量处理完成，成功处理 {success_count} 天的数据")
        return success_count
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """清理旧的仪表板数据
        
        Args:
            days_to_keep: 保留的天数
            
        Returns:
            删除的记录数
        """
        try:
            temp_session = Session(bind=engine)
            try:
                cutoff_date = datetime.date.today() - datetime.timedelta(days=days_to_keep)
                cutoff_datetime = datetime.datetime.combine(cutoff_date, datetime.time.min)
                
                old_records = temp_session.query(DashboardDaily).filter(
                    DashboardDaily.date < cutoff_datetime
                ).all()
                
                count = len(old_records)
                
                for record in old_records:
                    temp_session.delete(record)
                
                temp_session.commit()
                
                print(f"清理了 {count} 条旧的仪表板数据")
                return count
                
            finally:
                temp_session.close()
                
        except Exception as e:
            print(f"清理旧数据失败: {e}")
            return 0


# 创建全局实例
dashboard_handler = DashboardHandler()


def main():
    """主函数，用于测试和手动执行"""
    print("开始处理昨日仪表板数据...")
    
    # 处理昨天的数据
    success = dashboard_handler.process_yesterday_data()
    
    if success:
        print("昨日数据处理成功")
        
        # 获取并显示处理结果
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        data = dashboard_handler.get_dashboard_data(yesterday)
        
        if data:
            print(f"数据日期: {data['date']}")
            print(f"在线人数峰值: {data['online_curve_data']['peak_count']} 人 (在 {data['online_curve_data']['peak_hour']}:00)")
            print(f"总发言数: {data['player_chat_stats']['total_messages']}")
            print(f"活跃玩家数: {data['player_chat_stats']['total_players']}")
    else:
        print("昨日数据处理失败")


if __name__ == "__main__":
    main()