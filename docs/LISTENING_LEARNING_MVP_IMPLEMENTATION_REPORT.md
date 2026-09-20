# 听后学习流程补全：本地实现与验收说明

日期：2026-09-11。范围：已有两套 CET-6 材料的后置学习 MVP；不是多考种重构，也不是上线发布。

## 1. 本轮实际交付

Set2 的 7 个单元已接入独立「听后句段学习」页面，包含 42 个语境表达词条、14 条难句讲解。讲解包含本句义、句子结构、再听任务和换情境表达；词条包含本句义及新编例句。不把普通搭配全部叫作俚语，也不虚构连读标注。

学生路径：

1. 先登录，再新建 Set2 整套作答或 Continuous Practice。
2. 整套交卷，或 CP 到达 `result_final` 后，从结果页进入句段学习。
3. 整套作答可选择 Set2 的 7 个单元；CP 只解锁本次的 Unit 1。
4. 按原文顺序选句段，回听、写出听到的部分或用中文复述；允许选择「暂时没听出」。不从错题直接跳答案位置。
5. 保存尝试后，才可按需揭示该句段原文、表达和难句讲解。未揭示内容不在学习 DTO 中返回。
6. 英文输入可作词序对齐的文字差异对照；中文复述不评分，不把拼写差异判断为理解障碍。
7. 可以收起文字再听、跟读并在本机临时录音、自选收藏表达。录音最长 60 秒，只在页面内存中，不上传、不打分；离开或切换句段清除。
8. 可以提前结束，无需全文听写。收藏表达进入到期的语境/文字复习，先回想含义，再揭示、自评并安排下次到期。

**不要求先背完生词再听。** 首次测验及盲听阶段没有新增预教入口。词义和难句解释后置；已看过文字的练习属于熟悉材料练习，不能重新称为干净测验。

## 2. 两套材料分别怎么用

| 材料 | 本轮处理 | 当前用途 |
| --- | --- | --- |
| Set2 | 42 个表达、14 条难句已接入后置学习 | 开发/Pilot 环境中的可重复学习材料 |
| Set1 | 保留 7 单元学习稿，没有导入学生学习内容模块 | 内部备稿；继续遵守封存策略 |

配套稿件：`SET1_LISTENING_LEARNING_DRAFT.md`、`SET2_LISTENING_LEARNING_DRAFT.md`、`LISTENING_FLOW_LEARNING_COMPLETION_DRAFT.md`。

用户已声明持有材料版权。此次声明不等于 `teacher_verified`，不自动改变封卷、发布或 Profile 条件。Set1 既有 CP 入口及既往接触历史不能因此被当作「从未接触」；本轮没有修改冻结的 CP 核心来重写历史。

## 3. 边界与安全设计

- 新学习 API 必须使用有效账号 Cookie；写入复用现有同源 `X-Auth-Request` 防护。不接收客户端 student_id/owner_id 或客户端内容哈希作为授权。
- 在登录用户新建来源记录时绑定账号和内容快照，完成后解锁；不能凭已知 ID 认领历史或匿名记录。
- 新绑定来源的主要作答、事件、提交、复盘及 CP 状态/轮次等入口增加账号检查；匿名请求也不能操作这些新绑定来源。没有把整个历史匿名系统改成强制登录，也没有声称完成全站安全审计。
- 内容快照保存原文 revision、content_hash、教学内容版本、句段及词条、音频身份；学习事件再绑定快照 hash。未来修改文案不回写已有学习快照。
- Set1 不在学习白名单。发布 gate 每次检查，学习入口不会绕过现有 `gate_allows()`。
- 学习页展示 `profile_eligible=false`。尝试、自评、撤字重听、文字差异不生成 processing speed / attention / working memory 等能力结论。
- 新词卡不写入公开 `lex_items`，不会进入公开词表、种子词池或冷启动。只复用 `lex_srs` 的排期；旧声音识别接口拒绝 `learncard_` 词卡。
- 写入携带请求 ID：同内容重试幂等，冲突拒绝；复习排期使用事务，拒绝同轮重复排期、尚未到期提交和跨轮复用旧揭示。
- 修补旧采词入口的来源账号、Set1 封存和 CP 单元范围检查。旧词表的 CP 匹配仍是保守的词面包含检查，不是词形还原；匹配失败不强行放行。新词卡使用固定 ID 和来源锚点。
- 学生输入可暂存当前浏览器 sessionStorage，键包含账号/会话/句段；不保存 Token 或服务端原文。已同步输入保存在账号记录中。登出清除页面内容并停止媒体。

