import os
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY:
    raise RuntimeError(
        "没有读取到 DEEPSEEK_API_KEY，请检查 backend/.env"
    )


client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EssayRequest(BaseModel):
    examType: str
    writingType: str
    prompt: str
    essay: str


@app.get("/")
def home():
    return {
        "message": "阿Q的英语自习室后端启动成功"
    }


def build_grading_prompt(data: EssayRequest):
    exam_names = {
        "cet4": "大学英语四级",
        "cet6": "大学英语六级",
        "postgraduate": "考研英语",
        "ielts": "雅思写作",
        "gaokao": "高考英语"
    }

    writing_names = {
        "essay": "议论文",
        "application": "应用文",
        "continuation": "读后续写",
        "translation": "翻译写作"
    }

    exam_name = exam_names.get(
        data.examType,
        data.examType
    )

    writing_name = writing_names.get(
        data.writingType,
        data.writingType
    )

    return f"""
你是一名专业英语教师和英语考试阅卷教师。

请批改下面这篇学生英语作文。

考试类型：
{exam_name}

作文类型：
{writing_name}

作文题目或写作要求：
{data.prompt}

学生作文：
{data.essay}

你必须完成以下任务：

1. 根据当前考试类型进行评分。
2. 评价文章是否完成题目要求。
3. 分析语法、词汇、搭配、句式和表达自然度。
4. 分析文章内容、逻辑、段落组织和论证展开。
5. 对真正存在问题或明显值得提升的句子进行逐句分析。
6. 最后给出完整升级版本。

逐句反馈必须包含：

original：学生原句
problem：具体问题
reason：为什么存在这个问题
revision：修改后的句子

不要为了修改而修改。
如果原句本身准确、自然且符合考试要求，不要强行制造错误。
修改必须尽量保持学生原意，不能随意加入学生没有表达的信息。

所有解释使用中文。
学生原句、修改句和升级后的完整作文保持英文。

必须严格返回下面结构的 JSON：

{{
  "score": {{
    "overall": 0,
    "language": 0,
    "content": 0,
    "organization": 0
  }},
  "summary": "详细整体评价",
  "sentenceFeedback": [
    {{
      "original": "学生原句",
      "problem": "具体问题",
      "reason": "详细解释为什么存在问题",
      "revision": "修改后的句子"
    }}
  ],
  "logicFeedback": "文章逻辑、内容展开和结构分析",
  "rewrite": "完整升级后的作文"
}}

除了合法 JSON，不要输出任何其他内容。
"""


@app.post("/api/essay")
def submit_essay(data: EssayRequest):
    if not data.essay.strip():
        raise HTTPException(
            status_code=400,
            detail="作文内容不能为空"
        )

    try:
        grading_prompt = build_grading_prompt(data)

        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一名严谨的英语写作教师。"
                        "请严格按照用户要求批改作文，"
                        "并只返回合法 JSON。"
                    )
                },
                {
                    "role": "user",
                    "content": grading_prompt
                }
            ],
            response_format={
                "type": "json_object"
            },
            temperature=0.2
        )

        raw_content = response.choices[0].message.content

        if not raw_content:
            raise ValueError("模型没有返回内容")

        grading_result = json.loads(raw_content)

        return {
            "success": True,
            "message": "AI 批改完成",
            "data": {
                "examType": data.examType,
                "writingType": data.writingType,
                "prompt": data.prompt,
                "essay": data.essay,
                "wordCount": len(data.essay.split()),
                "grading": grading_result
            }
        }

    except json.JSONDecodeError as error:
        print("JSON 解析失败：", error)

        raise HTTPException(
            status_code=500,
            detail="AI 返回的数据不是合法 JSON"
        )

    except Exception as error:
        print("作文批改失败：", error)

        raise HTTPException(
            status_code=500,
            detail=f"作文批改失败：{str(error)}"
        )