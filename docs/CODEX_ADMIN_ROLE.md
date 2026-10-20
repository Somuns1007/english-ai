# Codex Prompt ⑤ — 账户级管理员角色系统

## 任务目标

为 `303528771@qq.com` 建立**账户级管理员最高权限**，取代当前的 `TEACHER_TOKEN` 口令验证。

## 现有权限架构（你必须理解）

当前系统**没有角色字段**：

1. **users 表**（`auth/data/auth.db`）只有 `id, email, password_hash, created_at, is_active`——没有 role 字段
2. **Gallery 管理员鉴权**（`gallery/router.py:31-39` 的 `administrator` 函数）靠 `require_teacher` 验证 `X-Teacher-Token` 头，与 `.env` 中的 `TEACHER_TOKEN` 比对
3. **听力管理接口**（`listening/router.py:63+` 的 `require_teacher`）同样靠 `TEACHER_TOKEN`
4. **前端**（`AuthStatus.vue` + `GalleryView.vue`）：用户需要在 Gallery 审核页手动输入教师口令，存在 sessionStorage，随页面关闭清除
5. **User Pydantic model**（`auth/models.py`）只返回 `id, email, created_at, is_active`

## 要做什么

### 1. 数据库：给 users 表加 `role` 字段

```sql
ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user';
```

角色值：
- `'user'`：普通用户（默认）
- `'admin'`：管理员（最高权限）

在 `auth/models.py` 的 `database()` 函数中，在 `CREATE TABLE IF NOT EXISTS` 之后追加一个 migration：
```python
# Migration: add role column if missing
try:
    connection.execute("SELECT role FROM users LIMIT 0")
except sqlite3.OperationalError:
    connection.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
```

**然后把 `303528771@qq.com` 设为 admin**——同样写在 migration 里：
```python
connection.execute("UPDATE users SET role='admin' WHERE email='303528771@qq.com'")
```

### 2. Pydantic model 更新

`auth/models.py` 的 `User` class 加一个字段：
```python
class User(BaseModel):
    id: str
    email: str
    created_at: str
    is_active: bool
    role: str = "user"
```

### 3. 认证服务更新

`auth/service.py` 的 `public_user(row)` 已经用 `User.model_fields` 动态取字段，加了 `role` 字段后自动包含，无需改动。

但需要确认 `get_user_by_token` 返回的 User 包含 role。

### 4. Gallery 管理员鉴权重构

`gallery/router.py` 的 `administrator` 函数改为**双通道**：
- **新通道**：如果当前登录用户 `role == 'admin'`，直接通过，不需要 teacher token
- **旧通道**：如果不是 admin 角色，仍然走 `require_teacher` 验证 teacher token（向后兼容）

```python
def administrator(user: User = Depends(current_user), x_teacher_token: str | None = Header(None)):
    if user.role == 'admin':
        return user
    # Fallback: teacher token for non-admin accounts
    try:
        require_teacher(x_teacher_token=x_teacher_token, token=None)
    except HTTPException as exc:
        if exc.status_code == 401:
            raise HTTPException(403, "仅管理员可以操作") from None
        raise
    return user
```

### 5. 前端：/api/auth/me 返回 role，Gallery 自动跳过口令输入

**AuthStatus.vue**：不需要改（它不展示角色信息）

**前端 auth service**：确认 `currentUser` 类型定义包含 `role` 字段。找到前端的 User 类型定义（可能在 `services/authApi.ts`），加 `role: string`。

**GalleryView.vue**：当前管理员验证流程在 `verifyAdmin()` 中——它调 `galleryRequest('admin/gallery?page_size=1', {}, true)` 来试探。第三个参数 `true` 会带上 `X-Teacher-Token` 头。

需要的改动：
- 如果 `currentUser.value?.role === 'admin'`，`verifyAdmin` 直接设 `isAdmin.value = true`，不再需要 teacher token
- Gallery 审核页的口令输入框（`mode === 'admin' && !isAdmin`）对 admin 角色用户自动跳过
- 具体改法：在 `verifyAdmin` 函数开头加判断：
```ts
async function verifyAdmin() {
  isAdmin.value = false
  if (!currentUser.value) return
  // Admin role: no teacher token needed
  if (currentUser.value.role === 'admin') {
    isAdmin.value = true
    return
  }
  if (!getTeacherToken()) return
  // ... existing teacher token logic
}
```

### 6. `/api/auth/me` 的响应

当前 `/api/auth/me` 返回 `User` model，加了 role 字段后会自动返回。但要确认前端能拿到——检查 `authApi.ts` 里 `getMe()` 的返回类型处理。

## 约束（必须遵守）

1. **不能改 listening.db**，只改 auth.db
2. **不能删除 TEACHER_TOKEN 机制**——保留作为 fallback，非 admin 用户仍然可以用 teacher token 进审核
3. 所有现有测试必须继续通过
4. `.env` 不要提交到 git
5. `student_release_allowed` 必须保持 false
6. admin 角色的用户**不需要**在前端输入教师口令就能直接进入审核页
7. migration 必须是幂等的（重复执行不报错）

## 文件清单

| 文件 | 改动 |
|---|---|
| `backend/auth/models.py` | User 加 role 字段 + migration |
| `backend/auth/service.py` | 确认 public_user 能取 role（大概率不用改）|
| `backend/gallery/router.py` | administrator 函数双通道 |
| `frontend/src/services/authApi.ts` | User 类型加 role |
| `frontend/src/views/gallery/GalleryView.vue` | verifyAdmin 支持 role |

## 验证方式

1. 启动后端，登录 `303528771@qq.com`，`GET /api/auth/me` 返回 `"role": "admin"`
2. 不带 X-Teacher-Token，直接 `GET /api/gallery/admin/gallery` 应该 200（因为 role=admin）
3. 其他普通用户不带 teacher token 访问同一接口应该 403
4. 普通用户 + 正确 teacher token 仍然可以进审核（向后兼容）
5. 前端 Gallery 审核页：admin 角色用户直接进入，不弹口令输入框
6. 全套测试通过
