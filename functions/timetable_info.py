"""时间表信息模块

提供时间表相关的配置和数据
"""

import datetime

# 地点时间表配置 - 使用datetime.time对象
place_timetable = {
    "main": datetime.time(8, 0),  # 8:00
    # "community": datetime.time(12, 0),  # 12:00
    # "gong_jian": datetime.time(18, 0),  # 18:00
}

# 地点映射表
place_map_2 = {
    "main": '云岫-外交公馆',
    "community": '云岫-社团中心',
    "iron": '云岫-刷铁机',
    "new": 'expo7',
    "gong_jian":"大坑共建"
}


# 活动时间表配置
activity_timetable = {
    "default": {
        "name": "默认活动",
        "schedule": []
    }
}

# 其他时间表相关配置
config = {
    "timezone": "Asia/Shanghai",
    "default_duration": 60  # 默认活动持续时间（分钟）
}