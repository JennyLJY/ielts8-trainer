import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT / ".copilot-work"
CONFIG_PATH = ROOT / "data" / "config.json"

PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "copilot": {
        "label": "GitHub Copilot CLI (本机免 Key)",
        "base_url": "",
        "model": "gpt-6.1-sol",
    },
    "openai": {
        "label": "ChatGPT (OpenAI)",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "kimi": {
        "label": "Kimi (Moonshot AI)",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
    },
    "qwen": {
        "label": "通义千问 (DashScope)",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
    },
    "claude": {
        "label": "Claude (Anthropic)",
        "base_url": "https://api.anthropic.com",
        "model": "claude-3-5-sonnet-latest",
    },
    "custom": {
        "label": "自定义 OpenAI 兼容接口 (Ollama / SiliconFlow 等)",
        "base_url": "http://127.0.0.1:11434/v1",
        "model": "qwen2.5:7b",
    },
}

TEACHER_PERSONA = (
    "You are an experienced IELTS Band 8.0 coach training a Chinese university student "
    "at CET-6 level (currently ~6.0-6.5) with weak speaking fluency and noticeable native-language "
    "accent (vowel reduction, dropped final consonants, flat intonation). "
    "Target split: Listening 8.5, Reading 8.5, Writing 7.0, Speaking 7.0 (Overall 8.0). "
    "Do NOT use any external URLs or links in your output. Return ONLY valid JSON without markdown fences."
)


def load_config() -> dict[str, str]:
    default = {
        "provider": os.environ.get("IELTS_PROVIDER", "copilot"),
        "base_url": os.environ.get("IELTS_BASE_URL", ""),
        "model": os.environ.get("IELTS_MODEL", "gpt-6.1-sol"),
        "api_key": os.environ.get("IELTS_API_KEY", ""),
    }
    if CONFIG_PATH.exists():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            for k in ("provider", "base_url", "model", "api_key"):
                if k in saved and saved[k] is not None:
                    default[k] = str(saved[k])
        except Exception:
            pass
    return default


def save_config(provider: str, base_url: str, model: str, api_key: str | None) -> dict[str, str]:
    current = load_config()
    if provider not in PROVIDER_PRESETS:
        raise ValueError(f"不支持的模型厂商: {provider}")
    preset = PROVIDER_PRESETS[provider]
    updated = {
        "provider": provider,
        "base_url": (base_url or preset["base_url"]).strip().rstrip("/"),
        "model": (model or preset["model"]).strip(),
        "api_key": current["api_key"] if api_key is None or api_key == "" else api_key.strip(),
    }
    if provider == "copilot" and api_key == "":
        updated["api_key"] = ""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
    return updated


def _find_copilot() -> str:
    exe = shutil.which(os.environ.get("COPILOT_CLI_PATH") or "copilot")
    if exe:
        return exe
    default = Path(r"C:\Users\jiayil\AppData\Local\GitHubCopilotCLI\copilot.exe")
    if default.exists():
        return str(default)
    raise RuntimeError("未找到 copilot.exe，请改用其他 API 或安装并登录 Copilot CLI。")


def _call_copilot_cli(prompt: str, model: str) -> str:
    exe = _find_copilot()
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    cmd = [
        exe,
        "--silent",
        "--output-format",
        "text",
        "--no-custom-instructions",
        "--disable-builtin-mcps",
        "--no-experimental",
        "--available-tools",
        "--deny-tool",
        "shell",
        "--deny-tool",
        "write",
        "--deny-tool",
        "read",
        "--deny-tool",
        "memory",
        "--deny-tool",
        "url",
        "--model",
        model or "gpt-6.1-sol",
    ]
    res = subprocess.run(
        cmd,
        input=f"{TEACHER_PERSONA}\n\n{prompt}",
        text=True,
        encoding="utf-8",
        capture_output=True,
        cwd=WORKSPACE,
        timeout=240,
        check=False,
    )
    if res.returncode != 0:
        raise RuntimeError(f"Copilot CLI 调用失败 ({res.returncode}): {res.stderr[-400:]}")
    return res.stdout.strip()


def _call_openai_compatible(prompt: str, base_url: str, model: str, api_key: str) -> str:
    if not base_url:
        raise ValueError("请填写 Base URL")
    if not api_key and "127.0.0.1" not in base_url and "localhost" not in base_url:
        raise ValueError("请先填写 API Key")
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": TEACHER_PERSONA},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:400]
        raise RuntimeError(f"API 请求失败 (HTTP {e.code}): {detail}") from e


