# 图片分享、人工审核与图片墙：实现及部署说明

日期：2026-09-20。状态：本地实现与验证；未部署线上。

## 1. 复用现有项目的方式

- Vue 3 / TypeScript / Vite，复用站点 CSS 变量、顶端账户导航和原有 footer。
- 使用现有 HttpOnly JWT 登录，上传者从登录凭证读取，不接受客户端指定身份。
- 当前仓库**没有账号管理员角色表**，现有教师权限是 `TEACHER_TOKEN` 口令。
  本功能调用原有 `require_teacher`，同时要求登录，审核人保存为当前账号 UUID。
  因此“管理员”指**已登录并通过教师口令验证的人**，不是新建的账号角色。
- 管理口令仍通过现有 sessionStorage 工具管理，只用请求头发送；图片接口不接受 URL 中的口令。
- 复用 `auth.models.database()` 的 SQLite 连接和事务，在现有 **auth.db** 增加图片表。
  不创建另一套认证，不改听力表和真实 listening.db。
- 已有上传功能是教师语料音频的本地文件存储，没有发现可直接复用的图片对象存储。
  图片采取独立私有目录及后端鉴权访问，不复用公开音频路径。

## 2. 学生和管理员怎么用

| 页面 | 用途 |
| --- | --- |
| `/gallery` | 无需登录，只显示通过审核的图片，按审核时间倒序，24 张一页 |
| `/gallery/upload` | 登录后选择或拖入一张图片、预览、移除重选、填可选说明、提交审核 |
| `/gallery/mine` | 只看自己的图片、中文审核状态及拒绝原因，分页 |
| `/admin/gallery` | 登录后输入现有教师口令，网格审核、筛选、分页、查看大图、通过/拒绝/删除 |

四条路由共用 `GalleryView.vue`，避免复制布局和列表逻辑。全站顶部添加图片墙入口。
管理员导航只有口令被后端验证后才出现；直接访问管理 URL 不会绕过后端验证。

上传限制：JPG/JPEG/PNG/WebP，单文件 10 MiB，1600 万像素、最长边 8000px。
不接受 GIF/SVG、动态 PNG/WebP、其他文档或脚本。每个账号滚动 24 小时最多提交 20 张。
拒绝或删除也不会返还当天额度，避免通过反复删除绕过限额。

图片和说明一起人工审核。上传后不能自行修改说明，避免通过后更换为未审核内容。
公开卡片不展示邮箱、账号 ID、原始文件名、审核员身份或拒绝原因。账号导航中的邮箱仅属于当前登录者。
没有添加公开昵称，因为现有账号模型没有公开昵称字段。

## 3. 文件清单

### 修改的已有文件

| 文件 | 本次修改 |
| --- | --- |
| `.gitignore` | 排除本地私有图片目录 |
| `backend/main.py` | 注册图片路由及请求体大小限制中间件 |
| `backend/requirements.txt` | 增加 Pillow 依赖 |
| `frontend/src/router/index.ts` | 新增四条图片路由 |
| `frontend/src/components/AuthStatus.vue` | 增加全站图片墙入口；登出时清除会话教师口令 |
| `frontend/src/views/auth/LoginView.vue` | 为四个固定图片页面增加登录返回白名单 |
| `deploy/nginx.conf` | 模板添加专属上传大小限制及限速，不改现有其他 API 规则 |

以上部分文件此前已有未提交改动；本次只追加相关逻辑，没有撤销先前修改。

### 新增文件

- `backend/gallery/__init__.py`：模块用途说明。
- `backend/gallery/storage.py`：复用账户数据库、幂等建表、安全文件路径。
- `backend/gallery/router.py`：上传、列表、图片读取、权限和人工审核。
- `backend/gallery/limits.py`：在解析 multipart 前限制整体请求体，包括无 Content-Length 的请求。
- `backend/tests/test_gallery.py`：隔离数据库/目录的安全回归测试。
- `backend/tests/preview_gallery.py`：仅本地使用的一次性完整应用预览，合成测试图片与测试账号。
- `frontend/src/services/galleryApi.ts`：类型、Cookie 请求、管理请求头、私有图片获取。
- `frontend/src/components/gallery/GalleryPhoto.vue`：带鉴权头获取缩略图/原图并管理临时预览地址。
- `frontend/src/views/gallery/GalleryView.vue`：四个页面共用的响应式布局及交互。
- 本文档。

## 4. API 与数据表

