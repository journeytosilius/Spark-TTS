from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import subprocess
import os
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

CLI_SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cli", "tts_cli.py"))
OUTPUT_AUDIO_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "example", "results")
)

class TTSRequest(BaseModel):
    text: str
    gender: str = Query("female", enum=["male", "female"])
    pitch: str = Query("medium", enum=["low", "medium", "high"])
    seed: int = 12345
    speed: str = Query("normal", enum=["very_low", "low", "normal", "high", "very_high"])
    emotion: str = Query("NEUTRAL")
    output_filename: str | None = None

@app.post("/infer")
def run_tts(req: TTSRequest):
    command = [
        "python", CLI_SCRIPT_PATH,
        "--text", req.text,
        "--gender", req.gender,
        "--pitch", req.pitch,
        "--seed", str(req.seed),
        "--speed", req.speed,
        # "--emotion", req.emotion
    ]

    output_filename_base = req.output_filename or "output"
    command += ["--output_filename", output_filename_base]

    expected_file_path = os.path.join(OUTPUT_AUDIO_PATH, output_filename_base)

    logging.info(f"🚀 Running command: {' '.join(command)}")

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        if not os.path.exists(expected_file_path):
            logging.error(f"❌ Output file not found at: {expected_file_path}")
            raise HTTPException(status_code=500, detail="TTS succeeded but output file was not found")

        logging.info("✅ TTS process completed successfully")
        return {
            "status": "success",
            "output": result.stdout.strip(),
            "output_filename": os.path.basename(expected_file_path)
        }

    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Subprocess failed\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed:\n{e.stderr.strip() if e.stderr else e.stdout.strip()}"
        )


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
