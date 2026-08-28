# V2.0a 教师验收包 — 人工核对指引

本包用于对 **8 道题**(2026年6月六级 Set1 Conversation One Q1–Q4 + Set2 Conversation One Q1–Q4)做字段级人工验收。验收通过的标准不是"看过",而是:**每个关键字段都由真人对着最终证据确认,且确认结果绑定了具体版本(revision + content hash)**。

## 目录结构

```
review_pack/
├── review_pack.json          # 机器可读验收单(在这里记录 verdict)
├── validate_review_pack.py   # 完整性断言(填完 verdict 后运行)
├── REVIEW_GUIDE.md           # 本文件
└── evidence/
    ├── set1_paper_full.png   # 第1套真题卷第1页(整页)
    ├── set1_paper_1.png … _4.png   # 第1套 Q1–Q4 逐题裁切
    ├── set2_paper_full.png   # 合集第9页(第2套听力,整页)
    ├── set2_paper_1.png … _4.png   # 第2套 Q1–Q4 逐题裁切
    ├── set1_answerkey_key.png      # 答案速查表·第1套听力答案区
    └── set2_answerkey_key.png      # 答案速查表·第2套听力答案区
```

音频(Conversation One 均为音频开头第一段):
- Set1:`backend\listening\data\audio\cet6_202606_set1.mp3`
- Set2:`backend\listening\data\audio\cet6_202606_set2.m4a`

## 必验范围(共 46 个必验字段)

| 类别 | 数量 | 对照证据 |
|---|---|---|
| 英文 options | 32(8题×4) | **原始真题页面裁切图**(evidence/*_paper_*.png) |
| question stems | 8 | **音频**(听录音中朗读的题干) |
| correct answers | 8 | 答案速查表裁切 + 解析册解析,双向一致 |
| transcript segments | 20(Set1×12 + Set2×8,按话轮) | **音频**,逐句逐话轮 |
| exam payload | 2 | 运行校验器自动断言白名单,人工复核输出 |

注意:**解析册和模型清洗结果只是 review helper,不是最终证据**。options 以卷面为准,stem 和 transcript 以录音为准。

## 如何记录 verdict

打开 `review_pack.json`,在 `verdicts` 里找到对应 `field_id`,填写:

```json
"cet6_202606_set1_q001.options_en": {
  "verdict": "PASS",
  "reviewer": "你的名字",
  "reviewed_at": "2026-08-28T15:30:00",
  "revision": 1,
  "content_hash": "…(不要改)",
  "note": null
}
```

- `verdict` 只允许 `PASS` 或 `NEEDS_REVIEW`(发现任何问题就用 NEEDS_REVIEW 并在 note 写明)。
- **不要修改 `content_hash` 和 `revision`** —— 它们绑定的是当前 candidate 内容。
- 如果两份答案来源冲突、录音听不清、页面裁切缺失:一律 `NEEDS_REVIEW`,不得自己选一个来源放行。

## PASS 失效规则(由校验器强制执行)

任何人之后修改了 candidate 里对应文本,content hash 会变;再次运行校验器时,该字段的旧 PASS 会被判 **INVALIDATED**,字段自动回到待审状态,必须重新人工核对。Unit 只有在全部必验字段都是有效 PASS 时才允许汇总为 `teacher_verified`。

## 填完后

```bash
python validate_review_pack.py
```

- 输出 `ALL INVARIANTS PASS` 且每个 unit 的 `teacher_verified_allowed=True` → 本批 8 题验收完成,可作为 50 题批量恢复的基准样本。
- 任何 invariant 失败都会列出并阻止通过,不存在"部分成功"。
