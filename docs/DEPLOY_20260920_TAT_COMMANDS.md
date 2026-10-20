# 部署方案 2026-09-20 — Gallery + 表达修正 + 听力学习 MVP

日期：2026-09-20。模型：Opus 4.6。状态：命令已生成，未执行。

## 本次部署内容

| 批次 | 内容 | 本地验证 |
|---|---|---|
| Gallery 图片墙 | 上传/审核/公开墙 + 点赞/排序/30张 | 20项gallery测试+全套289通过 |
| 表达内容修正 | 39场景/49题/12对话重写 + 12个r2音频 + revision版本门 | Opus 5独立复核通过 |
| 听力学习 MVP | 42词条+14难句+学习路由 + 前端优化 | MVP签字通过 |

## 前置条件

1. **本地 push**：在 Windows 终端执行 `cd D:\kimi-workspace\english-ai && git push github main`
2. 确认推送成功后，按下面顺序在**腾讯云 TAT 控制台**逐条执行

---

## TAT-0：探测服务器实际布局

> 目的：确认项目路径、服务名、Nginx 配置位置。**只读，不改任何东西。**

```bash
#!/bin/bash
set -e
echo "=== systemd service ==="
systemctl cat english-ai 2>/dev/null | head -20 || echo "服务名不是 english-ai，请用 systemctl list-units | grep -i english 查找"

echo ""
echo "=== 项目路径 ==="
for p in /opt/english-ai /var/www/english-ai; do
  [ -d "$p/.git" ] && echo "GIT仓库: $p" && ls "$p/backend/main.py" 2>/dev/null && echo "确认: $p"
done

echo ""
echo "=== Nginx 站点配置 ==="
sudo nginx -T 2>/dev/null | grep -E "server_name|root |proxy_pass|include |client_max_body" | head -20

echo ""
echo "=== 当前 .env（不显示密钥值）==="
for p in /opt/english-ai/backend/.env /var/www/english-ai/backend/.env; do
  [ -f "$p" ] && echo "找到: $p" && grep -oP '^\w+=' "$p" | sort
done

echo ""
echo "=== 磁盘空间 ==="
df -h / | tail -1

echo ""
echo "=== Node/Python 版本 ==="
node -v 2>/dev/null || echo "node 未安装"
python3 --version 2>/dev/null
```

**跑完把输出贴给我**，我根据实际路径调整后续命令。

---

下面的命令假设路径是 `/opt/english-ai`。如果探测发现是 `/var/www/english-ai`，全文替换即可。

## TAT-1：备份数据库

```bash
#!/bin/bash
set -e
PROJECT=/opt/english-ai
BACKUP_DIR="$PROJECT/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 备份 auth.db（gallery 表在这里）
AUTH_DB=$(grep -oP 'AUTH_DB_PATH=\K.*' "$PROJECT/backend/.env" 2>/dev/null || echo "$PROJECT/backend/auth/data/auth.db")
if [ -f "$AUTH_DB" ]; then
  sqlite3 "$AUTH_DB" ".backup '$BACKUP_DIR/auth.db.bak'"
  echo "auth.db 已备份到 $BACKUP_DIR/auth.db.bak ($(du -h "$BACKUP_DIR/auth.db.bak" | cut -f1))"
else
  echo "警告：未找到 auth.db at $AUTH_DB"
fi

# 备份 listening.db（本次不改，但留安全线）
LISTEN_DB=$(grep -oP 'LISTENING_DB_PATH=\K.*' "$PROJECT/backend/.env" 2>/dev/null || echo "$PROJECT/backend/listening/data/listening.db")
if [ -f "$LISTEN_DB" ]; then
  sqlite3 "$LISTEN_DB" ".backup '$BACKUP_DIR/listening.db.bak'"
  echo "listening.db 已备份到 $BACKUP_DIR/listening.db.bak ($(du -h "$BACKUP_DIR/listening.db.bak" | cut -f1))"
fi

# 备份当前前端构建（回滚用）
if [ -d "$PROJECT/frontend/dist" ]; then
  cp -a "$PROJECT/frontend/dist" "$BACKUP_DIR/dist_backup"
  echo "前端 dist 已备份"
fi

echo "备份完成: $BACKUP_DIR"
ls -la "$BACKUP_DIR/"
```

## TAT-2：拉取代码 + 安装依赖

