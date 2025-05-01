import sys
import os
import torch
import numpy as np
import soundfile as sf
import logging
from datetime import datetime
import time
import argparse # Import argparse directly in the main scope

# Ensure the package path is set correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Attempt imports, handle potential errors if structure is different
try:
    from cli.SparkTTS import SparkTTS
    from sparktts.utils.token_parser import EMO_MAP
except ImportError as e:
    print(f"Error importing SparkTTS components: {e}")
    print("Please ensure you are running from the correct directory and dependencies are installed.")
    sys.exit(1)

# Global cache for reuse
_cached_model_instance = None


def generate_tts_audio(
    text,
    model_dir=None,
    device="cuda:0",
    prompt_speech_path=None,
    prompt_text=None,
    gender=None,
    pitch=None,
    speed=None,
    emotion=None,
    save_dir="example/results", # Default save directory
    output_filename=None,      # <<< New parameter
    segmentation_threshold=150,
    seed=None,
    model=None,
    skip_model_init=False
):
    """
    Generates TTS audio from input text, splitting into segments if necessary.

    Args:
        text (str): Input text for speech synthesis.
        model_dir (str): Path to the model directory.
        device (str): Device identifier (e.g., "cuda:0" or "cpu").
        prompt_speech_path (str, optional): Path to prompt audio for cloning.
        prompt_text (str, optional): Transcript of prompt audio.
        gender (str, optional): Gender parameter ("male"/"female").
        pitch (str, optional): Pitch parameter (e.g., "moderate").
        speed (str, optional): Speed parameter (e.g., "moderate").
        emotion (str, optional): Emotion tag (e.g., "HAPPY", "SAD", "ANGRY").
        save_dir (str): Directory where generated audio will be saved.
        output_filename (str, optional): Desired base filename for the output.
                                         If None, a timestamp will be used.
        segmentation_threshold (int): Maximum number of words per segment.
        seed (int, optional): Seed value for deterministic voice generation.
        model (SparkTTS, optional): Pre-initialized model instance.
        skip_model_init (bool): If True and model is provided, skips initialization.


    Returns:
        str: The unique file path where the generated audio is saved.
    """
    # ============================== OPTIONS REFERENCE ==============================
    # ✔ Gender options: "male", "female"
    # ✔ Pitch options: "very_low", "low", "moderate", "high", "very_high"
    # ✔ Speed options: same as pitch
    # ✔ Emotion options: list from token_parser.py EMO_MAP keys
    # ✔ Seed: any integer (e.g., 1337, 42, 123456) = same voice (mostly)
    # ==============================================================================

    if model_dir is None:
        model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pretrained_models", "Spark-TTS-0.5B"))

    global _cached_model_instance

    if not skip_model_init or model is None:
        if _cached_model_instance is None:
            logging.info("Initializing TTS model...")
            if not prompt_speech_path:
                logging.info(f"Using Gender: {gender or 'default'}, Pitch: {pitch or 'default'}, Speed: {speed or 'default'}, Emotion: {emotion or 'none'}, Seed: {seed or 'random'}")
            try:
                model = SparkTTS(model_dir, torch.device(device))
                _cached_model_instance = model
            except Exception as e:
                logging.error(f"Failed to initialize SparkTTS model: {e}", exc_info=True)
                raise # Re-raise the exception after logging
        else:
            model = _cached_model_instance

    # Set seed for reproducibility
    if seed is not None:
        torch.manual_seed(seed)
        np.random.seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        logging.info(f"Seed set to: {seed}")

    # --- Determine filename --- <<< Modified Section
    os.makedirs(save_dir, exist_ok=True) # Ensure save directory exists

    if output_filename and output_filename.strip():
        # Use provided filename, ensure .wav extension
        base_name = os.path.splitext(os.path.basename(output_filename.strip()))[0]
        if not base_name: # Handle edge cases like input being only ".wav" or whitespace
            logging.warning(f"Invalid output filename '{output_filename}' provided, falling back to timestamp.")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
            filename = f"{timestamp}.wav"
        else:
             filename = f"{base_name}.wav"
             logging.info(f"Using specified output filename base: {base_name}")
    else:
        # Fallback to timestamp if no filename provided
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        filename = f"{timestamp}.wav"
        logging.info(f"Using timestamp for output filename: {timestamp}")

    save_path = os.path.join(save_dir, filename)
    # --- End Modified Section ---

    words = text.split()
    if len(words) > segmentation_threshold:
        logging.info(f"Text exceeds threshold ({segmentation_threshold} words); splitting into {len(words)//segmentation_threshold + 1} segments...")
        segments = [' '.join(words[i:i + segmentation_threshold]) for i in range(0, len(words), segmentation_threshold)]
        wavs = []
        segment_start_time = time.time()
        for i, seg in enumerate(segments):
            logging.info(f"Generating segment {i+1}/{len(segments)}...")
            with torch.no_grad():
                wav = model.inference(
                    seg,
                    prompt_speech_path,
                    prompt_text=prompt_text,
                    gender=gender,
                    pitch=pitch,
                    speed=speed,
                    emotion=emotion
                )
            wavs.append(wav)
        segment_end_time = time.time()
        logging.info(f"Segment generation took {segment_end_time - segment_start_time:.2f} seconds.")
        final_wav = np.concatenate(wavs, axis=0)
    else:
        generation_start_time = time.time()
        with torch.no_grad():
            final_wav = model.inference(
                text,
                prompt_speech_path,
                prompt_text=prompt_text,
                gender=gender,
                pitch=pitch,
                speed=speed,
                emotion=emotion
            )
        generation_end_time = time.time()
        logging.info(f"Single segment generation took {generation_end_time - generation_start_time:.2f} seconds.")


    sf.write(save_path, final_wav, samplerate=16000)
    logging.info(f"Audio saved at: {save_path}")
    return save_path


