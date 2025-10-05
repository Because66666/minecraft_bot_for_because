"""Web服务器模块

提供日志展示、用户认证和消息发送功能的Flask Web应用
"""
import os
import random
import time
from datetime import datetime, timedelta , date
from typing import Dict, Any, Tuple, List, Optional
from functools import wraps

from flask import config, request, render_template, jsonify, redirect, url_for, abort
from flask_login import (
    LoginManager, login_user, current_user, 
    login_required, logout_user, UserMixin
)
# SocketIO实例从functions模块导入
from sqlalchemy import desc, text
from dotenv import load_dotenv

from functions import (
    DatabaseManager, RIALogInfo, RIALogCommon, 
    EmailService,
    RIAMsgSend, RIAPlayers, WEBBannedIPs,
    SystemUtils, logger, logger_send, avatar_downloader,
    create_tables,
    config, socketio, app, db_service
)
from functions.square.dashboard_handle import dashboard_handler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# 加载环境变量
load_dotenv()


class WebServer:
    """Web服务器类"""
    
    def __init__(self):
        """初始化Web服务器"""
        # 使用从functions模块导入的app实例
        self.app = app
        
        # 配置Flask日志使用我们的logger
        self.app.logger.handlers = logger.handlers
        self.app.logger.setLevel(logger.level)
        
        
        # 初始化组件
        self.db_manager = DatabaseManager()
        
        # 创建数据库表
        create_tables()
        # 使用从functions模块导入的socketio实例（已经与app绑定）
        self.socketio = socketio
        self.login_manager = LoginManager()
        self.avatar_downloader = avatar_downloader
        
        # 配置登录管理器
        self.login_manager.init_app(self.app)
        self.login_manager.user_loader(self.load_user)
        
        # 验证码缓存
        self.verification_cache: Dict[str, Dict[str, Any]] = {}
        
        # 注册路由
        self._register_routes()
        
        # 启动头像下载器
        self.avatar_downloader.start()
        
        # 初始化定时任务调度器
        self.scheduler = BackgroundScheduler()
        self._setup_scheduled_tasks()
        self.scheduler.start()
        
        logger.info('Web服务器初始化完成')
    
    def get_client_ip(self) -> str:
        """获取客户端真实IP地址
        
        Returns:
            客户端IP地址
        """
        # 检查代理头部
        if request.headers.get('X-Forwarded-For'):
            # 取第一个IP（客户端真实IP）
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        elif request.headers.get('CF-Connecting-IP'):  # Cloudflare
            return request.headers.get('CF-Connecting-IP')
        else:
            return request.remote_addr or '127.0.0.1'
    
    def check_ip_ban(self, f):
        """IP封禁检查装饰器
        
        Args:
            f: 被装饰的函数
            
        Returns:
            装饰后的函数
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = self.get_client_ip()
            
            # 检查IP是否被封禁
            if db_service.is_ip_banned(client_ip):
                logger.warning(f'被封禁的IP尝试访问: {client_ip}')
                abort(403)  # 返回403 Forbidden
            
            return f(*args, **kwargs)
        return decorated_function
    
    def handle_bad_request_and_ban(self, f):
        """处理400错误并封禁IP的装饰器（仅用于根路由）
        
        Args:
            f: 被装饰的函数
            
        Returns:
            装饰后的函数
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                response = f(*args, **kwargs)
                
                # 检查响应状态码
                if hasattr(response, 'status_code') and response.status_code == 400:
                    client_ip = self.get_client_ip()
                    logger.warning(f'检测到400错误，封禁IP: {client_ip}')
                    db_service.ban_ip(client_ip, '400 Bad Request from root route')
                
                return response
                
            except Exception as e:
                # 如果发生异常导致400错误
                if '400' in str(e) or 'Bad Request' in str(e):
                    client_ip = self.get_client_ip()
                    logger.warning(f'异常导致400错误，封禁IP: {client_ip}, 错误: {e}')
                    db_service.ban_ip(client_ip, f'400 Bad Request Exception: {str(e)[:100]}')
                raise
                
        return decorated_function
    
    def load_user(self, user_id: str) -> Optional['RIAPlayers']:
        """加载用户
        
        Args:
            user_id: 用户ID（主键）
            
        Returns:
            用户对象或None
        """
        try:
            if not user_id: return None
            if user_id == 'None': return None
            logger.debug(f'尝试加载用户，用户ID: {user_id}')
            user = self.db_manager.session.query(RIAPlayers).filter_by(id=int(user_id)).first()
            if user:
                logger.debug(f'成功加载用户: {user.player_name} (ID: {user.id})')
            else:
                logger.warning(f'未找到用户ID: {user_id}')
            return user
        except Exception as e:
            logger.error(f'加载用户失败: {e}')
            return None


    def _prepare_log_data(self, log_type: int) -> Tuple[List[Dict[str, Any]], int, int]:
        """准备日志数据
        
        Args:
            log_type: 日志类型 (1为RIA_log_info, 2为RIA_log_common)
            
        Returns:
            日志数据列表、最大ID、最小ID
        """
        try:
            # 查询日志数据
            if log_type == 1:
                logs = (self.db_manager.session.query(RIALogInfo)
                       .order_by(desc(RIALogInfo.t))
                       .limit(20)
                       .all())
            else:
                logs = (self.db_manager.session.query(RIALogCommon)
                       .order_by(desc(RIALogCommon.t))
                       .limit(20)
                       .all())
            
            log_data = []
            
            # 反向遍历以获得正确的时间顺序
            for log in reversed(logs):
                if log_type == 1:
                    # 检查头像文件
                    avatar_path = f'./static/img/{log.who_string}.png'
                    if not os.path.exists(avatar_path):
                        self.avatar_downloader.add_player(log.who_string)
                        img_path = 'default.jpg'
                    else:
                        img_path = f'{log.who_string}.png'
                    
                    result = {
                        "id": log.id,
                        "who_string": log.who_string,
                        "log_string": log.log_string,
                        "t": log.t.strftime("%H:%M"),
                        'img_path': img_path
                    }
                else:
                    result = {
                        "id": log.id,
                        "log_string": log.log_string,
                        "t": log.t.strftime("%H:%M"),
                    }
                
                log_data.append(result)
            
            # 计算最大和最小ID
            max_id = log_data[-1]['id'] if log_data else 0
            min_id = log_data[0]['id'] if log_data else 0
            
            return log_data, max_id, min_id
            
        except Exception as e:
            logger.error(f'准备日志数据失败: {e}')
            return [], 0, 0


    def _setup_scheduled_tasks(self):
        """设置定时任务"""
        try:
            # 添加每日午夜12点执行的仪表板数据处理任务
            self.scheduler.add_job(
                func=self._daily_dashboard_task,
                trigger=CronTrigger(hour=0, minute=0),  # 每天午夜12点执行
                id='daily_dashboard_task',
                name='每日仪表板数据处理',
                replace_existing=True
            )
            logger.info('定时任务设置完成：每日午夜12点执行仪表板数据处理')
        except Exception as e:
            logger.error(f'设置定时任务失败: {e}')
    
    def _daily_dashboard_task(self):
        """每日仪表板数据处理任务"""
        try:
            logger.info('开始执行每日仪表板数据处理任务')
            success = dashboard_handler.process_yesterday_data()
            if success:
                logger.info('每日仪表板数据处理任务执行成功')
            else:
                logger.error('每日仪表板数据处理任务执行失败')
        except Exception as e:
            logger.error(f'每日仪表板数据处理任务异常: {e}')

    def _register_routes(self):
        """注册所有路由"""
        # 根路由需要特殊处理：先检查IP封禁，然后处理400错误并封禁
        root_handler = self.check_ip_ban(self.handle_bad_request_and_ban(self.index))
        self.app.add_url_rule('/', 'index', root_handler, methods=['GET'])
        
        # 其他路由只需要IP封禁检查
        self.app.add_url_rule('/common', 'index_common', self.check_ip_ban(self.index_common), methods=['GET'])
        self.app.add_url_rule('/login', 'login_page', self.check_ip_ban(self.login_page), methods=['GET', 'POST'])
        self.app.add_url_rule('/logout', 'logout', self.check_ip_ban(self.logout), methods=['GET'])
        self.app.add_url_rule('/square', 'square_page', self.check_ip_ban(login_required(self.square_page)), methods=['GET'])
        self.app.add_url_rule('/square/dashboard', 'dashboard_page', self.check_ip_ban(login_required(self.dashboard_page)), methods=['GET'])
        self.app.add_url_rule('/square/dashboard/api', 'dashboard_page_api', self.check_ip_ban(login_required(self.dashboard_page_api)), methods=['GET'])
        self.app.add_url_rule('/register', 'register', self.check_ip_ban(self.register), methods=['GET', 'POST'])
        self.app.add_url_rule('/msg_send', 'msg_send', self.check_ip_ban(login_required(self.msg_send)), methods=['POST'])
        self.app.add_url_rule('/login_api/send', 'login_api_send', self.check_ip_ban(self.login_api_send), methods=['POST'])
        self.app.add_url_rule('/login_api/register', 'login_api_register', self.check_ip_ban(self.login_api_register), methods=['POST'])

    
    def msg_send(self):
        """发送消息接口"""
        try:
            # 获取POST数据
            data = request.get_json()
            message = data.get('message', '')
            
            if not message:
                return jsonify({'status': 1, 'message': '消息不能为空'})
            
            # 格式化消息
            player_name = current_user.player_name
            if player_name != 'Because':
                text = f'[{player_name}]:{message}'
            else:
                text = message
            
            # 验证消息内容
            from functions.utils import TextValidator
            if TextValidator.contains_illegal_chars(text):
                return jsonify({'status': 1, 'message': '禁止特殊字符'})
            
            if len(text) > 90:
                return jsonify({'status': 1, 'message': '内容过长'})
            
            # 记录日志并保存到数据库
            logger_send.info(text)
            
            msg_obj = RIAMsgSend(text=text)
            self.db_manager.add_and_commit(msg_obj)
            
            return jsonify({'status': 0, 'message': '发送成功'})
            
        except Exception as e:
            logger.error(f'发送消息失败: {e}')
            return jsonify({'status': 1, 'message': '发送失败'})
    
    def index(self):
        """主页"""
        try:
            # 检查请求参数是否有效
            if request.args:
                # 如果有查询参数，验证其有效性
                for key, value in request.args.items():
                    if not key or not isinstance(key, str) or len(key) > 100:
                        # 无效参数，返回400错误
                        logger.warning(f'无效的查询参数: {key}={value}')
                        abort(400)
                    if value and len(str(value)) > 1000:
                        # 参数值过长，返回400错误
                        logger.warning(f'查询参数值过长: {key}={value[:50]}...')
                        abort(400)
            
            log_data, max_id, min_id = self._prepare_log_data(1)
            logger.debug(f'访问主页 - 用户认证状态: {current_user.is_authenticated if hasattr(current_user, "is_authenticated") else "未定义"}, 用户: {current_user.player_name if hasattr(current_user, "player_name") else "匿名"}')
            return render_template(
                'main_v3.html',
                logs=log_data,
                max_log_id=max_id,
                min_log_id=min_id,
                current_user=current_user
            )
        except Exception as e:
            logger.error(f'加载主页失败: {e}')
            # 如果是400相关的错误，重新抛出让装饰器处理
            if '400' in str(e) or 'Bad Request' in str(e):
                raise
            return render_template('error.html', error='页面加载失败')
    
    def index_common(self):
        """通用日志页面"""
        try:
            log_data, max_id, min_id = self._prepare_log_data(2)
            logger.debug(f'访问通用日志页面 - 用户认证状态: {current_user.is_authenticated if hasattr(current_user, "is_authenticated") else "未定义"}, 用户: {current_user.player_name if hasattr(current_user, "player_name") else "匿名"}')
            return render_template(
                'main_com_log_v3.html',
                logs=log_data,
                max_log_id=max_id,
                min_log_id=min_id,
                current_user=current_user
            )
        except Exception as e:
            logger.error(f'加载通用日志页面失败: {e}')
            return render_template('error.html', error='页面加载失败')

    def login_page(self):
        """登录页面"""
        try:
            if current_user.is_authenticated:
                return redirect(url_for('index'))
            
            return render_template('login_v2.html')
            
        except Exception as e:
            logger.error(f'加载登录页面失败: {e}')
            return render_template('error.html', error='页面加载失败')

    def square_page(self):
        """广场页面"""
        try:
            if current_user.is_authenticated:
                return render_template('square.html')
            
            return redirect(url_for('login_page'))
            
        except Exception as e:
            logger.error(f'加载广场页面失败: {e}')
            return render_template('error.html', error='页面加载失败')

    def dashboard_page(self):
        """数据分析页面"""
        try:
            if current_user.is_authenticated:
                return render_template('dashboard/index.html')
            
            return redirect(url_for('login_page'))
            
        except Exception as e:
            logger.error(f'加载数据分析页面失败: {e}')
            return render_template('error.html', error='页面加载失败')

    def dashboard_page_api(self):
        """数据分析页面API"""
        try:
            if current_user.is_authenticated:
                yesterday = date.today() - timedelta(days=1)
                data = dashboard_handler.get_dashboard_data(yesterday)
                response = {'status': 0, 'message': '成功'}
                if data:
                    response['data'] = data
                else:
                    response['message'] = '无数据'
                return jsonify(response)
            
            return jsonify({'status': 1, 'message': '未认证'})
            
        except Exception as e:
            logger.error(f'加载数据分析页面API失败: {e}')
            return jsonify({'status': 1, 'message': '页面加载失败'})

    def login_api_send(self):
        """发送登录验证码"""
        try:
            data = request.get_json()
            username = data.get('username', '')
            email = data.get('email', '')
            
            if not username or not email:
                return jsonify({'msg': '用户名和邮箱不能为空', 'status': 1})
            
            # 检查禁用用户名
            banned_names = ['because', 'Because']
            if username in banned_names:
                return jsonify({'msg': '不受支持的用户', 'status': 1})
            
            # 检验用户是否存在
            if not SystemUtils.check_player_exist(username):
                return jsonify({'msg': '用户不存在', 'status': 1})
            
            # 生成验证码
            verification_code = random.randint(1000, 9999)
            
            logger.info(f'发送邮件验证码，用户: {email}, 验证码: {verification_code}')
            
            # 发送验证码邮件
            email_service = EmailService()
            result = email_service.send_verification_code(email, str(verification_code))
            
            if result.get('status') == 0:
                # 缓存验证码
                self.verification_cache[email] = {
                    'code': str(verification_code),
                    'end_time': time.time() + 300  # 5分钟有效期
                }
                logger.info(f'验证码发送成功: {verification_code}')
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f'发送验证码失败: {e}')
            return jsonify({'msg': '发送验证码失败', 'status': 1})
    
    def login_api_register(self):
        """用户登录/注册"""
        try:
            data = request.get_json()
            username = data.get('username', '')
            email = data.get('email', '')
            code = data.get('code', '')
            
            if not username or not email or not code:
                return jsonify({'msg': '所有字段都不能为空', 'status': 1})
            
            # 特殊用户处理
            if username == 'Because':
                return jsonify({'msg': '该用户不受支持', 'status': 1})
            
            # 普通用户验证码验证
            if email not in self.verification_cache:
                return jsonify({'msg': '验证码错误', 'status': 1})
            
            cached_data = self.verification_cache[email]
            cached_code = cached_data['code']
            end_time = cached_data['end_time']
            
            # 检查验证码是否过期
            if time.time() > end_time:
                del self.verification_cache[email]
                return jsonify({'msg': '验证码超时', 'status': 1})
            
            # 检查验证码是否正确
            if cached_code != code:
                return jsonify({'msg': '验证码错误', 'status': 1})
            
            # 验证码正确，查找或创建用户
            user = (self.db_manager.session.query(RIAPlayers)
                   .filter_by(player_name=username, email=email)
                   .first())
            
            if user is None:
                user = RIAPlayers(player_name=username, email=email)
                self.db_manager.add_and_commit(user)
            
            # 登录用户
            login_user(user, remember=True)
            # 确保会话是永久的
            from flask import session
            session.permanent = True
            
            # 清除验证码缓存
            del self.verification_cache[email]
            
            logger.info(f'用户登录成功: {username} (ID: {user.id})')
            return jsonify({'msg': '登录成功', 'status': 0})
            
        except Exception as e:
            logger.error(f'用户登录失败: {e}')
            return jsonify({'msg': '登录失败', 'status': 1})

    @login_required
    def logout(self):
        """用户登出"""
        try:
            username = current_user.player_name if hasattr(current_user, 'player_name') else '未知用户'
            logout_user()
            logger.info(f'用户登出成功: {username}')
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f'用户登出失败: {e}')
            return redirect(url_for('index'))
    
    def register(self):
        """注册页面（暂未实现）"""
        return jsonify({'msg': '注册功能暂未开放', 'status': 1})
    

    
    def run(self, host: str = '127.0.0.1', port: int = 211, debug: bool = True):
        """启动Web服务器
        
        Args:
            host: 主机地址
            port: 端口号
            debug: 是否开启调试模式
        """
        try:
            logger.info(f'启动Web服务器，地址: {host}:{port}')
            
            # 配置SocketIO日志使用我们的logger
            import logging
            socketio_logger = logging.getLogger('socketio')
            socketio_logger.handlers = logger.handlers
            socketio_logger.setLevel(logger.level)
            engineio_logger = logging.getLogger('engineio')
            engineio_logger.handlers = logger.handlers
            engineio_logger.setLevel(logger.level)
            
            # Windows环境下使用threading模式，避免gevent-websocket问题
            self.socketio.run(
                self.app,
                host=host,
                port=port,
                debug=debug,
                use_reloader=False,
                log_output=False  # 禁用默认日志输出，使用我们的logger
            )
            
        except Exception as e:
            logger.error(f'Web服务器启动失败: {e}')
            raise
    
    def cleanup(self):
        """清理资源"""
        try:
            logger.info('正在清理Web服务器资源...')
            
            # 停止定时任务调度器
            if hasattr(self, 'scheduler') and self.scheduler:
                self.scheduler.shutdown()
                logger.info('定时任务调度器已停止')
            
            # 停止头像下载器
            if self.avatar_downloader:
                self.avatar_downloader.stop()
            
            # 关闭数据库连接
            if self.db_manager:
                self.db_manager.close()
            
            logger.info('Web服务器资源清理完成')
            
        except Exception as e:
            logger.error(f'清理Web服务器资源时出错: {e}')


def main():
    """主函数"""
    try:
        # 创建Web服务器实例
        web_server = WebServer()
        
        # 启动服务器
        if config.ENV == 'development':
            web_server.run(host='127.0.0.1', port=211, debug=True)
        else:
            web_server.run(host='0.0.0.0', port=211, debug=False)
        
    except KeyboardInterrupt:
        logger.info('收到中断信号，正在关闭Web服务器...')
    except Exception as e:
        logger.error(f'Web服务器运行出错: {e}')
    finally:
        # 清理资源
        if 'web_server' in locals():
            web_server.cleanup()


if __name__ == '__main__':
    main()
