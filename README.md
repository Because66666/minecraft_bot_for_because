# Minecraft Bot for Because

一个功能丰富的Minecraft机器人，集成了Kook（开黑啦）聊天平台与智谱轻言AI对话功能，提供游戏内外的互动体验。
由because个人从2022年开始开发并用于个人游玩过程，持续维护和更新。于2025年正式开源。
源代码因为过于臃肿，使用claude 4重构了整个项目并且修复若干bug后再次发布。

## 功能特性

### 🎮 Minecraft 机器人功能
- **自动化操作**：自动睡觉、自动签到、承接tpa传送等
- **玩家监控**：实时记录玩家上线/下线状态
- **事件响应**：响应游戏内各种事件（死亡、受伤、踢出等）
- **智能聊天**：集成智谱AI GLM模型，提供智能对话功能
- **定时任务**：支持定时执行各种游戏操作
- **关键词彩蛋**：关注游戏内聊天栏，当玩家发送包含特定关键词的消息时，触发相应的彩蛋播报以及虚拟货币的支付。

### 💬 Kook 集成
- **双向消息同步**：游戏内外消息实时同步
- **实时通知**：游戏事件实时推送到Kook频道

### 🌐 Web 实时对话界面
- **用户管理**：用户注册、登录、认证
- **用户认证**：基于邮箱的用户注册和登录系统
- **消息管理**：支持消息发送、接收和历史记录
- **日志查看**：实时查看游戏和系统日志
- **消息发送**：通过Web界面发送消息到游戏，并且与游戏内玩家实时对话

### 🧠 AI聊天功能
- **智谱AI集成**：使用智谱AI的GLM-4-Flash模型提供智能对话
- **多用户会话**：支持多用户同时进行AI对话，独立会话管理
- **上下文记忆**：维护对话上下文，提供连贯的聊天体验
- **角色扮演**：内置系统提示词以实现自定义的角色设定
- **容错处理**：AI服务异常时优雅降级，不影响其他功能
- **参数验证**：严格的输入验证，防止无效请求导致程序崩溃

## 技术架构

### 核心组件
- **Minecraft Bot**：基于Node.js mineflayer库的游戏机器人
- **Kook API**：与开黑啦平台的REST API集成
- **Flask Web Server**：提供Web管理界面和API服务
- **SQLAlchemy ORM**：数据库操作和模型管理
- **智谱AI服务**：集成GLM-4-Flash模型提供AI对话功能
- **Socket.IO**：实现Web界面与后端的实时双向通信
- **配置管理**：统一的环境变量和配置管理系统
- **日志系统**：分类日志记录和错误追踪

### 数据库模型
- **用户管理**：玩家信息、认证状态
- **消息系统**：聊天记录、消息队列
- **日志系统**：操作日志、错误日志
- **AI集成**：AI对话历史和配置

## 安装和配置

