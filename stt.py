from faster_whisper import WhisperModel


def transcribe_audio(
    file_path: str,
    model_size: str = "small",
    language: str = "ko",
) -> str:
    """
    로컬 오디오 파일을 텍스트로 변환한다.
    model_size 예시: tiny, base, small, medium, large-v3
    """
    model = WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8",
    )

    segments, info = model.transcribe(
        file_path,
        language=language,
        vad_filter=True,
    )

    lines = []

    for segment in segments:
        start = format_timestamp(segment.start)
        end = format_timestamp(segment.end)
        text = segment.text.strip()

        if text:
            lines.append(f"[{start} - {end}] {text}")

    return "\n".join(lines)


def format_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)
    minutes = total_seconds // 60
    secs = total_seconds % 60
    return f"{minutes:02d}:{secs:02d}"