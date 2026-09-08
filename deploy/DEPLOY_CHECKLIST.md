# English AI 上线准备检查单

用途：人工部署与验收说明，不是自动执行脚本。本次只准备配置，不连接服务器、不部署、不修改生产数据库。

## 0. 先确认真实生产布局

- 历史路径为 `/var/www/english-ai`，模板使用 `/opt/english-ai`。先检查现有服务、Nginx root/proxy_pass 和部署脚本，选定实际路径后统一替换，不能直接覆盖或搬迁线上目录。
- 域名 A/AAAA、TLS 证书、现有监听端口和反代必须核实；不要让旧服务与新服务竞争 8000。
- `frontend/dist/` 是构建产物，不是 `frontend/src/`。
- 当前数据（包括两个 SQLite 文件及音频）不完全由 Git 管理；新克隆不是可直接使用的完整生产数据。单独恢复经过确认的合法素材及数据库备份，禁止用空测试数据库覆盖。
- CORS 限制跨 Origin 浏览器访问；本模板前后端同源反代，本身不依赖跨域许可。生产 Origin 同时用于 auth CSRF 校验，两份名单仍应保持一致。

只读检查示例：

```bash
systemctl cat english-ai
sudo nginx -T
ss -lntp
```

## 1. 服务器一次性配置

以下示例面向 Debian/Ubuntu；先按服务器实际发行版调整。安装 Python 3.10+（建议 3.12）、python3-venv、Nginx、certbot、Git、OpenSSL。前端 Node 版本以当前 Vite 的 engines 为准，使用兼容的 Node LTS。

确认采用 `/opt/english-ai` 且该目录没有既有项目时：

```bash
sudo install -d -o "$USER" -g "$USER" /opt/english-ai
git clone <已确认的仓库地址> /opt/english-ai
cd /opt/english-ai
python3 -m venv /opt/english-ai/venv
/opt/english-ai/venv/bin/pip install -r backend/requirements.txt
```

**当前依赖清单的已知缺项**：main.py 已使用 `openai`、`python-dotenv`，但 requirements.txt 没有声明。此任务不修改该清单；首次部署需补装这两个现有运行依赖，并在后续依赖整理中锁定版本。不能只装 requirements 就宣称可以启动。

```bash
/opt/english-ai/venv/bin/pip install openai python-dotenv
/opt/english-ai/venv/bin/pip check
cd /opt/english-ai/frontend
npm ci
npm run build
```

有 package-lock.json 时使用 npm ci；无锁文件时才使用 npm install。词汇/语料工具可能另需 FFmpeg 或其既有可选依赖，应按启用的功能验收，不代表基础登录上线后所有教师工具均可用。

### 环境文件与写权限

- 仅当真实 `.env` 不存在时复制 `.env.example`，填写密钥和域名；不要覆盖已有文件。
- 使用 root 所有、权限 600 的 `.env` 供 systemd 读取并注入；服务代码不要以 root 运行。
- 确认 `www-data` 用户存在、对项目与 venv 有读取/执行权限，对两种数据库的**父目录**和数据库文件有写权限（SQLite 还要创建 journal 文件）。只授权必要数据目录，不要递归把整个仓库交给 www-data。
- 根据实际启用的教师上传/TTS 功能另行授权相应数据目录，本模板不自动放宽所有目录。

```bash
sudo install -d -o www-data -g www-data -m 750 /opt/english-ai/backend/auth/data
# 对已有 listening/data 及已有数据库，先确认数据已备份，再按上述原则设置权限。
```

### 首次 HTTPS 证书

先确认 DNS 指向本机，80/443 在安全组与防火墙开放，8000 不对公网开放。
没有证书时**不要先启用引用不存在证书的 443 配置**。

先在经过确认的 Nginx http include 目录放入临时 HTTP-only 站点（域名需替换）：

```nginx
server {
    listen 80;
    server_name 你的域名;
    location ^~ /.well-known/acme-challenge/ { root /var/lib/letsencrypt; }
    location / { return 503; }
}
```