def _call_claude(prompt: str, base_url: str, model: str, api_key: str) -> str:
    if not api_key:
        raise ValueError("请先填写 Claude API Key")
    root = (base_url or "https://api.anthropic.com").rstrip("/")
    url = root if root.endswith("/messages") else f"{root}/v1/messages"
    payload = {
        "model": model or "claude-3-5-sonnet-latest",
        "max_tokens": 4096,
        "system": TEACHER_PERSONA,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["content"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:400]
        raise RuntimeError(f"Claude API 请求失败 (HTTP {e.code}): {detail}") from e


def call_copilot_json(prompt: str) -> dict[str, Any]:
    cfg = load_config()
    provider = cfg["provider"]
    if provider == "copilot":
        raw = _call_copilot_cli(prompt, cfg["model"])
    elif provider == "claude":
        raw = _call_claude(prompt, cfg["base_url"], cfg["model"], cfg["api_key"])
    else:
        raw = _call_openai_compatible(prompt, cfg["base_url"], cfg["model"], cfg["api_key"])

    if "```json" in raw:
        raw = raw.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in raw:
        raw = raw.split("```", 1)[1].split("```", 1)[0].strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"模型未返回有效 JSON: {raw[:240]}")
    return json.loads(raw[start : end + 1])


def test_llm_connection() -> dict[str, Any]:
    res = call_copilot_json('Return exactly: {"ok": true, "reply": "ready"}')
    return {"ok": bool(res.get("ok")), "reply": res.get("reply", "ready")}


def generate_module_content(module: str, date_str: str, variant: int = 1) -> dict[str, Any]:
    if module == "shadowing":
        prompt = f"""Generate a daily IELTS Shadowing & Accent Correction exercise for {date_str} (variant {variant}).
Focus on fixing Chinese-speaker accent issues: long/short vowels, final consonants (-t/-d/-k/-s), linking, and thought-group stress.
Output JSON:
{{
  "title": "今日跟读主题（中英双语）",
  "target_focus": "今日重点纠音（如：/iː/ vs /ɪ/ 与句尾辅音不吞音）",
  "plain_text": "An authentic 70-90 word IELTS Speaking Part 2/3 or academic paragraph in natural British/American English.",
  "marked_text": "Same paragraph annotated with **STRESS** in caps/bold, / for pauses, and ‿ for linking.",
  "pronunciation_tips": [
    {{"word_or_phrase": "example", "issue": "常见中式发音问题", "fix": "正确口型与舌位技巧"}}
  ],
  "chinese_meaning": "全文自然中文翻译"
}}"""
    elif module == "listening":
        prompt = f"""Generate a daily IELTS Intensive Listening exercise (Section 3/4 academic style) for {date_str} (variant {variant}).
Output JSON:
{{
  "title": "听力精听主题",
  "transcript": "A 110-140 word coherent IELTS academic monologue or seminar excerpt with clear numbers, contrasts, and academic vocabulary.",
  "dictation_sentences": [
    "Sentence 1 for intensive dictation (12-18 words).",
    "Sentence 2 for intensive dictation (12-18 words)."
  ],
  "questions": [
    {{
      "q": "Question text",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "answer": "A",
      "explanation": "中文解析与同义替换点"
    }}
  ],
  "synonym_pairs": [
    {{"audio_phrase": "phrase in audio", "question_phrase": "paraphrase in question"}}
  ]
}}
Include 3 multiple-choice questions."""
    elif module == "reading":
        prompt = f"""Generate a daily IELTS Academic Timed Reading mini-passage for {date_str} (variant {variant}).
Time limit: 12 minutes. Output JSON:
{{
  "title": "Academic Passage Title",
  "time_limit_minutes": 12,
  "passage": "A well-structured 380-450 word IELTS-style academic passage divided into 4 paragraphs (A, B, C, D) separated by \\n\\n.",
  "questions": [
    {{
      "type": "TFNG",
      "q": "Statement to evaluate (TRUE / FALSE / NOT GIVEN)",
      "options": ["TRUE", "FALSE", "NOT GIVEN"],
      "answer": "TRUE",
      "explanation": "中文定位句与同义替换解析"
    }},
    {{
      "type": "MCQ",
      "q": "Multiple choice question",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "answer": "B",
      "explanation": "中文解析"
    }}
  ],
  "hard_sentences": [
    {{"en": "Complex sentence from passage", "cn": "中文意译", "grammar_note": "长难句结构拆解"}}
  ]
}}
Include 4 questions total (mix of TFNG and MCQ)."""
    elif module == "writing":
        prompt = f"""Generate a daily IELTS Writing practice task targeting Band 7.0+ for {date_str} (variant {variant}).
Output JSON:
{{
  "task_type": "Task 2",
  "title": "今日写作训练题目",
  "prompt_en": "Full IELTS Writing Task 2 prompt (or Task 1 data-table text description without external charts).",
  "prompt_cn": "题目中文解读与审题关键点",
  "band8_outline": [
    "立场与破题思路",
    "主体段 1 论点 + 具体论证方向",
    "主体段 2 论点 + 让步/反驳方向"
  ],
  "high_value_collocations": [
    {{"en": "collocation", "cn": "中文释义与用法"}}
  ]
}}"""
    elif module == "speaking":
        prompt = f"""Generate a daily IELTS Speaking Patterns & Mock exercise targeting Band 7.0+ for {date_str} (variant {variant}).
Address CET-6 Chinese student habits (Chinglish, tense slips, he/she mix-ups, repetitive 'very/good/I think').
Output JSON:
{{
  "title": "今日口语主题",
  "patterns": [
    {{"chinglish": "常见中式表达", "natural_75": "地道 7.5+ 替代表达", "note": "用法说明"}}
  ],
  "part1_questions": ["Part 1 Q1", "Part 1 Q2"],
  "part2_cue_card": {{
    "topic": "Describe a ...",
    "bullets": ["You should say:", "- bullet 1", "- bullet 2", "- bullet 3", "- and explain why..."]
  }},
  "sample_opening": "A natural 45-word Band 7.5+ opening response for Part 2."
}}
Include 3 pattern upgrades."""
    else:
        raise ValueError(f"未知训练模块: {module}")

    return call_copilot_json(prompt)


