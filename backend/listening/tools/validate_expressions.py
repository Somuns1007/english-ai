# -*- coding: utf-8 -*-
"""Phase 6 数据校验: Expression Bridge 数据层完整性检查。

校验内容:
1. 表达数量在 30-50 之间(筛选不贪多, 也不敷衍)
2. 每条 Expression 必填字段齐全, source 引用能落到真实 exam/unit/question
3. 每个表达有 2-4 个场景
4. source_type 合法: 表达=official_exam, 场景=ai_generated, 严禁冒充 authentic
5. target_expression 必须原样出现在场景 text 中
6. 每个场景 questions 三题(scene/meaning/key_info), 各 4 个选项, answer ∈ ABCD
7. review_status / generation_status 取值合法

用法: python -m listening.tools.validate_expressions
测试可 import validate() -> list[str], 返回空列表表示通过。
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXPRESSIONS_PATH = DATA_DIR / "expressions" / "expressions.json"
SCENARIOS_PATH = DATA_DIR / "expressions" / "scenarios.json"
EXAMS_DIR = DATA_DIR / "exams"

EXPR_REQUIRED_FIELDS = [
    "expression_id", "expression", "meaning",
    "source_exam_id", "source_unit_id", "source_question_id",
    "source_sentence", "source_sentence_status", "source_type",
    "communicative_function", "related_expressions",
    "selection_reasons", "review_status",
]
SCENARIO_REQUIRED_FIELDS = [
    "scenario_id", "expression_id", "scenario", "communicative_function",
    "difficulty", "target_expression", "related_expressions", "text",
    "questions", "source_type", "generation_status", "review_status",
]
ALLOWED_EXPR_SOURCE_TYPES = {"official_exam"}
ALLOWED_SCENARIO_SOURCE_TYPES = {"ai_generated"}
FORBIDDEN_SOURCE_TYPES = {"authentic", "authentic_clip", "real_corpus", "official_exam_audio"}
ALLOWED_REVIEW_STATUS = {"pending_teacher", "approved", "rejected"}
ALLOWED_GENERATION_STATUS = {"generated", "failed", "skipped"}
ALLOWED_DIFFICULTY = {"easy", "medium", "hard"}
QUESTION_KEYS = ("scene", "meaning", "key_info")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_exam_index(exams_dir: Path) -> dict:
    """exam_id -> {"units": set, "questions": set}"""
    index: dict = {}
    for p in sorted(exams_dir.glob("*.json")):
        exam = _load_json(p)
        exam_id = exam.get("id")
        units, questions = set(), set()
        for unit in exam.get("units", []):
            if unit.get("id"):
                units.add(unit["id"])
            for q in unit.get("questions", []):
                if q.get("id"):
                    questions.add(q["id"])
        index[exam_id] = {"units": units, "questions": questions}
    return index


def validate(expressions_path: Path = EXPRESSIONS_PATH,
             scenarios_path: Path = SCENARIOS_PATH,
             exams_dir: Path = EXAMS_DIR) -> list:
    """返回错误信息列表; 空列表 = 全部通过。"""
    errors: list = []

    expr_doc = _load_json(expressions_path)
    scn_doc = _load_json(scenarios_path)
    expressions = expr_doc.get("expressions", [])
    scenarios = scn_doc.get("scenarios", [])
    exam_index = _load_exam_index(exams_dir)

    # 1. 表达数量 30-50
    if not (30 <= len(expressions) <= 50):
        errors.append(f"表达数量 {len(expressions)} 不在 30-50 区间")

    # 2. Expression 字段与引用
    expr_ids = set()
    for e in expressions:
        eid = e.get("expression_id", "<missing>")
        if eid in expr_ids:
            errors.append(f"重复 expression_id: {eid}")
        expr_ids.add(eid)
        for f in EXPR_REQUIRED_FIELDS:
            if f not in e or e[f] in (None, ""):
                errors.append(f"{eid}: 缺少必填字段 {f}")
        st = e.get("source_type")
        if st in FORBIDDEN_SOURCE_TYPES or st not in ALLOWED_EXPR_SOURCE_TYPES:
            errors.append(f"{eid}: 非法 source_type={st!r}(表达必须 official_exam, 严禁冒充)")
        if e.get("review_status") not in ALLOWED_REVIEW_STATUS:
            errors.append(f"{eid}: 非法 review_status={e.get('review_status')!r}")
        exam_id = e.get("source_exam_id")
        if exam_id not in exam_index:
            errors.append(f"{eid}: source_exam_id={exam_id!r} 不存在于 exams 数据")
            continue
        if e.get("source_unit_id") not in exam_index[exam_id]["units"]:
            errors.append(f"{eid}: source_unit_id={e.get('source_unit_id')!r} 不在 {exam_id} 中")
        if e.get("source_question_id") not in exam_index[exam_id]["questions"]:
            errors.append(f"{eid}: source_question_id={e.get('source_question_id')!r} 不在 {exam_id} 中")
        if not e.get("selection_reasons"):
            errors.append(f"{eid}: selection_reasons 为空, 筛选规则不可追溯")

    # 3-7. Scenario 校验
    scn_ids = set()
    scn_count_by_expr: dict = {}
    for s in scenarios:
        sid = s.get("scenario_id", "<missing>")
        if sid in scn_ids:
            errors.append(f"重复 scenario_id: {sid}")
        scn_ids.add(sid)
        scn_count_by_expr[s.get("expression_id")] = scn_count_by_expr.get(s.get("expression_id"), 0) + 1
        for f in SCENARIO_REQUIRED_FIELDS:
            if f not in s or s[f] in (None, ""):
                errors.append(f"{sid}: 缺少必填字段 {f}")
        if s.get("expression_id") not in expr_ids:
            errors.append(f"{sid}: 引用了不存在的 expression_id={s.get('expression_id')!r}")
        st = s.get("source_type")
        if st in FORBIDDEN_SOURCE_TYPES or st not in ALLOWED_SCENARIO_SOURCE_TYPES:
            errors.append(f"{sid}: 非法 source_type={st!r}(场景必须 ai_generated, 严禁冒充 authentic/official)")
        if s.get("generation_status") not in ALLOWED_GENERATION_STATUS:
            errors.append(f"{sid}: 非法 generation_status={s.get('generation_status')!r}")
        if s.get("review_status") not in ALLOWED_REVIEW_STATUS:
            errors.append(f"{sid}: 非法 review_status={s.get('review_status')!r}")
        if s.get("difficulty") not in ALLOWED_DIFFICULTY:
            errors.append(f"{sid}: 非法 difficulty={s.get('difficulty')!r}")
        target = s.get("target_expression", "")
        surface = s.get("target_surface") or target
        # target_expression 是原形/规范形; 若对话中实际出现的是变形,
        # 必须用 target_surface 记录实际表层形式, 且表层形式必须原样出现在 text 中
        if surface and surface not in s.get("text", ""):
            errors.append(f"{sid}: target_surface {surface!r} 未原样出现在 text 中")
        if "target_surface" in s and not s.get("target_surface"):
            errors.append(f"{sid}: target_surface 存在但为空")
        text = s.get("text", "")
        if "A:" not in text or "B:" not in text:
            errors.append(f"{sid}: text 缺少 A:/B: 对话格式")
        qs = s.get("questions", {})
        for key in QUESTION_KEYS:
            qu = qs.get(key)
            if not qu:
                errors.append(f"{sid}: 缺少问题 {key}")
                continue
            opts = qu.get("options", {})
            if set(opts.keys()) != {"A", "B", "C", "D"}:
                errors.append(f"{sid}.{key}: 选项必须是 A/B/C/D 四项")
            if qu.get("answer") not in ("A", "B", "C", "D"):
                errors.append(f"{sid}.{key}: answer={qu.get('answer')!r} 非法")

    # 每表达 2-4 个场景
    for eid in expr_ids:
        n = scn_count_by_expr.get(eid, 0)
        if not (2 <= n <= 4):
            errors.append(f"{eid}: 场景数量 {n} 不在 2-4 区间")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print(f"FAILED: {len(errors)} 个问题")
        for e in errors:
            print(" -", e)
        return 1
    expr_doc = _load_json(EXPRESSIONS_PATH)
    scn_doc = _load_json(SCENARIOS_PATH)
    print(f"OK: {len(expr_doc['expressions'])} 个表达, {len(scn_doc['scenarios'])} 个场景, 全部校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
