from fastapi import FastAPI, Query
from pydantic import BaseModel
import subprocess
import uuid
import os
import logging

app = FastAPI()

# Setup basic logging
logging.basicConfig(level=logging.INFO)

CLI_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "cli", "tts_cli.py")
CLI_SCRIPT_PATH = os.path.abspath(CLI_SCRIPT_PATH)

class TTSRequest(BaseModel):
    text: str
    gender: str = Query("female", enum=["male", "female"])
    pitch: str = Query("medium", enum=["low", "medium", "high"])
    seed: int = 12345
    speed: str = Query("normal", enum=["very_low", "low", "normal", "high", "very_high"])
    output_filename: str | None = None

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

    if req.output_filename:
        command += ["--output_filename", req.output_filename]

    logging.info(f"🚀 Running command: {' '.join(command)}")

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logging.info(f"✅ TTS success - stdout:\n{result.stdout}")
        if result.stderr:
            logging.warning(f"⚠️ TTS stderr:\n{result.stderr}")

        # Optional: check if the file was actually created
        expected_file = req.output_filename or "output.wav"
        if not os.path.exists(expected_file):
            logging.error(f"❌ Output file not found: {expected_file}")
            return {"status": "error", "error": "Output file was not created"}

        return {
            "status": "success",
            "output": result.stdout.strip(),
            "output_filename": expected_file
        }

    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Subprocess failed - stderr:\n{e.stderr}")
        return {
            "status": "error",
            "error": e.stderr.strip() if e.stderr else str(e),
            "exit_code": e.returncode
        }



# curl -X POST http://localhost:8091/infer \
#   -H "Content-Type: application/json" \
#   -d '{
#     "text": "Breaking news in crypto...",
#     "gender": "female",
#     "pitch": "low",
#     "seed": 42567,
#     "speed": "very_high",
#     "output_filename": "trump_tax_cut_analysis"
#   }'