def grade_submission(module: str, exercise: dict[str, Any], submission: dict[str, Any]) -> dict[str, Any]:
    if module == "listening":
        prompt = f"""Grade the student's intensive listening dictation.
Reference sentences: {json.dumps(exercise.get("dictation_sentences", []), ensure_ascii=False)}
Student dictation: {json.dumps(submission.get("dictation", []), ensure_ascii=False)}
Output JSON:
{{
  "score_comment": "总体精听评价（中文）",
  "details": [
    {{"expected": "原句", "actual": "学生听写", "missed_reason": "漏听原因（如连读/弱读/拼写）"}}
  ]
}}"""
    elif module == "writing":
        prompt = f"""Grade this IELTS Writing response for a CET-6 student aiming for Band 7.0+ (Overall 8.0).
Prompt: {exercise.get("prompt_en", "")}
Student Essay: {submission.get("essay", "")}
Output JSON:
{{
  "estimated_band": 6.5,
  "criteria": {{
    "TR": "Task Response 评分与中文点评",
    "CC": "Coherence & Cohesion 评分与中文点评",
    "LR": "Lexical Resource 评分与中文点评",
    "GRA": "Grammatical Range & Accuracy 评分与中文点评"
  }},
  "sentence_upgrades": [
    {{"original": "学生原句", "improved": "7.5+ 润色句", "reason": "修改原因"}}
  ],
  "model_paragraph": "A Band 7.5+ sample body paragraph for this prompt."
}}"""
    elif module == "speaking":
        prompt = f"""Grade this IELTS Speaking typed/transcribed response for a CET-6 student aiming for Band 7.0+.
Cue Card / Question: {json.dumps(exercise.get("part2_cue_card", {}), ensure_ascii=False)}
Student Answer: {submission.get("answer", "")}
Output JSON:
{{
  "estimated_band": 6.5,
  "fluency_and_grammar": "流利度与语法纠错（重点抓时态、单复数、he/she、中式表达）",
  "upgrades": [
    {{"original": "原表达", "natural": "地道 7.5+ 表达"}}
  ],
  "polished_version": "A natural, fluent Band 7.5+ rewrite preserving the student's ideas."
}}"""
    else:
        raise ValueError(f"模块 {module} 不支持模型批改")

    return call_copilot_json(prompt)
