from fastapi import FastAPI, Query
from pydantic import BaseModel
import subprocess
import os

app = FastAPI()

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
    print(req)

    if not req.output_filename:
        return {
            "status": "error",
            "error": "output_filename is required to verify the output file exists."
        }

    output_wav = f"{req.output_filename}.wav"

    command = [
        "python", CLI_SCRIPT_PATH,
        "--text", req.text,
        "--gender", req.gender,
        "--pitch", req.pitch,
        "--seed", str(req.seed),
        "--speed", req.speed,
        "--output_filename", req.output_filename
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        # Check if the resulting .wav file exists
        if not os.path.isfile(output_wav):
            return {
                "status": "error",
                "error": f"Output file {output_wav} not found after synthesis",
                "exit_code": 1
            }

        return {
            "status": "success",
            "output": result.stdout.strip(),
            "output_filename": output_wav
        }

    except subprocess.CalledProcessError as e:
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