# Example CLI usage
if __name__ == "__main__":
    # import argparse # Moved to top level

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    parser = argparse.ArgumentParser(description="Generate TTS audio using SparkTTS.")
    parser.add_argument("--prompt_audio", type=str, help="Path to audio file for voice cloning")
    parser.add_argument("--prompt_text", type=str, help="Transcript text for the prompt audio (optional)")
    parser.add_argument("--text", type=str, help="Text to generate", required=False)
    parser.add_argument("--text_file", type=str, help="Path to .txt file with input text")
    parser.add_argument("--gender", type=str, choices=["male", "female"], default=None, help="Specify gender if not using voice cloning")
    parser.add_argument("--pitch", type=str, choices=["very_low", "low", "moderate", "high", "very_high"], default="moderate", help="Specify pitch if not using voice cloning")
    parser.add_argument("--speed", type=str, choices=["very_low", "low", "moderate", "high", "very_high"], default="moderate", help="Specify speed if not using voice cloning")
    parser.add_argument("--emotion", type=str, choices=list(EMO_MAP.keys()), default=None, help="Specify emotion (experimental)")
    parser.add_argument("--seed", type=int, default=None, help="Seed for reproducible voice generation")
    parser.add_argument("--save-dir", type=str, default="example/results", help="Directory to save the output audio file") # <<< Argument for save dir
    parser.add_argument("--output_filename", type=str, default=None, help="Desired base filename for the output audio (e.g., 'my_speech'). '.wav' added automatically.") # <<< New argument
    parser.add_argument("--model-dir", type=str, default=None, help="Path to the SparkTTS model directory") # <<< Argument for model dir
    parser.add_argument("--device", type=str, default="cuda:0", help="Device to use (e.g., 'cuda:0', 'cpu')") # <<< Argument for device

    args = parser.parse_args()


    # ---------------- Argument Validation Block ----------------
    if not args.prompt_audio and not args.gender:
        print("❌ Error: You must provide either --gender (male/female) or --prompt_audio for voice cloning.")
        print("   Example 1: python tts_cli.py --text \"Hello there.\" --gender female")
        print("   Example 2: python tts_cli.py --text \"Hello there.\" --prompt_audio sample.wav")
        sys.exit(1)

    # --------------- Emotions ------------
    if args.emotion:
        logging.warning("⚠ Emotion input is experimental — model may not reflect emotion changes reliably or at all.")

    # Allow loading text from a file if provided
    input_text = ""
    if args.text_file:
        if os.path.exists(args.text_file):
            try:
                with open(args.text_file, "r", encoding="utf-8") as f:
                    input_text = f.read().strip()
                logging.info(f"Loaded text from file: {args.text_file}")
            except Exception as e:
                 logging.error(f"Error reading text file {args.text_file}: {e}")
                 sys.exit(1)
        else:
            logging.error(f"Text file not found: {args.text_file}")
            sys.exit(1)
    elif args.text:
        input_text = args.text
    else:
        # This case should ideally be caught by argparse if --text was required,
        # but double-checking helps if requirement changes.
        logging.error("You must provide either --text or --text_file.")
        sys.exit(1)

    # Voice Cloning Mode Overrides
    prompt_audio_path = None
    if args.prompt_audio:
        # Normalize path + validate
        prompt_audio_path = os.path.abspath(args.prompt_audio)
        if not os.path.exists(prompt_audio_path):
            logging.error(f"❌ Prompt audio file not found: {prompt_audio_path}")
            sys.exit(1)

        # Log cloning info
        logging.info("🔊 Voice cloning mode enabled")
        logging.info(f"🎧 Cloning from: {prompt_audio_path}")

        # Bonus: Log audio info
        try:
            info = sf.info(prompt_audio_path)
            logging.info(f"📏 Prompt duration: {info.duration:.2f} seconds | Sample Rate: {info.samplerate}")
        except Exception as e:
            logging.warning(f"⚠️ Could not read prompt audio info: {e}")

        # Override pitch/speed/gender
        if args.gender or args.pitch or args.speed:
            logging.warning("[!] Warning: Voice cloning mode detected — ignoring gender/pitch/speed settings.")
        args.gender = None
        args.pitch = None
        args.speed = None
    else:
         # Ensure gender is set if not cloning
         if not args.gender:
             logging.error("❌ Error: --gender must be set if not using --prompt_audio for voice cloning.")
             sys.exit(1)


    # Start timing
    start_time = time.time()

    try:
        output_file = generate_tts_audio(
            text=input_text,
            gender=args.gender,
            pitch=args.pitch,
            speed=args.speed,
            emotion=args.emotion,
            seed=args.seed,
            prompt_speech_path=prompt_audio_path, # Use validated path
            prompt_text=args.prompt_text,
            save_dir=args.save_dir,              # Pass save_dir from args
            output_filename=args.output_filename, # Pass output_filename from args
            model_dir=args.model_dir,            # Pass model_dir from args
            device=args.device                 # Pass device from args
        )

        # End timing
        end_time = time.time()
        elapsed = end_time - start_time

        print(f"\n✅ Successfully generated audio file: {output_file}")
        print(f"⏱ Generation time: {elapsed:.2f} seconds")

    except Exception as e:
        logging.error(f"❌ Audio generation failed: {e}", exc_info=True) # Log full traceback
        sys.exit(1)