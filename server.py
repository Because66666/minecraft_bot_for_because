"""Web服务器模块

提供日志展示、用户认证和消息发送功能的Flask Web应用
"""
import os
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List, Optional

from flask import config, request, render_template, jsonify, redirect, url_for
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
    RIAMsgSend, RIAPlayers,
    SystemUtils, logger, logger_send, avatar_downloader,
    create_tables,
    config, socketio, app
)

# 加载环境变量
load_dotenv()


class WebServer:
    """Web服务器类"""
    
    def __init__(self):
        """初始化Web服务器"""
        # 使用从functions模块导入的app实例
        self.app = app
        
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
        
        logger.info('Web服务器初始化完成')
    
    def load_user(self, user_id: str) -> Optional['RIAPlayers']:
        """加载用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象或None
        """
        try:
            return self.db_manager.session.query(RIAPlayers).filter_by(id=int(user_id)).first()
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


    def _register_routes(self):
        """注册所有路由"""
        self.app.add_url_rule('/', 'index', self.index, methods=['GET'])
        self.app.add_url_rule('/common', 'index_common', self.index_common, methods=['GET'])
        self.app.add_url_rule('/login', 'login_page', self.login_page, methods=['GET', 'POST'])
        self.app.add_url_rule('/logout', 'logout', login_required(self.logout), methods=['GET'])
        self.app.add_url_rule('/register', 'register', self.register, methods=['GET', 'POST'])
        self.app.add_url_rule('/msg_send', 'msg_send', login_required(self.msg_send), methods=['POST'])
        self.app.add_url_rule('/login_api/send', 'login_api_send', self.login_api_send, methods=['POST'])
        self.app.add_url_rule('/login_api/register', 'login_api_register', self.login_api_register, methods=['POST'])

    
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
            log_data, max_id, min_id = self._prepare_log_data(1)
            return render_template(
                'main_v3.html',
                logs=log_data,
                max_log_id=max_id,
                min_log_id=min_id,
                current_user=current_user
            )
        except Exception as e:
            logger.error(f'加载主页失败: {e}')
            return render_template('error.html', error='页面加载失败')
    
    def index_common(self):
        """通用日志页面"""
        try:
            log_data, max_id, min_id = self._prepare_log_data(2)
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
            
            # 清除验证码缓存
            del self.verification_cache[email]
            
            return jsonify({'msg': '登录成功', 'status': 0})
            
        except Exception as e:
            logger.error(f'用户登录失败: {e}')
            return jsonify({'msg': '登录失败', 'status': 1})

    def logout(self):
        """用户登出"""
        try:
            logout_user()
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
            
            self.socketio.run(
                self.app,
                host=host,
                port=port,
                debug=debug,
                use_reloader=False,
                log_output=True
            )
            
        except Exception as e:
            logger.error(f'Web服务器启动失败: {e}')
            raise
    
    def cleanup(self):
        """清理资源"""
        try:
            logger.info('正在清理Web服务器资源...')
            
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
        web_server.run()
        
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