| 方法及路径 | 权限 |
| --- | --- |
| `POST /api/gallery/upload` | 必须登录；multipart 的 `file` 和可选 `caption` |
| `GET /api/gallery/mine` | 必须登录，SQL 按当前账号过滤 |
| `GET /api/gallery/public` | 公开，SQL 固定 `status='approved'` |
| `GET /api/gallery/images/{id}` | 通过审核可公开；否则仅本人或已验证管理员 |
| `GET /api/gallery/images/{id}/thumbnail` | 与原图相同权限 |
| `GET /api/admin/gallery` | 登录 + 教师口令，`status=pending/approved/rejected/all` |
| `POST /api/admin/gallery/{id}/approve` | 登录 + 教师口令 |
| `POST /api/admin/gallery/{id}/reject` | 登录 + 教师口令，JSON `{"reject_reason":"可选原因"}` |
| `DELETE /api/admin/gallery/{id}` | 登录 + 教师口令 |

列表支持 `page` 和 `page_size`；默认 24，最大 48。所有写入继续使用现有 `X-Auth-Request: 1` 和来源校验。

新增 `gallery_images`：需求列全部具备，另加 `deleted_at` 支持软删除。
`file_size` 为重新编码后的大图体积，`mime_type` 为实际保存的 `image/webp`。
`image_url` / `thumbnail_url` 是后端受控访问地址，不是静态文件路径。
新增 `gallery_audit`：保存图片 ID、审核账号 ID、时间、操作；删除图片记录后也保留审核轨迹。
另发出 Python 审核日志，沿用服务日志收集方式；数据库审计记录不依赖日志级别。

## 5. 数据库迁移

当前项目使用原生 sqlite3，无 Alembic。首次使用图片 API 时自动、幂等创建新表和索引。
**不需要手工创建表，不需要执行 Alembic 命令。** 已有用户不受影响。

如希望上线前主动建表，在服务器**实际后端虚拟环境**和 `backend/` 工作目录中运行：

```bash
python -c 'from dotenv import load_dotenv
load_dotenv()
from gallery.storage import gallery_database
with gallery_database():
    pass
print("gallery tables ready")'
```

务必使用现有生产 `AUTH_DB_PATH`，不要为了这个功能更换账户数据库位置。
操作前按原部署流程备份 auth.db；同时备份图片目录，数据库与文件需要一起恢复。

## 6. 存储目录、环境与 Linux 权限

默认路径是项目根目录下 `uploads/gallery/`，不会由 FastAPI 静态挂载。
生产可显式设置（以下沿用此前提供的项目路径，**本轮未连接服务器确认**）：

```dotenv
GALLERY_UPLOAD_DIR=/var/www/english-ai/uploads/gallery
```

确认现有 `AUTH_ALLOWED_ORIGINS` 包含 `https://zaixuexidexiaoq.cn`，保留其他仍需使用的合法来源。
继续使用现有 `AUTH_JWT_SECRET`、`AUTH_COOKIE_SECURE=true` 和 `TEACHER_TOKEN`，不要把生产密钥提交到 Git。
教师口令未配置时管理员接口关闭，不会自动选一个普通学生当管理员。

目录在第一次上传时可自动创建，但生产建议提前建立。当前 systemd 模板用户为 `www-data`，
先核对线上实际服务用户；若不同，下面的 owner/group 要对应修改：

```bash
sudo install -d -m 0750 -o www-data -g www-data /var/www/english-ai/uploads/gallery
```

后端服务用户需要目录读写权限及 auth.db 所在目录的 SQLite journal 写权限。
新图片权限为 0640；不要使用 0777。Nginx 无需读取图片目录。
不新增可执行文件，不保存用户上传的原始二进制，不允许用户决定最终文件名。
新文件是随机 UUID 命名的 WebP，以及最长边 600px 的 WebP 缩略图。

## 7. Nginx 调整（仅上传接口）

现有模板 `/api/` 限制为 2m，不能上传完整 10 MiB 图片。
因此需要为上传接口单独放宽至 11m（包含 multipart 开销），其他接口维持原限制。
**不要为 uploads/gallery 添加 root、alias 或公开静态路由。** 原图和缩略图全部继续走 FastAPI 校验。

以下 zone 定义放在 `http {}` 内，仅定义一次；如果当前站点文件在 http 下被 include，可放在该文件 server 外：

```nginx
limit_req_zone $binary_remote_addr zone=gallery_upload_limit:10m rate=10r/m;
```

在现有 HTTPS `server {}` 内，新增以下完整 location，不替换原 `/api/`：