### 环境要求
- Python 3.8+
- SQLite数据库
- Kook机器人Token（可选）
- 智谱AI API密钥（可选）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/Because66666/minecraft_bot_for_because
cd mc_bot_for_github
```

2. **安装Python依赖**
```bash
pip install -r requirements.txt
```

**主要依赖包：**
- Flask 2.3.3 - Web框架
- Flask-SocketIO 5.3.6 - 实时通信
- SQLAlchemy 2.0.23 - 数据库ORM
- zhipuai 2.0.1 - 智谱AI SDK
- requests 2.31.0 - HTTP请求
- python-dotenv 1.0.0 - 环境变量管理

3. **配置环境变量**
将`.env.example`文件改为`.env`文件以启用环境变量配置。

**重要配置项说明：**

**游戏连接配置：**
- `PLAYER`: Minecraft玩家名
- `HOST`: 服务器地址（默认：127.0.0.1）
- `PORT`: 服务器端口（默认：25565）
- `AUTH`: 是否启用正版验证（True/False）
- `SERVER_PASSWORD`: 服务器登录密码

**Kook机器人配置：**
- `KOOK`: Kook机器人Token（必需）
- `KOOK_MAIN_CHANNEL`: 主频道ID
- `KOOK_AI_CHANNEL`: AI对话频道ID

**智谱AI配置：**
- `ZHIPU_AI_API_KEY`: 智谱AI的API密钥（必需）
- `ZHIPU_AI_MODEL`: 使用的模型名称（默认：glm-4-flash）
- `AI_SESSION_TIMEOUT`: AI会话超时时间（秒，默认：180）
- `SYSTEM_PROMPT`: AI系统提示词

**邮件服务配置：**
- `MAIL_USER`: 邮箱账号
- `MAIL_PASS`: 邮箱密码或授权码
- `MAIL_HOST`: SMTP服务器（默认：smtp.qq.com）
- `MAIL_PORT`: SMTP端口（默认：465）

**Flask应用配置：**
- `SECRET_KEY`: Flask应用密钥

**获取智谱AI API密钥：**
1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册账号并创建API密钥
3. 将密钥填入`.env`文件的`ZHIPU_AI_API_KEY`字段


## 使用方法

### 启动机器人

1. **启动Minecraft机器人**
```bash
python mc.py
```

2. **启动Web服务器**
```bash
python server.py
```

3. **访问Web界面**
打开浏览器访问 `http://localhost:211`

### 基本操作

#### 用户注册和登录
1. 访问Web界面的登录页面
2. 使用邮箱注册账户
3. 验证邮箱后即可登录

#### 发送消息
- **游戏内**：直接在游戏聊天框输入消息
- **Kook**：在配置的频道中发送消息
- **Web界面**：登录后在消息发送页面输入

#### 机器人命令
游戏内可使用以下命令：
- `/tpa <bot_name>` - 承接传送
- `/whisper <bot_name> <消息>` - 与AI进行对话
- 关键词触发 - 发送特定关键词触发彩蛋功能

## 项目结构

```
mc_bot_for_github/
├── mc.py                 # Minecraft机器人主程序
├── server.py             # Flask Web服务器
├── .env                  # 环境变量配置文件
├── .env.example          # 环境变量配置示例
├── .gitignore            # Git忽略文件配置
├── functions/            # 核心功能模块
│   ├── __init__.py       # 模块导出接口
│   ├── config.py         # 配置管理
│   ├── database.py       # 数据库模型和操作
│   ├── my_logger.py      # 日志系统
│   ├── tools.py          # Flask应用和Socket.IO
│   ├── utils.py          # 系统工具和游戏逻辑
│   ├── kook_api.py       # Kook API封装
│   ├── communicate_by_ai.py # AI通信模块
│   ├── keyword_in_communication.py # 关键词处理
│   └── timetable_info.py # 时间表信息模块
├── templates/            # HTML模板文件
│   ├── error.html        # 错误页面
│   ├── for_because.html  # 主页面
│   └── for_because_v2.html # 主页面v2
├── static/              # 静态资源
│   ├── css/             # 样式文件
│   ├── js/              # JavaScript文件
│   └── img/             # 图片资源（玩家头像）
├── logs/                # 日志文件目录
│   ├── ai.txt           # AI对话日志
│   ├── communication.txt # 通信日志
│   ├── error.txt        # 错误日志
│   ├── log.txt          # 主日志
│   └── sending.txt      # 消息发送日志
├── requirements.txt     # Python依赖
└── README.md           # 项目文档
```

## 开发指南

### 代码结构

#### 主要类和模块
- **Config**：统一配置管理类
- **DatabaseManager**：数据库连接和操作管理
- **KookAPI**：Kook平台API封装和消息发送
- **ZhipuAIChat**：智谱AI聊天管理和对话处理
- **GeometryUtils/SystemUtils**：几何计算和系统工具
- **EasterEggManager**：关键词彩蛋管理
- **EmailService**：邮件发送服务
- **Logger系统**：分类日志记录（通信、AI、发送、错误）

