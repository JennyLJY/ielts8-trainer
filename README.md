# IELTS 8.0 Daily Trainer（雅思 8.0 每日训练营）

一个面向大学六级基础、冲刺雅思总分 **8.0**（听 8.5 / 读 8.5 / 写 7.0 / 口 7.0）的纯本地 Web 训练工具。  
所有训练页面、音频合成、录音对比与学习记录均在本机运行，**学生端界面不包含任何外部链接**。

## 支持的模型接口（网页端一键切换）

点击左侧栏 **「⚙ 模型 / API 设置」** 即可填写并测试以下任意接口（API Key 仅保存在本机 `data/config.json`，不会上传）：

- **ChatGPT (OpenAI)**：`https://api.openai.com/v1`（如 `gpt-4o-mini` / `gpt-4o`）
- **DeepSeek**：`https://api.deepseek.com/v1`（如 `deepseek-chat`）
- **Kimi (Moonshot AI)**：`https://api.moonshot.cn/v1`（如 `moonshot-v1-8k`）
- **通义千问 (DashScope)**：`https://dashscope.aliyuncs.com/compatible-mode/v1`（如 `qwen-plus`）
- **Claude (Anthropic)**：`https://api.anthropic.com`（如 `claude-3-5-sonnet-latest`）
- **自定义 OpenAI 兼容接口**：如本地 Ollama（`http://127.0.0.1:11434/v1`）、SiliconFlow、OpenRouter 等
- **GitHub Copilot CLI**：本机已登录 Copilot CLI 时可免 Key 直接使用

## 五大每日训练模块

1. **语音跟读与纠音（Shadowing）**：标注重音/连读/停顿，支持 0.8x/1.0x 离线语音示范 + 浏览器本地麦克风录音回放对比。
2. **听力精听与听写**：盲听音频 + 选择题 + 逐句精听听写，AI 诊断漏听与连读/弱读原因。
3. **阅读限时与长难句**：内置 12 分钟倒计时 + TFNG/选择题自动判分 + 长难句拆解。
4. **写作训练与四维批改**：每日出题 + 思路框架，AI 按 TR/CC/LR/GRA 打分、逐句润色并给出 7.5+ 示范段。
5. **口语句型与模考**：每日中式英语 → 7.5+ 地道替换 + Part 2（1 分钟准备 + 2 分钟录音计时）+ AI 抓语法升级。

## 快速开始

```bash
git clone <your-repo-url>
cd ielts8-trainer
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8088
```

Windows 用户也可直接运行 `start-ielts-trainer.ps1` 自动启动并打开 `http://127.0.0.1:8088`。

> **注**：语音示范（`/api/tts`）在 Windows 上调用系统内置 `System.Speech` 离线生成 `.wav` 音频，无需联网；macOS/Linux 可按需替换为本地 TTS 引擎。
