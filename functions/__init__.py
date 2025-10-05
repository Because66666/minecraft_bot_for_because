"""Functions module for MC Bot.

This module provides centralized access to all core functionality modules.
"""

# Configuration management
from .config import config

# Database management
from .database import (
    DatabaseManager,
    RIAOnline, 
    RIALogInfo, 
    RIAMsgSend, 
    RIALogCommon,
    RIAPlayers,
    WEBBannedIPs,
    create_tables,
    db_service
)

# Utility functions
from .utils import GeometryUtils, SystemUtils, EasterEggManager, EmailService

# AI communication
from .communicate_by_ai import main_ai

# Keyword processing
from .keyword_in_communication import keys, keys_set

# KOOK API integration
from .kook_api import get_kook_api_instance, send_kook_message, send_kook_notification

# Logging utilities
from .my_logger import logger, logger_com, logger_ai, logger_send

# Tools and Flask app
from .tools import app, socketio, avatar_downloader

# Timetable information
from .timetable_info import place_timetable, activity_timetable, config as timetable_config

# 广场的方法函数
from .square.dashboard_handle import dashboard_handler

__all__ = [
    # Configuration
    'config',
    
    # Database
    'DatabaseManager',
    'RIAOnline',
    'RIALogInfo',
    'RIAMsgSend',
    'RIALogCommon',
    'RIAPlayers',
    'WEBBannedIPs',
    'create_tables',
    'db_service',
    
    # Utils
    'GeometryUtils',
    'SystemUtils', 
    'EasterEggManager',
    'EmailService',
    
    # AI
    'main_ai',
    
    # Keywords
    'keys',
    'keys_set',
    
    # KOOK API
    'get_kook_api_instance',
    'send_kook_message',
    'send_kook_notification',
    
    # Logging
    'logger',
    'logger_com',
    'logger_ai',
    'logger_send',
    
    # Tools
    'app',
    'socketio',
    'avatar_downloader',
    
    # Timetable
    'place_timetable',
    'activity_timetable',
    'timetable_config',
    
    # Dashboard
    'dashboard_handler',

]