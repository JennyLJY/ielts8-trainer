# IELTS 8.0 Daily Trainer（雅思 8.0 每日训练营）

一个面向**大学六级基础（约 6.0–6.5 分）、口语偏弱或母语口音较重、目标冲刺雅思总分 8.0** 的纯本地 AI 私教训练系统。  
采用科学提分权重：**听力 8.5 + 阅读 8.5 + 写作 7.0 + 口语 7.0 = 7.75 → 总分 8.0**。

> **核心特点**
> - **零外部链接**：学生端页面与训练界面不包含任何外链或第三方 CDN，打开即练、专注无干扰。
> - **多模型自由切换**：内置 **ChatGPT、DeepSeek、Kimi、通义千问、Claude、Ollama 本地模型、GitHub Copilot CLI** 等接口，网页端一键填写自己的 API Key 即可使用。
> - **离线语音合成 + 本地录音对比**：Windows 上调用系统内置 `System.Speech` 离线生成 `.wav` 示范音频，配合浏览器本地 `MediaRecorder` 录音回放对比，无需联网 TTS。
> - **本地数据留存**：每日题目、批改记录与打卡进度保存在本机 `data/trainer.db`，API Key 仅保存在本机 `data/config.json`。

---

## 一、环境要求

- **操作系统**：Windows 10 / 11（完整支持离线语音合成）；macOS / Linux 可运行核心网页与 AI 批改功能（`/api/tts` 需按需替换为本地 TTS）。
- **Python**：`3.10` 及以上（推荐 `3.11` – `3.13`）。
- **浏览器**：Chrome / Edge / Firefox 最新版（用于麦克风本地录音与回放）。

---

## 二、安装与启动步骤

### 1. 下载代码并安装依赖

```bash
git clone https://github.com/JennyLJY/ielts8-trainer.git
cd ielts8-trainer

# 创建并激活虚拟环境
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

# 安装依赖（仅 3 个轻量包：fastapi / uvicorn / pydantic）
pip install -r requirements.txt
```

### 2. 启动程序

- **方式 A：Windows 一键启动（推荐）**  
  右键使用 PowerShell 运行（或在终端执行）：
  ```powershell
  .\start-ielts-trainer.ps1
  ```
  脚本会自动启动本地服务并打开浏览器访问 `http://127.0.0.1:8088`。

- **方式 B：通用命令行启动**
  ```bash
  uvicorn app.main:app --host 127.0.0.1 --port 8088
  ```
  然后在浏览器打开 `http://127.0.0.1:8088`。

---

## 三、配置大模型 API（必读）

打开网页 `http://127.0.0.1:8088` 后，点击左侧边栏的 **「⚙ 模型 / API 设置」**：

1. 在 **「选择模型厂商」** 下拉框选择你拥有的模型服务。
2. 确认 **API Base URL** 和 **模型名称 (Model)**（系统会自动填入默认值，也可手动修改）。
3. 在 **API Key** 输入框粘贴你的密钥。
4. 点击 **「测试连接」**，提示 `连接成功！模型回复: ready` 后点击 **「保存设置」**。
5. 点击主界面右上角 **「换一组新题」**，即可使用新模型生成训练内容。

### 支持的模型厂商与默认参数对照表

| 厂商 | 界面选项 | 默认 Base URL | 推荐 Model | 说明 |
|---|---|---|---|---|
| **DeepSeek** | `DeepSeek` | `https://api.deepseek.com/v1` | `deepseek-chat` | 性价比高，中文批改与逻辑解析清晰 |
| **Kimi** | `Kimi (Moonshot AI)` | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` | 长文本阅读生成稳定 |
| **通义千问** | `通义千问 (DashScope)` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` | 阿里云百炼 OpenAI 兼容接口 |
| **ChatGPT** | `ChatGPT (OpenAI)` | `https://api.openai.com/v1` | `gpt-4o-mini` / `gpt-4o` | 英文表达地道，适合口语/写作润色 |
| **Claude** | `Claude (Anthropic)` | `https://api.anthropic.com` | `claude-3-5-sonnet-latest` | 写作批改与长难句解析质量极佳 |
| **本地/第三方** | `自定义 OpenAI 兼容接口` | `http://127.0.0.1:11434/v1` | `qwen2.5:7b` 等 | 支持 Ollama、SiliconFlow、OpenRouter、vLLM |
| **Copilot CLI** | `GitHub Copilot CLI` | （无需填写） | `gpt-6.1-sol` | 本机已安装并登录 Copilot CLI 时免 Key 使用 |

> **也支持环境变量配置**：复制 `.env.example` 为 `.env`，设置 `IELTS_PROVIDER`、`IELTS_BASE_URL`、`IELTS_MODEL`、`IELTS_API_KEY` 即可作为默认配置。

---

## 四、五大每日训练模块使用指南

建议每天按顺序投入 **2.5 – 3.5 小时** 完成以下 5 个模块，全部完成后点击右上角 **「打卡完成本项」** 记录今日进度：