```nginx
location = /api/gallery/upload {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    client_max_body_size 11m;
    client_body_timeout 30s;
    limit_req zone=gallery_upload_limit burst=3 nodelay;
    limit_req_status 429;
    proxy_read_timeout 60s;
}
```

如生产后端不是 8000 端口，必须沿用实际 upstream。Nginx 限速是共享出口 IP 维度，校园网试运行时需观察 429。
配置合并到**实际正在使用的站点文件**后执行 `sudo nginx -t`，成功才 `sudo systemctl reload nginx`。
本地没有 Nginx，未声称已经通过服务器的 `nginx -t`。

## 8. 构建与重启

先在现有后端虚拟环境安装依赖：

```bash
python -m pip install -r requirements.txt
```

以上在 `backend/` 执行。本地验证 Pillow 版本 12.3.0；不要使用项目中已失效的 Windows venv 启动器。

前端在 `frontend/` 执行：

```bash
npm run build
```

通过后仍按原有前端发布流程部署 `frontend/dist`；不是要求把整个仓库目录设为 Nginx web root。
后端新增模块、依赖和环境变量后需要重启现有服务：

```bash
sudo systemctl restart english-ai
sudo systemctl status english-ai --no-pager
```

`english-ai` 是仓库模板服务名，执行前核对线上实际服务名和 Python 路径。本轮未部署或重启任何线上服务。

## 9. 手工验收

1. 未登录打开 `/gallery`：只能看到已通过的图片。打开 `/gallery/upload`：提示登录。
2. 学生 A 登录，选择 JPG/PNG/WebP，检查预览、移除、重新选择、可选说明。
3. 提交后看到“上传成功，图片将在审核通过后展示。”；我的图片显示“审核中”。
4. 在无痕窗口及学生 B 账号下访问该图片/缩略图地址：都应 404。B 的我的图片里也不能出现 A 的待审记录。
5. 普通账号直接调用管理 API：403；无登录：401。仅知道图片 ID 不足以审核、删除或查看私有图片。
6. 管理员登录后进入 `/admin/gallery`，输入现有教师口令，默认看到待审网格。点击缩略图查看完整大图。
7. 点击通过：图片进入公开墙。退出登录或无痕查看，仍能看到**已通过**的图片，但看不到上传账号隐私。
8. 管理端切换“已通过”并拒绝图片，填写原因：图片立即从公开 API 消失，新的原图/缩略图请求变 404；本人可看拒绝原因。
9. 删除另一张测试图片：列表消失、原图和缩略图被清理；文件事先不存在也不应报错。
10. 检查分页及手机布局；测试超过 10MB、伪装扩展名、非图片文件被拒绝。

已经公开下载或截图到他人设备的图片无法远程收回。`no-store` 和权限复检用于阻止后续请求继续读取撤下图片，不承诺抹除既往下载。

## 10. 本地验证与安全检查

- 完整 FastAPI 应用在一次性数据库和上传目录下正常启动；没有调用外部 AI。
- 前端 `npm run build` 通过，包含 TypeScript 检查。
- 完整后端测试最终结果：**287 passed in 72.80s**，其中图片功能新增 17 项；执行命令为 `python backend/tests/run_student_auth_regression.py tests -x -q`，使用可用的 Python 运行环境。
- 后端测试通过隔离 runner 执行；新增覆盖权限、IDOR、枚举、公开白名单、MIME/真实格式、文件大小、尺寸、动态图片、解压炸弹、EXIF 清理、缩略图、CSRF、额度、分页、审核日志、删除失败后隐藏及重试。
- 使用浏览器技能检查了桌面页面与 390px 手机视口，验证了登录、图片选择预览、提交、我的图片状态、教师口令、审核网格、通过后公开；手机墙没有横向溢出。
- 未审核和拒绝图片没有静态公开路径；图片请求不携带 URL 密钥，响应为 `private, no-store` 和 `nosniff`。
- 后端文件名只由 UUID 生成，原文件名仅作元数据。重新生成像素并编码为 WebP，不携带原始 EXIF/GPS/ICC/XMP。
- 业务不会自动通过审核，不调用 AI 替代人工审核，不改变任何听力 release/profile gate。
- 真实 `backend/listening/data/listening.db` 的 SHA256 保持：
  `AEDEB601197E859E3ECA5E41DCB809288352FCEECDE6E4F5648F7B6B19628DC0`。

上线时还需要正常执行人工内容审核、定期备份、磁盘容量与限速告警；代码的格式验证不能代替人工判断图片内容。
