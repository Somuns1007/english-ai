# 管理员账号 + 邮箱验证码实施与上线说明

日期：2026-09-21。代码本地实现；**未操作线上数据库、未部署、未发送真实邮件**。

## 已完成的功能

1. 用户新增 `role=user/admin`，默认全部为普通用户；注册传入 role 无法提权。
2. 当前登录每次从数据库读取角色。管理员无需教师口令即可管理图片、听力表达和语料。
3. 网站顶部为管理员显示图片管理、听力管理、语料管理入口；管理端仍由后端强制鉴权。
4. 账户 Cookie 管理写入需要原有 CSRF 请求头与来源检查，旧共享口令可显式关闭。
5. 邮件验证码用于注册验证、找回密码，仍保留平时的邮箱密码登录，不是每次登录都发邮件。
6. 验证码用途与邮箱绑定，10 分钟有效，仅可使用一次，最多尝试 5 次；数据库只保存 HMAC 摘要。
7. 同一邮箱 60 秒发送间隔、每小时最多 5 次；每 IP 每小时 20 次；全站滚动 24 小时默认 200 次。
   失败及不存在账号请求也占限额，减少费用滥用；新发送请求清理超过 48 小时的记录，无请求期间不定时清理。
8. 重置密码后增加 token_version，旧设备和已复制的旧 JWT 均失效；角色不会改变。
9. 未配置邮件时返回明确的不可用提示，不会返回验证码或伪造真实发送成功。

## 实际阻碍（未完成上线的原因）

- 本地 `backend/auth/data/auth.db` 不存在，`.env` 没有 AUTH_DB_PATH 覆盖。不能找到或操作线上账号 UUID。
- 本地没有 SMTP 配置，不知道要使用哪一家服务的实际发信账户。
- 本机 `.ssh` 只有 known_hosts 文件，没有登录配置或身份密钥；未尝试猜测服务器用户、密码或绕过访问。
- 因此 **303528771@qq.com 尚未被本轮操作授予线上管理员权限**，也没有新建一个同名账号替代它。

## 一、给已有账号一次性授予管理员

在**生产实际项目的 backend 目录、现有 Python 虚拟环境**下执行，使用原生产 `.env`。
前提是本轮后端代码已更新到服务器；旧版本没有 auth.admin 模块。
先确认 systemd EnvironmentFile 与当前 shell 的 AUTH_DB_PATH 一致，不要误用另一个 auth.db。
例如原项目目录若仍是 `/var/www/english-ai`，进入 `/var/www/english-ai/backend`；不要凭此示例修改现有部署目录。

第一步仅查询：

```bash
python -m auth.admin --email 303528771@qq.com
```

它只读查询该已有账号，打印 UUID。若不存在、被禁用或不唯一会停止，不会创建账号。
确认这是你已持有、已登录的账号，然后用刚才返回的 UUID 执行：

```bash
python -m auth.admin --email 303528771@qq.com --user-id 实际查询返回的UUID
```

命令先通过 SQLite backup API 备份当前账户库，再校验 UUID + 邮箱 + 启用状态，授予 admin，并记录操作审计。
不是在每次连接数据库时按邮箱自动提升权限；未来注册同一邮箱也不会自动成为管理员。
本工具没有公网提权接口。需拥有服务器操作权限的人才能运行。

授权后刷新网页：`/api/auth/me` 应返回 `role: admin`。
检查 `/api/admin/gallery`、`/api/listening/teacher/expressions`、`/api/listening/teacher/corpus/assets` 无教师口令均可访问。
角色从数据库实时读取，一般不需要重新登录。不要把用户密码、Cookie、SMTP 密钥贴进聊天。

## 二、关闭旧教师口令

验证账号管理功能和教师音频预览都正常后，在生产环境设置：

```dotenv
AUTH_ALLOW_LEGACY_TEACHER_TOKEN=false
```

重启现有后端服务。之后普通账号即使持有旧 TEACHER_TOKEN 也无法进入图片和听力管理接口。
默认 true 仅为了迁移期间兼容原流程；**未关闭前，管理员账号不是唯一管理通道**。
如登录管理员仍无法使用某接口，不要重新公开上传目录或绕过发布 gate。

## 三、接入真实邮件

当前实现使用标准 TLS SMTP（适配实际支持 SMTP 的服务），无新增收费 SDK，也没有自动购买服务。
请先选择允许你的个人实名认证主体使用的发信服务；服务端 API 与 SMTP 权限可能不同，不能假定所有产品都支持。
如果选定的平台只开放 HTTP API，需要另接它的正式投递接口，不可用未获授权的 SMTP 方式绕过。

在服务商控制台完成发信地址/域名验证与要求的 SPF、DKIM 等 DNS 配置后，将下列内容填到服务器 `.env`，不要提交 Git：

```dotenv
AUTH_SMTP_HOST=服务商提供的SMTP主机
AUTH_SMTP_PORT=465
AUTH_SMTP_SECURITY=ssl
AUTH_SMTP_USER=服务商给出的SMTP用户名
AUTH_SMTP_PASSWORD=服务商给出的SMTP授权密码
AUTH_MAIL_FROM=已验证的发信地址
AUTH_MAIL_DAILY_LIMIT=200
AUTH_EMAIL_VERIFICATION_REQUIRED=true
```

