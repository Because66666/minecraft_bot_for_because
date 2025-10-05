# Dashboard Handle 数据库存储说明文档

## 概述

`dashboard_handle.py` 是一个仪表板数据处理模块，负责处理每日仪表板数据，包括在线人数变化曲线和玩家发言统计。该模块通过分析历史数据，生成每日汇总报告并存储到数据库中。

## 涉及的数据库表

### 1. DashboardDaily（仪表板每日数据表）

**表名**: `dashboard_daily`

**用途**: 存储每日处理后的仪表板汇总数据

**字段结构**:
```sql
CREATE TABLE dashboard_daily (
    id INTEGER PRIMARY KEY,
    date DATETIME UNIQUE NOT NULL,           -- 数据日期
    online_curve_data JSON,                  -- 在线人数变化曲线数据
    player_chat_stats JSON,                  -- 玩家发言次数统计
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP  -- 记录创建时间
);
```

**字段说明**:
- `id`: 主键，自增整数
- `date`: 数据日期，唯一约束，表示该记录对应的日期
- `online_curve_data`: JSON格式，存储在线人数变化曲线数据
- `player_chat_stats`: JSON格式，存储玩家发言统计数据
- `created_at`: 记录创建时间，默认为当前时间

### 2. RIALogInfo（聊天日志表）

**表名**: `RIA_log_info`

**用途**: 存储玩家聊天记录，作为生成发言统计的数据源

**字段结构**:
```sql
CREATE TABLE RIA_log_info (
    id INTEGER PRIMARY KEY,
    who_string TEXT,                         -- 玩家名字
    log_string TEXT,                         -- 聊天内容
    t DATETIME                               -- 记录时间
);
```

**在dashboard_handle中的使用**:
- 用于统计指定日期内每个玩家的发言次数
- 生成玩家活跃度排行榜
- 计算总发言数和平均发言数

### 3. RIAOnline（在线玩家记录表）

**表名**: `RIA_online`

**用途**: 存储玩家在线状态记录，作为生成在线人数曲线的数据源

**字段结构**:
```sql
CREATE TABLE RIA_online (
    id INTEGER PRIMARY KEY,
    player_name TEXT,                        -- 玩家名字
    DataInfo JSON,                           -- 数据信息
    t DATETIME                               -- 记录时间
);
```

**在dashboard_handle中的使用**:
- 用于统计指定日期内每小时的在线人数
- 生成24小时在线人数变化曲线
- 计算峰值在线人数和峰值时间
- 统计当日独特在线玩家总数

## 数据处理流程

### 1. 数据收集阶段

```python
def process_yesterday_data(self, target_date: Optional[datetime.date] = None) -> bool:
```

**流程**:
1. 确定目标日期（默认为昨天）
2. 检查该日期是否已经处理过（避免重复处理）
3. 从源表收集原始数据
4. 处理并生成汇总数据
5. 存储到 `dashboard_daily` 表

### 2. 在线人数曲线数据处理

```python
def _get_online_curve_data(self, target_date: datetime.date) -> Dict:
```

**处理逻辑**:
1. 查询指定日期的所有在线记录（`RIA_online` 表）
2. 按小时分组统计在线玩家
3. 生成24小时的数据点
4. 计算峰值时间和峰值人数
5. 统计当日独特玩家总数

**输出数据格式**:
```json
{
    "hours": [0, 1, 2, ..., 23],
    "online_counts": [5, 8, 12, ..., 3],
    "peak_hour": 14,
    "peak_count": 25,
    "total_unique_players": 45
}
```

### 3. 玩家发言统计处理

```python
def _get_player_chat_stats(self, target_date: datetime.date) -> Dict:
```

**处理逻辑**:
1. 查询指定日期的所有聊天记录（`RIA_log_info` 表）
2. 统计每个玩家的发言次数
3. 排序获取最活跃的前10名玩家
4. 计算总发言数和平均发言数

**输出数据格式**:
```json
{
    "total_messages": 156,
    "total_players": 12,
    "top_players": [
        {"player_name": "Player1", "message_count": 25},
        {"player_name": "Player2", "message_count": 18}
    ],
    "all_players": {"Player1": 25, "Player2": 18, ...},
    "average_messages_per_player": 13.0
}
```

## 数据存储特点

### 1. 数据去重机制

- 通过 `_is_date_processed()` 方法检查日期是否已处理
- `dashboard_daily.date` 字段设置唯一约束
- 避免重复处理同一天的数据

### 2. 事务安全性

- 使用 `DatabaseManager` 的 `add_and_commit()` 方法
- 包含重试机制和事务回滚
- 独立的 Session 管理避免冲突

### 3. 错误处理

- 每个数据处理方法都包含异常处理
- 失败时返回默认值，确保系统稳定性
- 详细的错误日志记录

## 数据查询接口

### 1. 获取仪表板数据

```python
def get_dashboard_data(self, target_date: Optional[datetime.date] = None) -> Optional[Dict]:
```

**功能**: 获取指定日期的已处理仪表板数据

### 2. 批量处理

```python
def process_multiple_days(self, start_date: datetime.date, end_date: datetime.date) -> int:
```

**功能**: 批量处理多天的数据，适用于历史数据补充

### 3. 数据清理

```python
def cleanup_old_data(self, days_to_keep: int = 30) -> int:
```

**功能**: 清理超过指定天数的旧数据，节省存储空间

## 使用示例

### 基本使用

```python
from functions.square.dashboard_handle import dashboard_handler

# 处理昨天的数据
success = dashboard_handler.process_yesterday_data()

# 获取昨天的仪表板数据
yesterday = datetime.date.today() - datetime.timedelta(days=1)
data = dashboard_handler.get_dashboard_data(yesterday)

if data:
    print(f"峰值在线人数: {data['online_curve_data']['peak_count']}")
    print(f"总发言数: {data['player_chat_stats']['total_messages']}")
```

### 批量处理历史数据

```python
import datetime

# 处理过去7天的数据
end_date = datetime.date.today() - datetime.timedelta(days=1)
start_date = end_date - datetime.timedelta(days=6)

processed_count = dashboard_handler.process_multiple_days(start_date, end_date)
print(f"成功处理了 {processed_count} 天的数据")
```

### 数据维护

```python
# 清理30天前的旧数据
deleted_count = dashboard_handler.cleanup_old_data(days_to_keep=30)
print(f"清理了 {deleted_count} 条旧记录")
```

## 注意事项

1. **数据依赖性**: 确保 `RIA_log_info` 和 `RIA_online` 表有足够的历史数据
2. **时区处理**: 所有时间处理基于系统本地时区
3. **性能考虑**: 大量历史数据处理时建议分批进行
4. **数据完整性**: 建议定期检查源数据的完整性
5. **存储空间**: 定期清理旧数据以节省存储空间

## 数据库维护

### 创建表结构

```python
from functions.database import create_tables
create_tables()  # 创建所有必要的表结构
```

### 索引建议

为提高查询性能，建议在以下字段上创建索引：

```sql
-- RIA_log_info 表索引
CREATE INDEX idx_ria_log_info_t ON RIA_log_info(t);
CREATE INDEX idx_ria_log_info_who ON RIA_log_info(who_string);

-- RIA_online 表索引  
CREATE INDEX idx_ria_online_t ON RIA_online(t);
CREATE INDEX idx_ria_online_player ON RIA_online(player_name);

-- dashboard_daily 表索引
CREATE INDEX idx_dashboard_daily_date ON dashboard_daily(date);
```

这些索引将显著提高数据查询和处理的性能。