# 独立邮箱登录模块

用途：邮箱密码注册、登录、当前用户查询及退出；不接管 listening 的匿名 student_id。

## 启动配置

安装 `backend/requirements.txt` 中的新增依赖。现有 main.py 仍需原来的 DeepSeek 配置。
在后端进程环境或本地 backend/.env 配置以下变量（不要提交真实密钥）：

```dotenv
AUTH_JWT_SECRET=<使用 secrets.token_urlsafe(48) 生成的随机密钥>
AUTH_COOKIE_SECURE=true
AUTH_ALLOWED_ORIGINS=https://你的实际网站域名
```

使用 `python -c "import secrets; print(secrets.token_urlsafe(48))"` 生成密钥，妥善保管。
密钥至少 32 字节、所有 worker 保持一致；缺失时注册/登录返回 503，不使用默认弱密钥。
本地 HTTP 开发需明确设 `AUTH_COOKIE_SECURE=false`，允许来源可保留默认的
`http://localhost:5173,http://127.0.0.1:5173`。生产环境必须使用 HTTPS 和 Secure cookie。
反向代理下请显式配置真实前端 Origin（协议、主机、必要的端口，无路径）。

默认账号数据库是 `backend/auth/data/auth.db`，首次账号请求时自动建表，已加入 Git 忽略。
可设置绝对路径 `AUTH_DB_PATH`；禁止指向 listening 目录。部署用户需有该独立目录写权限。
本任务测试只使用临时数据库，不创建或修改真实账号库、listening.db。

## 接口与页面

- POST `/api/auth/register`：JSON `{email,password}`；201 返回用户，注册后跳转登录，不自动登录。
- POST `/api/auth/login`：同上；返回用户，通过 HttpOnly/SameSite=Lax cookie 设置 30 天 JWT。
- POST `/api/auth/logout`：204，清除同路径 cookie。
- GET `/api/auth/me`：返回 id/email/created_at/is_active；未登录、过期、禁用账号返回 401。
- 所有 POST 要求 `X-Auth-Request: 1`，前端客户端已自动添加，用于抵御跨站伪造请求。
- `/login`、`/register`、`/forgot-password`；忘记密码仅展示联系管理员提示。

邮箱去除首尾空白并统一小写；密码不 trim，至少 8 个字符、UTF-8 不超过 72 字节，避免 bcrypt 截断。
token 和密码哈希不返回前端 JSON，不写 localStorage；既有匿名学习记录不会自动迁移到账号。

## 验证与边界

在 backend 下运行 `python -m pytest tests/test_auth.py`；在 frontend 下运行 `npm run build`。
没有邮件验证码，不能证明用户拥有该邮箱；没有密码重置邮件、账号合并或跨设备同步。
登出只清除当前浏览器 cookie，已复制的 JWT 在过期前仍有效；全会话撤销需后续会话表。
本阶段没有新增注册/登录限流，上公网前应补充限流与滥用防护。
新增认证不会保护既有 listening/teacher/writing 接口，不应将它描述为全站访问控制。

实现参考：bcrypt 官方说明 https://pypi.org/project/bcrypt/ ，
python-jose JWT API https://python-jose.readthedocs.io/en/latest/jwt/api.html 。

### 本次验证（2026-09-08）

- `npm run build`：TypeScript 检查和 Vite 生产构建通过。
- `tests/test_auth.py`：15 项通过；有一项 Starlette/httpx 弃用警告，不影响结果。
- 使用生产前端构建和独立 auth router，浏览器验证了注册、密码确认、登录、刷新保持、首页登出、登出后刷新及三个页面路由。
- 测试未导入完整 main.py，避免初始化 listening 或调用写作模型；现有 Python venv 解释器路径失效，因此依赖安装在工作区隔离测试目录。
- 现有 listening.db 测试前后 SHA-256 一致，真实 auth/data 目录未创建。
- 没有部署线上，也没有写入真实 JWT 密钥或修改 backend/.env；正式运行前须完成上述配置。