如果服务商要求 587/STARTTLS，则同时修改端口为 587、security 为 starttls。禁止明文 SMTP。
配置需由管理员安全保存到服务器文件，不应写入前端、不应粘贴到对话中。
先在测试环境验证真实投递和垃圾邮件落箱情况，再在生产开启强制注册验证。
`email_available=true` 只说明必要配置齐全，**不代表 SMTP 连通、域名审核及投递已经成功**。

默认 `AUTH_EMAIL_VERIFICATION_REQUIRED=false` 兼容已有注册，不会在无发信渠道时突然让原站无法注册。
当设置 true 后，没有有效验证码不能注册；旧账号仍可使用原密码登录，不会被自动标成已验证邮箱。
找回密码成功说明当前拥有邮箱，email_verified 随之更新。

邮件上限限制的是本应用的发送尝试，不覆盖服务商账号被其他应用使用的费用，仍应开启云平台费用告警。
接口不直接信任客户端自报 IP；保持现有 Nginx X-Forwarded-For 与 Uvicorn 仅信任本机反代的配置。

## 四、构建、迁移与部署

- 不使用 Alembic。auth.models.database 自动幂等添加 users 的 role/email_verified/token_version 字段。
- 添加 auth_email_codes、auth_role_audit 表及索引；不修改 listening.db。
- 不需要为本轮增加依赖，SMTP、TLS、HMAC 使用 Python 标准库。
- 前端在 frontend 目录执行 `npm run build`，按现有流程发布 dist；后端更新后重启现有服务。
- 如果服务名是模板中的 english-ai，可执行 `sudo systemctl restart english-ai`，否则使用实际服务名。
- **不要直接部署未整理的整个脏工作区**：图片墙视觉改动和站点 CSS 是本轮开始前已有的改动，本轮已保留。
- 本轮没有改 Nginx、真实 .env、数据 JSON 或 listening release/profile gate。

建议顺序：先更新后端（注册验证码暂保持 false）→ 发布新前端 → 按 UUID 授权并验证管理账号 → 配置并测试真实邮件 → 开启注册验证 → 确认后台全部正常后关闭旧教师口令。不要在旧前端尚未支持验证码时提前强制验证。

## 五、验证清单

1. 普通用户注册，即便提交 role=admin 或使用指定邮箱也只获得 user。
2. 已有账号授权后，原 Cookie 无需更换即可访问图片/听力后台；撤销角色立即失去权限。
3. 图片原图与缩略图同样接受管理员角色，未登录者不可读取未审核图片。
4. 管理员 Cookie 写请求缺失 X-Auth-Request 或来源不合法时拒绝。
5. 关闭旧口令开关后，普通用户携带旧口令也被拒绝。
6. 验证码错邮箱、错用途、过期、重复使用、连续错 5 次均不能注册/改密码。
7. 已发送验证码不会原样出现在接口响应或数据库；发送失败不暴露 SMTP 异常和密钥。
8. 重置后旧密码失败、旧 Cookie 401，新密码可以登录，管理员角色保持不变。
9. `.env` 未配置邮件时前端明确提示；配置后实际收信需再单独验收。

自动测试使用临时数据库与模拟邮件，不会发出真实邮件。复测：

```bash
python backend/tests/run_student_auth_regression.py tests -x -q
```

仅本地页面验证可运行 `python backend/tests/preview_auth.py`，然后启动 Vite。
该预览脚本使用一次性账号库、禁用旧教师口令，邮件为模拟投递，**严禁作为生产服务启动**。

## 六、本轮代码文件

新增：`backend/auth/admin.py`、`permissions.py`、`mailer.py`、`email_codes.py`；
`backend/tests/test_admin_email.py`、`preview_auth.py`；`frontend/src/components/EmailCodeField.vue`；本文档。

修改：`backend/auth/models.py`、`service.py`、`router.py`、`README.md`；
`backend/.env.example`；`backend/gallery/router.py`；`backend/listening/router.py`；
`frontend/src/services/authApi.ts`、`listeningApi.ts`；
`frontend/src/components/AuthStatus.vue`；`frontend/src/views/gallery/GalleryView.vue`；
`frontend/src/views/listening/TeacherGate.vue`；
`frontend/src/views/auth/RegisterView.vue`、`ForgotPasswordView.vue`、`auth.css`。

## 七、本地验证结果

- 最终完整后端测试：**300 passed in 97.82s**，新增专项测试 10 项。
- `npm run build`：TypeScript 与生产构建通过。
- 完整 FastAPI 应用在一次性账户/听力数据库下启动成功。
- 浏览器技能检查：管理员登录后出现三个后台入口；图片、表达和语料管理不要求教师口令；退出后管理员入口消失。
- 手机注册表单包含验证码、发送提示与倒计时，无横向溢出；检查时修正了浅色模式下表单背景/文字对比度。
- 使用模拟投递验证页面提示，不等于真实 SMTP 投递验收。
- 真实 listening.db SHA256 保持 `AEDEB601197E859E3ECA5E41DCB809288352FCEECDE6E4F5648F7B6B19628DC0`；本地真实 auth.db 仍不存在，未新建替代账号库。
- `student_release_allowed=false` 保持不变。未进行 Git 提交、推送或线上部署。