### 1. 语音跟读与纠音（Shadowing，建议 45 分钟）
- **训练目标**：解决中国考生常见的元音不饱满、句尾辅音吞音、语调平淡问题。
- **使用步骤**：
  1. 页面会展示带标记的跟读段落（**粗体大写**为重音词，`/` 为意群停顿，`‿` 为连读位置）。
  2. 先点 **「播放慢速示范 (0.8x)」** 听清每个词的发音，再切 **「播放常速示范 (1.0x)」** 跟读。
  3. 点击 **「开始录音跟读」**（首次需在浏览器允许麦克风权限），读完点 **「停止录音」**，直接回放对比自己与示范音的差距。
  4. 对照页面下方的 **「今日纠音要点」** 反复磨 3–5 遍。

### 2. 听力精听与听写（Intensive Listening，建议 60 分钟）
- **训练目标**：冲刺听力 **8.5**，攻克 Section 3/4 学术场景中的连读、弱读与同义替换。
- **使用步骤**：
  1. 先**不要点「显示/隐藏原文」**，直接点击 **「播放听力音频 (1.0x)」** 盲听做选择题。
  2. 点击 **「慢速精听 (0.8x)」**，在下方听写框逐词敲出听到的句子。
  3. 点击 **「交卷并让 AI 诊断漏听原因」**，系统会核对答案、展示同义替换点并分析你漏听的原因。

### 3. 阅读限时与长难句（Timed Reading，建议 50 分钟）
- **训练目标**：冲刺阅读 **8.5**，培养快速定位与同义替换识别能力。
- **使用步骤**：
  1. 进入模块后右上角自动开启 **12 分钟倒计时**。
  2. 限时完成学术短文后的 `TRUE / FALSE / NOT GIVEN` 与选择题。
  3. 点击 **「交卷核对答案」**，自动评分并展开 **「长难句精讲」**（含结构拆解与中文意译）。

### 4. 写作训练与四维批改（Writing，建议 45 分钟）
- **训练目标**：冲刺写作 **7.0+**，摆脱模板化表达。
- **使用步骤**：
  1. 阅读今日 Task 2/Task 1 题目、审题关键点、高分思路框架与高分搭配。
  2. 在输入框撰写英文作文（底部实时统计词数，建议写满 250+ 词）。
  3. 点击 **「提交 AI 考官批改」**，获取预估分数、**TR / CC / LR / GRA 四维点评**、逐句润色建议及 **7.5+ 示范段**。

### 5. 口语句型与模考（Speaking，建议 45 分钟）
- **训练目标**：冲刺口语 **7.0+**，消灭中式英语（Chinglish）与时态/人称口误。
- **使用步骤**：
  1. 先熟读今日 3 组 **中式表达 → 7.5+ 地道替换**。
  2. 查看 Part 2 题卡，点击 **「1 分钟准备倒计时」** 列关键词提纲。
  3. 点击 **「开始 2 分钟录音答题」** 计时口述，也可先听 **「7.5+ 示范开头」**。
  4. 将你的回答要点或转写文本输入下方文本框，点击 **「提交口语纠错与升级」** 获取语法纠错与 7.5+ 润色版。

---

## 五、项目结构说明

```text
ielts8-trainer/
├── app/
│   ├── main.py              # FastAPI 后端、SQLite 每日进度存储与接口路由
│   ├── copilot_service.py   # 多模型统一调度（OpenAI/DeepSeek/Kimi/Qwen/Claude/Copilot）
│   └── tts_service.py       # Windows System.Speech 本地离线 WAV 语音合成
├── static/
│   └── index.html           # 纯本地单页应用前端（零外部链接/零 CDN）
├── data/                    # 运行时自动生成（已在 .gitignore 中忽略，不会上传）
│   ├── config.json          # 本机保存的 API 配置与密钥
│   ├── trainer.db           # SQLite 每日题目缓存与打卡记录
│   └── audio/               # 离线合成的 .wav 音频缓存
├── start-ielts-trainer.ps1  # Windows 一键启动脚本
├── requirements.txt         # Python 依赖列表
├── .env.example             # 环境变量配置示例
└── README.md                # 本使用说明
```

---

## 六、常见问题（FAQ）

1. **同一天切换模块后再切回来，题目会丢失吗？**  
   不会。每天每个模块首次生成后会自动缓存到 `data/trainer.db`，当天重新打开秒开；如果你想再练一套新题，点击右上角 **「换一组新题」** 即可。
2. **点击录音按钮提示无法访问麦克风？**  
   请确保使用 `http://127.0.0.1:8088`（或 `localhost:8088`）访问，并在浏览器地址栏左侧允许麦克风权限。
3. **8088 端口被占用了怎么办？**  
   启动时换成其他端口即可，例如：`uvicorn app.main:app --host 127.0.0.1 --port 8099`。
4. **如何完全重置或清理本地数据？**  
   删除 `data/trainer.db` 与 `data/audio/` 即可清空历史题目和音频缓存；删除 `data/config.json` 可重置 API 配置。

---

## License

MIT License

