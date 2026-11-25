import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT / "data" / "audio"


def synthesize_wav(text: str, rate: int = 0, voice: str = "Microsoft Zira Desktop") -> str:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(f"{voice}|{rate}|{text}".encode("utf-8")).hexdigest()[:16]
    wav_path = AUDIO_DIR / f"{key}.wav"
    if wav_path.exists() and wav_path.stat().st_size > 1000:
        return wav_path.name

    safe_text = text.replace("'", "''")
    safe_voice = voice.replace("'", "''")
    ps_script = f"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {{ $synth.SelectVoice('{safe_voice}') }} catch {{}}
$synth.Rate = {int(rate)}
$synth.SetOutputToWaveFile('{str(wav_path)}')
$synth.Speak('{safe_text}')
$synth.Dispose()
"""
    res = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    if res.returncode != 0 or not wav_path.exists():
        raise RuntimeError(f"本地语音合成失败: {res.stderr}")
    return wav_path.name