```bash
#!/bin/bash
set -e
PROJECT=/opt/english-ai
cd "$PROJECT"

# 拉取代码
git pull --ff-only
echo "最新 commit: $(git log --oneline -3)"

# 安装后端依赖（含新增 Pillow）
"$PROJECT/venv/bin/pip" install -r backend/requirements.txt -q
# 补装已知缺项
"$PROJECT/venv/bin/pip" install openai python-dotenv -q
echo ""
echo "=== pip check ==="
"$PROJECT/venv/bin/pip" check 2>&1 | tail -5
echo ""
echo "=== Pillow 版本 ==="
"$PROJECT/venv/bin/python" -c "import PIL; print(PIL.__version__)"
```

## TAT-3：创建 Gallery 上传目录 + 更新 .env

```bash
#!/bin/bash
set -e
PROJECT=/opt/english-ai
GALLERY_DIR="$PROJECT/uploads/gallery"

# 确认运行用户
SERVICE_USER=$(grep -oP 'User=\K\w+' /etc/systemd/system/english-ai.service 2>/dev/null || echo "www-data")
echo "服务用户: $SERVICE_USER"

# 创建目录
sudo install -d -m 0750 -o "$SERVICE_USER" -g "$SERVICE_USER" "$GALLERY_DIR"
echo "Gallery 目录已创建: $GALLERY_DIR"
ls -la "$GALLERY_DIR/.."

# 添加 GALLERY_UPLOAD_DIR 到 .env（如果不存在）
ENV_FILE="$PROJECT/backend/.env"
if ! grep -q "^GALLERY_UPLOAD_DIR=" "$ENV_FILE" 2>/dev/null; then
  echo "" >> "$ENV_FILE"
  echo "GALLERY_UPLOAD_DIR=$GALLERY_DIR" >> "$ENV_FILE"
  echo "已添加 GALLERY_UPLOAD_DIR=$GALLERY_DIR"
else
  echo "GALLERY_UPLOAD_DIR 已存在，跳过"
fi

# 确认 AUTH_ALLOWED_ORIGINS 包含域名
grep "AUTH_ALLOWED_ORIGINS" "$ENV_FILE" || echo "警告：.env 中未找到 AUTH_ALLOWED_ORIGINS"
```

## TAT-4：更新 Nginx 配置

> 本步骤需要在现有 Nginx 站点配置中添加 gallery 上传专用 location。

```bash
#!/bin/bash
set -e

# 找到实际的站点配置文件
NGINX_CONF=""
for f in /etc/nginx/conf.d/english-ai.conf /etc/nginx/sites-enabled/english-ai /etc/nginx/sites-enabled/default; do
  if [ -f "$f" ] && grep -q "zaixuexidexiaoq" "$f" 2>/dev/null; then
    NGINX_CONF="$f"
    break
  fi
done

if [ -z "$NGINX_CONF" ]; then
  echo "未找到站点配置，请手动确认 Nginx 配置文件路径"
  sudo nginx -T 2>/dev/null | grep -B2 "zaixuexidexiaoq" | head -10
  exit 1
fi

echo "站点配置文件: $NGINX_CONF"

# 检查是否已有 gallery_upload_limit zone
if grep -q "gallery_upload_limit" "$NGINX_CONF"; then
  echo "gallery_upload_limit 已存在，跳过 Nginx 修改"
else
  echo "需要添加 gallery 上传配置。当前配置备份..."
  sudo cp "$NGINX_CONF" "${NGINX_CONF}.bak.$(date +%Y%m%d)"
  
  # 在 limit_req_zone 行后追加 gallery zone（如果有现有 zone）
  if grep -q "limit_req_zone" "$NGINX_CONF"; then
    sudo sed -i '/^limit_req_zone.*auth_limit/a limit_req_zone $binary_remote_addr zone=gallery_upload_limit:10m rate=10r/m;' "$NGINX_CONF"
  else
    # 在文件开头添加两个 zone
    sudo sed -i '1i limit_req_zone $binary_remote_addr zone=gallery_upload_limit:10m rate=10r/m;' "$NGINX_CONF"
  fi
  
  # 在 /api/ location 前插入 gallery upload location
  sudo sed -i '/location \/api\//i \
    # Gallery 上传接口：放宽到 11m，独立限速\
    location = /api/gallery/upload {\
        proxy_pass http://127.0.0.1:8000;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        client_max_body_size 11m;\
        client_body_timeout 30s;\
        limit_req zone=gallery_upload_limit burst=3 nodelay;\
        limit_req_status 429;\
        proxy_read_timeout 60s;\
    }\
' "$NGINX_CONF"
  
  echo "Nginx 配置已更新"
fi

echo ""
echo "=== 验证 Nginx 配置 ==="
sudo nginx -t
```

## TAT-5：构建前端