#### 数据库模型
- **RIAPlayers**：玩家信息和认证状态
- **RIAMsgSend**：消息发送队列
- **RIALogin**：玩家登录记录
- **RIAOnline**：在线状态记录
- **RIALogInfo/RIALogCommon**：系统日志记录
- **UserRecord**：用户注册和认证记录
- **CreativeLogin**：创造服务器登录记录

### 扩展开发

#### 添加新的游戏事件处理
```python
class BotEventHandler:
    @staticmethod
    def handle_new_event(bot, event_data):
        """处理新的游戏事件"""
        try:
            # 事件处理逻辑
            logger.info(f'处理新事件: {event_data}')
        except Exception as e:
            logger.error(f'处理事件失败: {e}')
```

#### 添加新的Web路由
```python
class WebServer:
    def new_route(self):
        """新的Web路由"""
        try:
            # 路由处理逻辑
            return jsonify({'status': 'success'})
        except Exception as e:
            logger.error(f'路由处理失败: {e}')
            return jsonify({'status': 'error', 'message': str(e)})
```

#### 扩展AI功能
```python
# 在communicate_by_ai.py中扩展AI功能
from functions.communicate_by_ai import get_ai_chat_instance, main_ai

def custom_ai_handler(username, message, caches=None):
    """自定义AI处理函数"""
    try:
        # 使用main_ai函数进行AI对话
        response = main_ai(username, message, caches)
        return response
    except Exception as e:
        logger.error(f'AI处理失败: {e}')
        return "抱歉，AI服务暂时不可用"

# 自定义AI配置
class CustomAIChat(ZhipuAIChat):
    def __init__(self):
        super().__init__()
        # 可以通过环境变量自定义模型
        self.model = os.getenv('ZHIPU_AI_MODEL', 'glm-4-flash')
        self.temperature = 0.7  # 调整创造性
```

#### 网页端API接口说明
[转md文档](server_api.md)

## 故障排除

### 常见问题

1. **机器人无法连接到Minecraft服务器**
   - 检查服务器地址和端口配置
   - 确认用户名和密码正确
   - 检查网络连接

2. **Kook消息发送失败**
   - 验证Kook Token是否正确
   - 检查频道ID配置
   - 确认机器人有发送消息权限

3. **Web界面无法访问**
   - 检查端口是否被占用
   - 确认防火墙设置（如果是公开前端界面，需要找对应的服务器供应商的防火墙设置）
   - 查看服务器启动日志

4. **数据库连接错误**
   - 检查数据库文件路径
   - 确认数据库权限
   - 验证连接字符串格式

5. **AI对话功能异常**
   - 检查智谱AI API密钥是否正确配置
   - 确认网络连接正常
   - 查看AI相关日志文件

6. **参数缺失导致程序崩溃**
   - 程序已优化错误处理，缺少必要参数时会记录日志而不崩溃
   - 检查日志文件中的警告和错误信息
   - 确保所有必需的环境变量都已正确配置

### 日志查看
项目采用分类日志系统，便于问题定位：
- **主日志** (`logs/log.txt`)：系统主要运行日志
- **通信日志** (`logs/communication.txt`)：游戏内外消息通信记录
- **AI日志** (`logs/ai.txt`)：AI对话和处理记录
- **发送日志** (`logs/sending.txt`)：消息发送状态记录
- **错误日志** (`logs/error.txt`)：系统错误和异常记录
- **控制台输出**：实时查看程序运行状态
- **Web界面**：通过Web管理界面查看日志

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 创建 Issue

## 重构日志

### v2.0.0 (最新)
- 完全重构代码架构，模块化设计
- 改进错误处理和日志记录系统
- 优化数据库操作和连接管理
- 增强Web界面功能和用户体验
- 集成智谱AI GLM模型提供智能对话
- 添加参数验证和容错处理机制
- 提升系统稳定性和可维护性
- 统一配置管理和环境变量处理

### v1.0.0
- 初始版本发布
- 基础Minecraft机器人功能
- Kook集成
- 简单Web管理界面
