## 路由与HTML界面映射分析

| 路由路径 | 处理函数 | 使用的HTML模板 | 说明 |
|---------|----------|----------------|------|
| `/` (主页) | `index()` | `main_v3.html` | 主聊天界面页面 |
| `/common` (通用日志) | `index_common()` | `main_com_log_v3.html` | 通用日志显示页面 |
| `/login` (登录页面) | `login_page()` | `login_v2.html` | 用户登录界面 |
| `/logout` (登出) | `logout()` | 无（重定向到主页） | 执行登出后重定向到主页 |
| `/register` (注册) | `register()` | 无（返回JSON） | 注册功能暂未实现 |
| `/msg_send` (发送消息) | `msg_send()` | 无（返回JSON） | API接口，返回JSON响应 |
| `/login_api/send` (发送验证码) | `login_api_send()` | 无（返回JSON） | API接口，返回JSON响应 |
| `/login_api/register` (登录注册) | `login_api_register()` | 无（返回JSON） | API接口，返回JSON响应 |

### 错误处理
所有页面在发生异常时都会使用：
- `error.html` - 错误显示页面

### 模板文件位置
根据代码中的`render_template()`调用，这些HTML文件应该位于：
- `templates/main_v3.html`
- `templates/main_com_log_v3.html` 
- `templates/login_v2.html`
- `templates/error.html`

API接口（`/msg_send`、`/login_api/send`、`/login_api/register`）不返回HTML界面，而是返回JSON格式的响应数据。
        