## 4. 改动文件

### 后端

- `backend/listening/learning_content.py`：Set2 教学内容与原文锚点。
- `backend/listening/learning_service.py`：来源绑定、不可变快照、逐步揭示、听写对照、私人词卡与排期。
- `backend/listening/learning_router.py`：独立认证 API、输入白名单、禁止缓存。
- `backend/listening/repository.py`：新增四张表的幂等建表声明。
- `backend/listening/router.py`：来源创建时绑定、相关来源访问检查；既有接口只作衔接。
- `backend/listening/aural_lexicon_service.py`：旧采词边界及文字词卡禁止冒充声音识别。
- `backend/main.py`：注册学习路由。
- `backend/tests/test_learning.py`：新增 15 个测试实例。
- `backend/tests/preview_learning.py`：仅监听本机的可丢弃数据库/账号预览工具。

### 前端

- `frontend/src/views/listening/ListeningLearningView.vue`：新学习、复习及临时录音页面，手机布局。
- `frontend/src/services/learningApi.ts`：Cookie 请求、类型、取消请求及错误处理。
- `frontend/src/router/index.ts`：`/listening/learning` 与 `/listening/learning/:sessionId`。
- `frontend/src/views/auth/LoginView.vue`：安全返回指定站内听力页。
- `frontend/src/views/listening/ListeningExamV2View.vue`：Set2 交卷后的学习入口。
- `frontend/src/views/listening/ListeningPracticeV2View.vue`：Set2 终态学习入口、显式重新练习入口。
- `frontend/src/views/ListeningView.vue`、`frontend/src/views/listening/AuralLexiconView.vue`：学习/复习导航与准确的说明文案。
- `frontend/src/App.vue`：仅为 footer 添加 `box-sizing: border-box`，修复手机横向溢出；备案链接不变。

进入工作时已存在的 `HomeView.vue`、`style.css` 改动及 `StudyIcon.vue` 未作为本轮改动重写或撤销。

## 5. 数据与 API

新增表：`learning_sources`、`learning_sessions`、`learning_events`、`learning_cards`。排期复用 `lex_srs`。本轮只在隔离数据库中实际建表；今后应用启动会按既有初始化机制创建这些表，上线前仍应备份数据库。

API 前缀 `/api/listening/learning`：

- `GET /materials`：本人已完成来源可学习的单元。
- `GET/POST /sessions`：本人列表 / 创建或恢复学习。
- `GET /sessions/{id}`：按揭示状态返回学习 DTO。
- `POST /sessions/{id}/attempts`、`/reveal`、`/finish`、`/cards`。
- `GET /sessions/{id}/compare`、`/audio`。
- `GET /cards`；`POST /cards/{id}/reveal`、`/grade`。

音频复用现有整套文件，支持 Range；会话验证身份和文件 hash，版本不匹配则拒绝替换。Unit 1 的播放器使用既有整段边界，其他单元只能整卷回听。**客户端整段边界是播放体验，不是服务端音频裁切隔离**；没有新增逐句切片或伪造时间戳。

## 6. 验证

