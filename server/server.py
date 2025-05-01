from fastapi import FastAPI, Query
from pydantic import BaseModel
import subprocess
import uuid
import os

app = FastAPI()

# Define the base path to your CLI directory
CLI_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "cli", "tts_cli.py")

class TTSRequest(BaseModel):
    text: str
    gender: str = Query("female", enum=["male", "female"])
    pitch: str = Query("medium", enum=["low", "medium", "high"])
    seed: int = 12345
    speed: str = Query("normal", enum=["very_low", "low", "normal", "high", "very_high"])

@app.post("/infer")
def run_tts(req: TTSRequest):
    command = [
        "python", CLI_SCRIPT_PATH,
        "--text", req.text,
        "--gender", req.gender,
        "--pitch", req.pitch,
        "--seed", str(req.seed),
        "--speed", req.speed
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return {"status": "success", "output": result.stdout.strip()}
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "error": e.stderr.strip() if e.stderr else str(e),
            "exit_code": e.returncode
        }