这是新站点引导配置，不要覆盖已有线上服务。在现有站点上签发证书时，只协调添加 challenge 路径。

```bash
sudo install -d -m 755 /var/lib/letsencrypt
sudo nginx -t
sudo systemctl reload nginx
sudo certbot certonly --webroot -w /var/lib/letsencrypt -d 你的域名
```

证书签发后，用填写完实际域名/路径的 deploy/nginx.conf 替换**该站点配置**，不要替换主 `/etc/nginx/nginx.conf`。保留 HTTP-01 challenge 路径用于续期；成功续期后需 reload Nginx，配置 certbot deploy hook 或发行版提供的等效机制，并测试 `certbot renew --dry-run`。

### 安装服务与站点

- 先替换 service/nginx 中所有域名和路径；service 的 WorkingDirectory 必须是 backend/。
- Nginx 主 `http {}` 必须 include mime.types 和本文件所在目录；limit_req_zone 只能在 http 上下文定义一次。
- 模板将 10r/m 限制仅用于 login/register，不限制听力心跳和普通 API。共享出口 IP 可能误伤，需要观察 429。
- `client_max_body_size 2m` 是当前模板约束，大音频上传会得到 413；若启用教师上传，需单独评估上传路径限额，不要无条件放宽所有 API。

```bash
sudo install -m 644 deploy/english-ai.service /etc/systemd/system/english-ai.service
# 按真实 Nginx include 布局安装，避免同时在 sites-enabled 再引入同一站点。
sudo install -m 644 deploy/nginx.conf /etc/nginx/conf.d/english-ai.conf
sudo systemd-analyze verify /etc/systemd/system/english-ai.service
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now english-ai
sudo systemctl reload nginx
```

## 2. 每次部署

1. 确认工作树、待发布提交、现有服务和数据库路径；记录回滚 commit/上一份前端构建。
2. 使用 SQLite 在线 backup API 或在停止写入的维护窗口备份两个数据库；不要在有写入时只复制主文件，尤其不要漏掉可能存在的 WAL。
3. 在确认的项目目录执行 `git pull --ff-only`，不使用 hard reset 清除线上未知修改。
4. 依赖变化时运行 venv 的 `pip install -r backend/requirements.txt`；注意上述两个缺项。
5. 前端有变化时 `cd frontend && npm ci && npm run build`。推荐在发布副本中构建、验证后切换，避免 Vite 清理 dist 时线上出现短暂缺文件。
6. 验证环境配置；后端或环境有变化时 `sudo systemctl restart english-ai`。
7. service 有变化才 daemon-reload；Nginx 有变化须先 nginx -t 再 reload。
8. 完成启动验证，检查日志/错误率，失败时恢复已验证的代码/静态构建并重启。数据库迁移回滚必须单独评估，不能盲目覆盖数据库。

首次初始化 listening repository 会执行 owner_id 等已有迁移。不要为了“测试启动”直接操作真实库；先在副本验证迁移和权限。

## 3. 环境变量清单（/opt/english-ai/backend/.env）

- [ ] DEEPSEEK_API_KEY 已填写真实有效值。
- [ ] AUTH_JWT_SECRET 已填写随机密钥（≥32 字节），所有 worker 一致；`openssl rand -hex 32` 生成。
- [ ] AUTH_COOKIE_SECURE=true。
- [ ] AUTH_ALLOWED_ORIGINS=https://你的实际域名（按需逗号分隔）。
- [ ] CORS_ALLOWED_ORIGINS=https://你的实际域名；禁止 `*`，不带路径或尾斜杠。
- [ ] 若覆盖数据库路径，AUTH_DB_PATH/LISTENING_DB_PATH 使用经过确认的绝对路径。
- [ ] LISTENING_UNSAFE_FAST_DB 未设置（生产禁止）。
- [ ] ALLOW_UNRELEASED_LISTENING_V2 未设置（生产禁止绕过闸门）。
- [ ] TEACHER_TOKEN 按需独立生成；不设置时教师端点拒绝请求。

