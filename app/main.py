import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.copilot_service import (
    PROVIDER_PRESETS,
    generate_module_content,
    grade_submission,
    load_config,
    save_config,
    test_llm_connection,
)
from app.tts_service import AUDIO_DIR, synthesize_wav

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "trainer.db"
STATIC_DIR = ROOT / "static"

app = FastAPI(title="IELTS 8.0 Daily Trainer (Local)")


def _db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS daily_modules (
            date_str TEXT NOT NULL,
            module TEXT NOT NULL,
            variant INTEGER NOT NULL DEFAULT 1,
            payload_json TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            last_score TEXT DEFAULT '',
            updated_at TEXT NOT NULL,
            PRIMARY KEY (date_str, module)
        )"""
    )
    return conn


class GenerateRequest(BaseModel):
    module: str
    date_str: str | None = None
    refresh: bool = False


class GradeRequest(BaseModel):
    module: str
    date_str: str | None = None
    submission: dict[str, Any]


class TtsRequest(BaseModel):
    text: str
    rate: int = 0
    voice: str = "Microsoft Zira Desktop"


class CompleteRequest(BaseModel):
    module: str
    date_str: str | None = None
    score: str = ""


class SettingsRequest(BaseModel):
    provider: str
    base_url: str = ""
    model: str = ""
    api_key: str | None = None


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/settings")
def get_settings() -> dict[str, Any]:
    cfg = load_config()
    key = cfg.get("api_key", "")
    masked = f"{key[:4]}****{key[-4:]}" if len(key) >= 10 else ("已配置" if key else "")
    return {
        "provider": cfg["provider"],
        "base_url": cfg["base_url"],
        "model": cfg["model"],
        "has_api_key": bool(key),
        "api_key_masked": masked,
        "presets": PROVIDER_PRESETS,
    }


@app.post("/api/settings")
def update_settings(req: SettingsRequest) -> dict[str, Any]:
    try:
        saved = save_config(req.provider, req.base_url, req.model, req.api_key)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {
        "ok": True,
        "provider": saved["provider"],
        "base_url": saved["base_url"],
        "model": saved["model"],
        "has_api_key": bool(saved["api_key"]),
    }


@app.post("/api/settings/test")
def test_settings() -> dict[str, Any]:
    try:
        return test_llm_connection()
    except Exception as exc:
        raise HTTPException(400, f"连接测试失败: {exc}") from exc


@app.get("/api/status")
def daily_status(date_str: str | None = None) -> dict[str, Any]:
    today = date_str or datetime.now().strftime("%Y-%m-%d")
    with _db() as conn:
        rows = conn.execute(
            "SELECT module, completed, last_score FROM daily_modules WHERE date_str = ?",
            (today,),
        ).fetchall()
    return {
        "date": today,
        "modules": {
            r["module"]: {"completed": bool(r["completed"]), "score": r["last_score"]}
            for r in rows
        },
    }


@app.post("/api/module/generate")
def api_generate(req: GenerateRequest) -> dict[str, Any]:
    today = req.date_str or datetime.now().strftime("%Y-%m-%d")
    with _db() as conn:
        row = conn.execute(
            "SELECT variant, payload_json, completed, last_score FROM daily_modules WHERE date_str = ? AND module = ?",
            (today, req.module),
        ).fetchone()
        if row and not req.refresh:
            return {
                "date": today,
                "module": req.module,
                "cached": True,
                "completed": bool(row["completed"]),
                "data": json.loads(row["payload_json"]),
            }
        next_variant = (row["variant"] + 1) if row else 1

    try:
        data = generate_module_content(req.module, today, variant=next_variant)
    except Exception as exc:
        raise HTTPException(500, f"生成训练内容失败: {exc}") from exc

    with _db() as conn:
        conn.execute(
            """INSERT INTO daily_modules (date_str, module, variant, payload_json, completed, updated_at)
               VALUES (?, ?, ?, ?, 0, ?)
               ON CONFLICT(date_str, module) DO UPDATE SET
                 variant=excluded.variant,
                 payload_json=excluded.payload_json,
                 completed=0,
                 updated_at=excluded.updated_at""",
            (today, req.module, next_variant, json.dumps(data, ensure_ascii=False), datetime.now().isoformat()),
        )
        conn.commit()

    return {"date": today, "module": req.module, "cached": False, "completed": False, "data": data}


@app.post("/api/module/grade")
def api_grade(req: GradeRequest) -> dict[str, Any]:
    today = req.date_str or datetime.now().strftime("%Y-%m-%d")
    with _db() as conn:
        row = conn.execute(
            "SELECT payload_json FROM daily_modules WHERE date_str = ? AND module = ?",
            (today, req.module),
        ).fetchone()
    if not row:
        raise HTTPException(404, "请先生成今日该模块题目")
    exercise = json.loads(row["payload_json"])
    try:
        feedback = grade_submission(req.module, exercise, req.submission)
    except Exception as exc:
        raise HTTPException(500, f"批改失败: {exc}") from exc
    return {"feedback": feedback}


@app.post("/api/module/complete")
def api_complete(req: CompleteRequest) -> dict[str, bool]:
    today = req.date_str or datetime.now().strftime("%Y-%m-%d")
    with _db() as conn:
        conn.execute(
            "UPDATE daily_modules SET completed = 1, last_score = ?, updated_at = ? WHERE date_str = ? AND module = ?",
            (req.score, datetime.now().isoformat(), today, req.module),
        )
        conn.commit()
    return {"ok": True}


@app.post("/api/tts")
def api_tts(req: TtsRequest) -> dict[str, str]:
    try:
        filename = synthesize_wav(req.text, rate=req.rate, voice=req.voice)
        return {"url": f"/audio/{filename}"}
    except Exception as exc:
        raise HTTPException(500, f"本地语音生成失败: {exc}") from exc


AUDIO_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")