```bash
#!/bin/bash
set -e
PROJECT=/opt/english-ai
cd "$PROJECT/frontend"

npm ci --prefer-offline 2>&1 | tail -3
npm run build 2>&1 | tail -10

echo ""
echo "=== 构建产物 ==="
ls -la dist/index.html
du -sh dist/
```

## TAT-6：重启服务 + 验收

```bash
#!/bin/bash
set -e

echo "=== 重启后端 ==="
sudo systemctl restart english-ai
sleep 2
sudo systemctl status english-ai --no-pager | head -15

echo ""
echo "=== 重载 Nginx ==="
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo "=== 启动日志（检查有无 ImportError）==="
sudo journalctl -u english-ai -n 30 --no-pager 2>&1 | tail -20

echo ""
echo "=== API 基础验证 ==="
# 首页
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://zaixuexidexiaoq.cn/)
echo "首页: $HTTP_CODE (期望 200)"

# 未登录 auth/me
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://zaixuexidexiaoq.cn/api/auth/me)
echo "auth/me 未登录: $HTTP_CODE (期望 401)"

# Gallery 公开列表
GALLERY=$(curl -s https://zaixuexidexiaoq.cn/api/gallery/public)
echo "gallery/public: $(echo "$GALLERY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'page_size={d[\"page_size\"]}, total={d[\"total\"]}')" 2>/dev/null || echo "$GALLERY" | head -1)"

# Gallery 排序参数
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://zaixuexidexiaoq.cn/api/gallery/public?sort=popular")
echo "gallery sort=popular: $HTTP_CODE (期望 200)"

# Gallery 点赞（未登录应拒绝）
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "https://zaixuexidexiaoq.cn/api/gallery/images/00000000000000000000000000000000/like")
echo "gallery like 未登录: $HTTP_CODE (期望 401 或 403)"

echo ""
echo "=== listening.db SHA256 ==="
LISTEN_DB=$(grep -oP 'LISTENING_DB_PATH=\K.*' /opt/english-ai/backend/.env 2>/dev/null || echo "/opt/english-ai/backend/listening/data/listening.db")
sha256sum "$LISTEN_DB" 2>/dev/null | awk '{print $1}'
echo "期望: aedeb601197e859e3eca5e41dcb809288352fceecde6e4f5648f7b6b19628dc0"

echo ""
echo "=== student_release_allowed ==="
python3 -c "
import sqlite3, os
db = os.environ.get('LISTENING_DB_PATH', '/opt/english-ai/backend/listening/data/listening.db')
conn = sqlite3.connect(db)
r = conn.execute('SELECT value FROM metadata WHERE key=\"student_release_allowed\"').fetchone()
print(f'student_release_allowed = {r[0] if r else \"not set (默认false)\"}')
conn.close()
" 2>/dev/null || echo "无法检查 student_release_allowed"
```

---

## 回滚方案

如果部署后出现问题：

```bash
#!/bin/bash
PROJECT=/opt/english-ai
# 找最近的备份
BACKUP=$(ls -td "$PROJECT/backups/"* 2>/dev/null | head -1)
echo "回滚到: $BACKUP"

# 1. 回退代码
cd "$PROJECT"
git log --oneline -5
# git reset --hard <上一个好的commit>
# 或: git revert HEAD~3..HEAD

# 2. 恢复前端
sudo cp -a "$BACKUP/dist_backup" "$PROJECT/frontend/dist"

# 3. 恢复数据库（如果 gallery 表出问题）
# sqlite3 <AUTH_DB_PATH> ".restore '$BACKUP/auth.db.bak'"

# 4. 恢复 Nginx
# sudo cp "${NGINX_CONF}.bak.20260920" "$NGINX_CONF"

# 5. 重启
sudo systemctl restart english-ai
sudo nginx -t && sudo systemctl reload nginx
```

---

## 部署后浏览器验收清单

1. 打开 `https://zaixuexidexiaoq.cn/gallery` — 应显示公开图片墙（可能为空），有「最新/最热」排序标签
2. 点「分享图片」→ 提示登录
3. 登录后上传一张测试图片 + 写说明 → "上传成功，图片将在审核通过后展示"
4. 「我的图片」→ 显示"审核中"
5. 管理员登录 → `/admin/gallery` → 输入教师口令 → 看到待审图片 → 通过
6. 回到图片墙 → 图片已公开，可点赞 ❤️
7. 切换「最热」排序 → 按赞数排序
8. 打开表达练习 → 验证修改后的场景能正常播放（特别是 r2 音频）
9. 打开听力学习页面 → 验证词条和难句加载正常
