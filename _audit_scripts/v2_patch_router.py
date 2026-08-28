# -*- coding: utf-8 -*-
"""router.py V2.1 端点追加 + create_attempt/submit_attempt 最小分支。
一次性补丁脚本; 执行后可删除(保留作审计痕迹)。"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

P = r"D:\kimi-workspace\english-ai\backend\listening\router.py"
src = open(P, encoding="utf-8").read()

# 1) import v2 service(插入到 from . import ( 之后)
marker = "from . import ("
assert marker in src
i = src.index(marker) + len(marker)
assert "v2_exam_service" not in src
src = src[:i] + "\r\n    v2_exam_service," + src[i:]

# 2) create_attempt 存在性检查扩展到 V2 registry
old_ca = "    if not exam_repo.get(body.exam_id):"
assert old_ca in src, "create_attempt anchor"
src = src.replace(
    old_ca,
    "    if not exam_repo.get(body.exam_id) and not v2_exam_service.is_v2_exam(body.exam_id):",
    1,
)

# 3) submit_attempt 判分分支
old_sa = ('@router.post("/attempts/{attempt_id}/submit")\r\n'
          'def submit_attempt(attempt_id: str):\r\n'
          '    result = service.submit_attempt(attempt_id)')
if old_sa not in src:
    old_sa = old_sa.replace("\r\n", "\n")
assert old_sa in src, "submit anchor"
nl = "\r\n" if "\r\n" in old_sa else "\n"
new_sa = nl.join([
    '@router.post("/attempts/{attempt_id}/submit")',
    'def submit_attempt(attempt_id: str):',
    '    attempt = student_repo.get_attempt(attempt_id)',
    '    if attempt and v2_exam_service.is_v2_exam(attempt["exam_id"]):',
    '        result = service.submit_v2_attempt(attempt_id)',
    '    else:',
    '        result = service.submit_attempt(attempt_id)',
])
src = src.replace(old_sa, new_sa, 1)

# 4) 追加 V2 端点
v2 = """

# ================= V2.1 Exam Mode(白名单 DTO, audio_only) =================


@router.get("/v2/exams")
def v2_list_exams():
    \"\"\"V2 套题列表: 只含元信息, 不含题目内容。\"\"\"
    return {"data": v2_exam_service.exam_summaries()}


@router.get("/v2/exams/{exam_id}/paper")
def v2_exam_paper(exam_id: str):
    \"\"\"作答卷面: 白名单 DTO(题号+英文选项), 服务端递归断言无禁止字段。\"\"\"
    dto = v2_exam_service.paper_dto(exam_id)
    if dto is None:
        raise HTTPException(status_code=404, detail="V2 套题不存在")
    return {"data": dto}


@router.get("/v2/exams/{exam_id}/audio")
def v2_exam_audio(exam_id: str):
    \"\"\"整套原始音频(无 unit 切分, 无题号映射)。\"\"\"
    path = v2_exam_service.audio_file(exam_id)
    if not path:
        raise HTTPException(status_code=404, detail="音频不存在")
    media_type = "audio/mp4" if path.suffix == ".m4a" else "audio/mpeg"
    return FileResponse(path, media_type=media_type)
"""
src = src.rstrip("\r\n") + v2.replace("\n", "\r\n")
open(P, "w", encoding="utf-8", newline="").write(src)
print("router.py patched OK")
