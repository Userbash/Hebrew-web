from __future__ import annotations

import asyncio
import difflib
import io
import logging
import os
import queue
import shutil
import subprocess
import threading
import time
import wave
from typing import Any, Dict

from .env_loader import load_env_file
from .kernel_protocol import KernelAPI, KernelModule

logger = logging.getLogger("voice_listener")


class _EnergyVAD:
    def __init__(self, threshold: int) -> None:
        self.threshold = threshold

    def is_speech(self, frame: bytes, sample_rate: int) -> bool:
        del sample_rate
        if not frame:
            return False
        samples = len(frame) // 2
        if samples == 0:
            return False
        total = 0
        for idx in range(0, len(frame) - 1, 2):
            value = int.from_bytes(frame[idx:idx + 2], "little", signed=True)
            total += abs(value)
        return total // samples >= self.threshold


class VoiceListenerModule(KernelModule):
    """
    Direct Voice-to-Text module for the Orchestrator.
    Listens to the microphone, uses VAD to detect speech boundaries,
    transcribes with faster-whisper, and submits commands directly to the core.
    """
    name: str = "voice_listener"

    def __init__(self):
        self._api: KernelAPI | None = None
        self._running = False
        self._thread: threading.Thread | None = None
        self._audio_queue: queue.Queue = queue.Queue()
        self._openai_stt_disabled = False
        self._openai_refine_disabled = False

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        load_env_file()
        
        if os.getenv("AI_BRIDGE_ENABLE_VOICE", "false").lower() in ("true", "1", "yes"):
            self._running = True
            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()
            self._api.log("info", f"[{self.name.upper()}] Voice listening thread started.")
        else:
            self._api.log("info", f"[{self.name.upper()}] Module loaded but inactive (AI_BRIDGE_ENABLE_VOICE != true).")

    def on_unload(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        if self._api:
            if self._thread and self._thread.is_alive():
                self._api.log("warning", f"[{self.name.upper()}] Stop requested; listener thread is still finishing startup/work.")
            else:
                self._api.log("info", f"[{self.name.upper()}] Voice listening thread stopped.")

    def _listen_loop(self):
        sample_rate = int(os.getenv("AI_BRIDGE_VOICE_SAMPLE_RATE", "16000"))
        frame_duration_ms = int(os.getenv("AI_BRIDGE_VOICE_FRAME_MS", "30"))  # webrtcvad supports 10, 20, 30 ms
        frame_size = int(sample_rate * frame_duration_ms / 1000)
        bytes_per_frame = frame_size * 2 # 16-bit audio = 2 bytes per sample

        vad = self._build_vad()
        transcriber = self._build_transcriber(sample_rate)
        if transcriber is None:
            return

        accumulated_audio = []
        silence_frames = 0
        is_speaking = False
        silence_threshold = int(1000 / frame_duration_ms)  # 1 second of silence
        min_speech_frames = int(os.getenv("AI_BRIDGE_VOICE_MIN_SPEECH_MS", "450")) // frame_duration_ms
        process = None

        try:
            process = self._open_audio_stream(sample_rate)
            if process.stdout is None:
                raise RuntimeError("audio recorder did not expose stdout")
            
            while self._running:
                # Read exactly one frame of audio
                frame = process.stdout.read(bytes_per_frame)
                if not frame or len(frame) != bytes_per_frame:
                    if self._api:
                        self._api.log("warning", f"[{self.name.upper()}] Audio stream interrupted or ended.")
                    break

                # VAD expects 16-bit mono PCM audio
                is_speech = vad.is_speech(frame, sample_rate)

                if is_speech:
                    if not is_speaking:
                        is_speaking = True
                        if self._api:
                            self._api.log("debug", f"[{self.name.upper()}] Voice detected, capturing...")
                    
                    silence_frames = 0
                    accumulated_audio.append(frame)
                elif is_speaking:
                    silence_frames += 1
                    accumulated_audio.append(frame)

                    if silence_frames > silence_threshold:
                        # Speech ended, process buffer
                        audio_data = b"".join(accumulated_audio)
                        speech_frames = max(0, len(accumulated_audio) - silence_frames)
                        if self._api:
                            self._api.log("debug", f"[{self.name.upper()}] Silence detected. speech_frames={speech_frames}")
                        
                        if speech_frames >= min_speech_frames:
                            threading.Thread(target=self._process_audio, args=(transcriber, sample_rate, audio_data), daemon=True).start()
                        elif self._api:
                            self._api.log("debug", f"[{self.name.upper()}] Ignored short audio fragment.")
                        
                        # Reset state
                        is_speaking = False
                        accumulated_audio = []
                        silence_frames = 0
        except Exception as e:
            if self._api:
                self._api.log("error", f"[{self.name.upper()}] Audio stream error: {e}")
        finally:
            if process:
                process.terminate()
                process.wait()

    def _build_vad(self):
        try:
            import webrtcvad
            vad = webrtcvad.Vad(int(os.getenv("AI_BRIDGE_VOICE_VAD_AGGRESSIVENESS", "2")))
            if self._api:
                self._api.log("info", f"[{self.name.upper()}] Using webrtcvad speech detection.")
            return vad
        except (ImportError, OSError) as exc:
            threshold = int(os.getenv("AI_BRIDGE_VOICE_ENERGY_THRESHOLD", "650"))
            if self._api:
                self._api.log("warning", f"[{self.name.upper()}] webrtcvad unavailable ({exc}); using energy VAD threshold={threshold}.")
            return _EnergyVAD(threshold)

    def _audio_recorder_candidates(self, sample_rate: int) -> list[list[str]]:
        configured = os.getenv("AI_BRIDGE_VOICE_RECORDER", "").strip()
        if configured:
            return [configured.split()]

        candidates: list[list[str]] = []
        if shutil.which("parec"):
            candidates.append(["parec", "--format=s16le", f"--rate={sample_rate}", "--channels=1"])
        if shutil.which("parecord"):
            candidates.append(["parecord", "--format=s16le", f"--rate={sample_rate}", "--channels=1", "-"])
        if shutil.which("pw-record"):
            candidates.append(["pw-record", "--format=s16", f"--rate={sample_rate}", "--channels=1", "-"])
        return candidates

    def _open_audio_stream(self, sample_rate: int) -> subprocess.Popen[bytes]:
        candidates = self._audio_recorder_candidates(sample_rate)
        if not candidates:
            raise RuntimeError("no audio recorder found; install PulseAudio/PipeWire tools such as parec or pw-record")

        last_error: Exception | None = None
        for cmd in candidates:
            try:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                time.sleep(0.25)
                if process.poll() is None:
                    if self._api:
                        self._api.log("info", f"[{self.name.upper()}] Audio recorder active: {' '.join(cmd)}")
                    return process
                stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
                last_error = RuntimeError(f"{' '.join(cmd)} exited early: {stderr.strip() or 'no stderr'}")
                if self._api:
                    self._api.log("warning", f"[{self.name.upper()}] {last_error}")
            except Exception as exc:
                last_error = exc
                if self._api:
                    self._api.log("warning", f"[{self.name.upper()}] Audio recorder failed ({' '.join(cmd)}): {exc}")

        raise RuntimeError(f"could not start an audio recorder: {last_error}")

    def _process_audio(self, transcriber, sample_rate: int, audio_data: bytes):
        try:
            text = transcriber(audio_data, sample_rate).strip()

            if text:
                if self._api:
                    self._api.log("info", f"[{self.name.upper()}] Transcribed: '{text}'")

                if len(text) > 3:
                    self._dispatch_to_core(text)
        except Exception as e:
            if self._api:
                self._api.log("error", f"[{self.name.upper()}] Transcription failed: {e}")

    def _build_transcriber(self, sample_rate: int):
        backend = os.getenv("AI_BRIDGE_VOICE_STT_BACKEND", "openai").strip().lower()
        local_transcriber = None
        if backend in {"openai", "auto"}:
            primary = self._build_openai_transcriber(sample_rate)
            if primary is not None:
                local_transcriber = self._build_local_whisper_transcriber()

                def transcribe(audio_data: bytes, actual_sample_rate: int) -> str:
                    if self._openai_stt_disabled and local_transcriber is not None:
                        return local_transcriber(audio_data, actual_sample_rate)
                    try:
                        return primary(audio_data, actual_sample_rate)
                    except Exception as exc:
                        if self._should_disable_openai(exc):
                            self._openai_stt_disabled = True
                        if self._api:
                            self._api.log("warning", f"[{self.name.upper()}] OpenAI STT failed, falling back to local whisper: {exc}")
                        if local_transcriber is None:
                            raise
                        return local_transcriber(audio_data, actual_sample_rate)

                return transcribe
        transcriber = local_transcriber or self._build_local_whisper_transcriber()
        if transcriber is not None:
            return transcriber
        if self._api:
            self._api.log("error", f"[{self.name.upper()}] No speech-to-text backend is available.")
        return None

    def _build_openai_transcriber(self, sample_rate: int):
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return None
        try:
            from openai import OpenAI
        except ImportError as exc:
            if self._api:
                self._api.log("warning", f"[{self.name.upper()}] OpenAI SDK unavailable: {exc}")
            return None

        model_name = os.getenv("AI_BRIDGE_VOICE_OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe")
        language = os.getenv("AI_BRIDGE_VOICE_LANGUAGE", "ru").strip() or None
        prompt = os.getenv(
            "AI_BRIDGE_VOICE_TRANSCRIBE_PROMPT",
            "Это русский голосовой ввод для AI-оркестратора. Точно распознавай слово 'оркестратор' и технические команды.",
        )
        client = OpenAI(api_key=api_key)
        if self._api:
            self._api.log("info", f"[{self.name.upper()}] Using OpenAI STT backend ({model_name}).")

        def transcribe(audio_data: bytes, actual_sample_rate: int) -> str:
            wav_bytes = self._pcm_to_wav_bytes(audio_data, actual_sample_rate)
            audio_file = io.BytesIO(wav_bytes)
            audio_file.name = "voice.wav"
            result = client.audio.transcriptions.create(
                model=model_name,
                file=audio_file,
                language=language,
                prompt=prompt,
            )
            return getattr(result, "text", "") or ""

        return transcribe

    def _build_local_whisper_transcriber(self):
        try:
            from faster_whisper import WhisperModel
        except (ImportError, OSError) as exc:
            if self._api:
                self._api.log("error", f"[{self.name.upper()}] Missing local whisper dependency: {exc}")
            return None

        model_name = os.getenv("AI_BRIDGE_VOICE_WHISPER_MODEL", "tiny")
        if self._api:
            self._api.log("info", f"[{self.name.upper()}] Loading fallback faster-whisper model ({model_name})...")
        try:
            model = WhisperModel(model_name, device="cpu", compute_type="int8")
        except Exception as exc:
            if self._api:
                self._api.log("error", f"[{self.name.upper()}] Failed to load faster-whisper model {model_name}: {exc}")
            return None
        if self._api:
            self._api.log("info", f"[{self.name.upper()}] Fallback faster-whisper model loaded.")

        def transcribe(audio_data: bytes, actual_sample_rate: int) -> str:
            import numpy as np

            audio_np = np.frombuffer(audio_data, np.int16).astype(np.float32) / 32768.0
            language = os.getenv("AI_BRIDGE_VOICE_LANGUAGE", "ru").strip() or None
            segments, _ = model.transcribe(audio_np, beam_size=5, language=language)
            return "".join(segment.text for segment in segments).strip()

        return transcribe

    def _pcm_to_wav_bytes(self, audio_data: bytes, sample_rate: int) -> bytes:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data)
        return buffer.getvalue()

    def _refine_command_text(self, text: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key or self._openai_refine_disabled:
            return text
        try:
            from openai import OpenAI
        except ImportError:
            return text

        model_name = os.getenv("AI_BRIDGE_VOICE_OPENAI_REFINE_MODEL", "gpt-4o-mini")
        client = OpenAI(api_key=api_key)
        try:
            response = client.chat.completions.create(
                model=model_name,
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты приводишь русскую голосовую команду для AI-оркестратора к короткому точному тексту. Верни только команду без пояснений. Если это не команда, верни пустую строку.",
                    },
                    {"role": "user", "content": text},
                ],
            )
        except Exception as exc:
            if self._should_disable_openai(exc):
                self._openai_refine_disabled = True
            raise
        message = response.choices[0].message.content if response.choices else ""
        return (message or "").strip() or text

    def _should_disable_openai(self, exc: Exception) -> bool:
        message = str(exc).lower()
        fatal_markers = ("insufficient_quota", "quota", "billing", "invalid_api_key", "authentication")
        return any(marker in message for marker in fatal_markers)

    def _normalize_voice_command(self, text: str) -> str | None:
        cleaned = " ".join(text.strip().split())
        if not cleaned:
            return None
        require_wake = os.getenv("AI_BRIDGE_VOICE_REQUIRE_WAKE_WORD", "true").strip().lower() in {"1", "true", "yes", "on"}
        if not require_wake:
            return cleaned

        wake_words = [
            item.strip().lower()
            for item in os.getenv("AI_BRIDGE_VOICE_WAKE_WORDS", "оркестратор,команда,система").split(",")
            if item.strip()
        ]
        lowered = cleaned.lower()
        for word in wake_words:
            if lowered == word:
                return None
            prefixes = (f"{word} ", f"{word},", f"{word}:", f"{word}.")
            if lowered.startswith(prefixes):
                command = cleaned[len(word):].lstrip(" ,:.!-—")
                return command or None
        fuzzy = self._extract_fuzzy_wake_command(cleaned, wake_words)
        if fuzzy:
            return fuzzy
        return None

    def _extract_fuzzy_wake_command(self, cleaned: str, wake_words: list[str]) -> str | None:
        tokens = cleaned.split()
        if not tokens:
            return None

        max_window = min(3, len(tokens))
        threshold = float(os.getenv("AI_BRIDGE_VOICE_WAKE_FUZZY_THRESHOLD", "0.72"))
        for size in range(1, max_window + 1):
            candidate = " ".join(tokens[:size]).lower()
            for word in wake_words:
                ratio = difflib.SequenceMatcher(None, candidate, word).ratio()
                if ratio >= threshold:
                    command = " ".join(tokens[size:]).lstrip(" ,:.!-—")
                    return command or None
        return None

    def _dispatch_to_core(self, text: str):
        if not self._api:
            return
            
        command_text = self._normalize_voice_command(text)
        if not command_text:
            self._api.log("info", f"[{self.name.upper()}] Ignored voice input without wake word.")
            return

        final_text = command_text
        try:
            refined = self._refine_command_text(command_text)
            if refined and len(refined.strip()) > 0:
                self._api.log("info", f"[{self.name.upper()}] Refined intent: '{refined}'")
                final_text = refined
            else:
                self._api.log("info", f"[{self.name.upper()}] Ignored non-command voice input.")
                return
        except Exception as e:
            self._api.log("warning", f"[{self.name.upper()}] Intent refinement failed, using raw text. Error: {e}")

        payload = {
            "message": final_text,
            "description": final_text,
            "source": "voice_input",
            "session_id": "voice",
        }
        
        if hasattr(self._api, "submit_user_task"):
            try:
                result = self._api.submit_user_task(payload, source="voice_listener")
                self._api.log("info", f"[{self.name.upper()}] Task accepted by core. Status: {result.get('status')}")
            except Exception as e:
                self._api.log("error", f"[{self.name.upper()}] Failed to submit task to core: {e}")
        else:
            self._api.log("error", f"[{self.name.upper()}] Orchestrator API lacks submit_user_task method.")

    def before_task(self, task: Any, context: Dict[str, Any]) -> None:
        pass

    def after_task(self, task: Any, result: Any, context: Dict[str, Any]) -> None:
        pass

    def finalize(self) -> Dict[str, Any]:
        return {
            "status": "active" if self._running else "inactive",
            "thread_alive": self._thread.is_alive() if self._thread else False
        }