- 前端 `npm run build` 通过（TypeScript + Vite）。
- 后端使用 `backend/tests/run_student_auth_regression.py tests -x -q`，该工具在临时数据库/JSON 副本上运行，阻止写入真实 data 目录。全量 261 个测试通过（原 246 + 新 15）。
- 新增覆盖：真实 Cookie 登录、终态 gate、CSRF、提前揭示、跨账号/匿名访问、来源旧路径保护、跨单元、Set1/历史记录拒绝、版本快照、发布关闭、音频 Range/缓存、幂等冲突、结束状态、私人词卡、SRS 重复/过期轮次，以及全部 42/14 内容锚点。
- 浏览器技能实际验证：登录后回到学习页；尝试前揭示按钮不可用；保存/揭示/英文对照/收藏；结束后进入到期复习；揭示后自评排期；登出清除旧账号页面内容。
- 390px 手机视口发现并修复学习页面及 footer 横向溢出，复核页面宽度不再超出视口。此项是桌面浏览器窄屏验证，不代替 iOS/安卓真机测试。
- 没有请求用户真实麦克风权限、没有录制或上传真实声音；录音权限/编码兼容性仍需真机验证。
- `git diff --check` 无空白错误；Git 的 LF/CRLF 提示不是构建失败。

本机原虚拟环境的启动器指向已丢失的 Kimi Python。验证使用同为 Python 3.12.14 的可用运行时、既有依赖目录和临时测试依赖目录；没有修改项目虚拟环境配置或生产依赖文件。

受保护文件 SHA256 与实施前一致：

| 文件 | SHA256 |
| --- | --- |
| `backend/listening/data/listening.db` | `AEDEB601197E859E3ECA5E41DCB809288352FCEECDE6E4F5648F7B6B19628DC0` |
| `V2_0B_BASELINE.json` | `AEB4608BA2EBD0976E725AAD28730604373A4BC181207D16A88F54165401BA16` |
| `cet6_202606_set1.candidate.json` | `A375DB3627863EAF8BCFD4DB5D55C2C9CC3B8B2F1E5C4B2FFBF2A494C12B8FFF` |
| `cet6_202606_set2.candidate.json` | `D344F8F960F711990F9999F2B22689F69C468AB2BC7691C4734FCFE840DF6F39` |

`student_release_allowed` 仍为 `false`；没有改动 V2.2 CP 核心服务、素材 JSON 或真实学生数据库，没有提交 Git、部署线上或调整 Nginx。

## 7. 本地复现与上线前检查

在有完整后端依赖的 Python 环境中，从仓库根目录运行：

```powershell
python backend/tests/run_student_auth_regression.py tests -x -q
python backend/tests/preview_learning.py
```

另开终端：

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

访问 `http://127.0.0.1:5173/listening/learning`。预览专用临时账号：`preview@example.com` / `Preview-only-123`。预览脚本会在临时库准备终态来源和 7 个学习会话；这是 UI 测试夹具，不是生产绕过接口。停止预览进程后不保留这些测试记录。端口被占用时不要结束不明进程。

生产仍受现有 release gate 限制；本轮没有代替发布审核。正式启用前：复核内容和时间边界，明确 Set1 是否解封，备份数据库，使用实际部署环境验证 Cookie/CSRF/音频 Range 与手机浏览器，再按原部署流程发布。

## 8. 没有完成、不能夸大的部分

1. **不是完整的逐句精确音频 Sentence Lab**：当前沿用原文句段，一段可能多句；没有核验的句级时间轴，无法声称每一句都有独立精听音频。
2. **词卡不是声音识别测验**：尚缺逐词/短语听核切片；现阶段只作语境文字复习。
3. **不证明泛化提高**：反复熟悉 Set2 不能当作陌生材料听力提升；仍需干净材料后测和新增输入。
4. **未全站重构训练/画像**：旧训练计划、旧 Phase 0 和其他 legacy 入口仍存在；新学习证据没有进入正式 Profile。
5. **Set1 未开放**：版权声明已记录，但解封会破坏保留后测的选择，需要单独产品决定。
6. **录音只做本机自比**：没有 ASR、发音打分、千问调用或服务端录音存储。
7. **没有上线**：当前是本地验证的后置学习 MVP，不是学生正式发布验收。
