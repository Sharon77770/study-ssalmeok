from collections.abc import Callable
from pathlib import Path


REQUIRED_MODEL_FILES = ("config.json", "model.bin")
ProgressHandler = Callable[[int, str], None]





def transcribe_audio(
    file_path: str | Path,
    model_ref: str | Path,
    language: str = "ko",
    progress_callback: ProgressHandler | None = None,
) -> str:
    """Convert a local audio file into timestamped transcript text."""
    model_ref = resolve_model_ref(model_ref)
    emit_progress = progress_callback or (lambda percent, message: None)
    emit_progress(0, "STT 모델 로딩 중")


    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper가 설치되어 있지 않습니다. "
            "`pip install -e .` 또는 `pip install faster-whisper`로 설치하세요."
        ) from exc


    model = WhisperModel(
        model_ref,
        device="cpu",
        compute_type="int8",
        local_files_only=True,
    )


    emit_progress(0, "STT 음성 분석 중")
    segments, info = model.transcribe(
        str(file_path),
        language=language,
        vad_filter=False,
    )
    duration = get_audio_duration(info)


    lines = []
    last_percent = 0


    for segment in segments:
        start = format_timestamp(segment.start)
        end = format_timestamp(segment.end)
        text = segment.text.strip()


        if text:
            lines.append(f"[{start} - {end}] {text}")


        percent = calculate_progress(segment.end, duration)


        if percent > last_percent:
            emit_progress(percent, f"STT 진행 중 {percent}%")
            last_percent = percent


    emit_progress(100, "STT 완료")


    return "\n".join(lines)




def get_audio_duration(transcription_info: object) -> float:
    duration_after_vad = getattr(transcription_info, "duration_after_vad", None)
    duration = duration_after_vad or getattr(transcription_info, "duration", 0) or 0


    try:
        return max(float(duration), 0.0)
    except (TypeError, ValueError):
        return 0.0




def calculate_progress(position_seconds: float, duration_seconds: float) -> int:
    if duration_seconds <= 0:
        return 0


    try:
        position = max(float(position_seconds), 0.0)
    except (TypeError, ValueError):
        return 0


    return min(int(position / duration_seconds * 100), 99)





def resolve_model_ref(model_ref: str | Path) -> str:
    raw_model_ref = str(model_ref).strip()


    if not raw_model_ref:
        raise ValueError("STT 모델 폴더 또는 캐시 모델명을 입력하세요.")


    candidate_path = Path(raw_model_ref).expanduser()


    if candidate_path.exists():
        return str(validate_model_dir(candidate_path))


    return raw_model_ref





def validate_model_dir(model_dir: str | Path) -> Path:
    local_model_dir = Path(model_dir).expanduser()


    if not local_model_dir.exists():
        raise FileNotFoundError(f"STT 모델 폴더를 찾을 수 없습니다: {local_model_dir}")


    if not local_model_dir.is_dir():
        raise NotADirectoryError(f"STT 모델 경로가 폴더가 아닙니다: {local_model_dir}")


    missing_files = [
        file_name
        for file_name in REQUIRED_MODEL_FILES
        if not (local_model_dir / file_name).exists()
    ]


    if missing_files:
        missing = ", ".join(missing_files)
        raise FileNotFoundError(
            f"STT 모델 폴더에 필요한 파일이 없습니다: {missing}"
        )


    return local_model_dir





def format_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60


    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


    return f"{minutes:02d}:{secs:02d}"