当前 JWT 密钥不是启动即校验：缺失时进程仍可能运行，但认证返回 503，所以 active(running) 不足以证明登录可用。systemd EnvironmentFile 在模块导入前注入变量，能避免仅靠 main.py 的 load_dotenv 晚于 listening 导入所带来的数据库路径读取时序问题。

## 4. 启动验证

```bash
sudo systemctl status english-ai --no-pager
sudo journalctl -u english-ai -n 100 --no-pager
curl -i https://你的域名/api/auth/me
curl -I http://你的域名/
curl -i https://你的域名/
```

- [ ] 服务 active(running)；日志无 ImportError、数据库权限或锁错误。
- [ ] 未登录 `/api/auth/me` 返回 401（正常）。首页返回 HTML，HTTP 首页跳转 HTTPS。
- [ ] `/login`、`/register` 深链接和静态 JS/CSS 正常加载，ICP footer 正常。
- [ ] 浏览器注册专用测试账号、登录、刷新 `/api/auth/me` 返回账号、登出后返回 401。
- [ ] 登录 cookie 包含 HttpOnly/Secure/SameSite=Lax；客户端 POST 保留 X-Auth-Request: 1。
- [ ] 在专用测试 IP 低风险验证 login/register 的 429 行为；普通 listening API 不应被 auth_limit 限流。
- [ ] 不携带真实密码的 CORS 预检返回正确 Origin 与 allow-credentials；未许可 Origin 不返回许可头：

```bash
curl -i -X OPTIONS https://你的域名/api/auth/login \
  -H 'Origin: https://你的域名' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: content-type,x-auth-request'
```

- [ ] student_release_allowed 仍为 false；站点基础登录可用不代表 V2 未审核材料已允许发布。
- [ ] 先在隔离环境执行 `python backend/tests/run_student_auth_regression.py tests -x -q`，不要直接运行会备份后重写真实 JSON 的旧测试入口。

## 5. 已知限制与上线决策

这些是需要负责人接受或继续整改的限制，不能统一标为“不影响上线”：

- 匿名请求（包括无效 cookie）绕过当前 attempt owner 校验；这仍允许匿名注入。完整封堵需后续强制登录/权限设计。
- 登录前匿名历史不自动合并到账号。
- 只有本轮指定的写入路径检查 owner；不是全站资源权限保护。邮箱未验证，密码重置也仅为提示 UI。
- SQLite 当前未启用 WAL；即使启用 WAL，也只能改善读写并行，不能消除单写者锁等待。2 workers 是起点，需要基于真实请求量、写频率、锁等待和错误率压测。约 1000 用户不等于 1000 并发；没有可靠的“500 并发写”通用迁移阈值。出现持续写瓶颈时评估 PostgreSQL。
- 现有 requirements 缺少两个基础入口依赖；首次部署必须补装并检查。
- 密钥、真实域名、有效证书、数据库权限和素材恢复未验证前，不能把模板当成已经完成的线上部署。

## 6. 参考与本地验证边界

2026-09-08 本地验证：后端 246 项通过（22.12 秒）；使用 main.py 实际 CORS 配置语句的 5 项预检通过（开发双默认来源、生产多来源去空白、拒绝外部来源、空名单）。测试没有导入 main.py 或读取真实 .env，不代表真实密钥/完整进程已验证。
service 的节、续行与命令参数，以及 Nginx 括号/限流上下文静态检查通过；未运行原生配置校验。
真实 listening.db SHA-256 保持 AEDEB601197E859E3ECA5E41DCB809288352FCEECDE6E4F5648F7B6B19628DC0；student_release_allowed 仍为 false。

- Nginx limit_req 官方文档：https://nginx.org/en/docs/http/ngx_http_limit_req_module.html
- Uvicorn 代理头设置：https://www.uvicorn.org/settings/
- 本地是 Windows 环境，生成模板不代表已运行 Linux 的 systemd-analyze 或服务器 nginx -t；上述原生验收命令必须在目标服务器执行。
