import sys
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from services.transcriber import resolve_model_ref, transcribe_audio, validate_model_dir


class TranscriberTest(TestCase):
    def test_validate_model_dir_accepts_required_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            model_dir = Path(temp_dir)
            (model_dir / "config.json").write_text("{}", encoding="utf-8")
            (model_dir / "model.bin").write_bytes(b"model")


            self.assertEqual(validate_model_dir(model_dir), model_dir)





    def test_validate_model_dir_rejects_missing_model_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            model_dir = Path(temp_dir)
            (model_dir / "config.json").write_text("{}", encoding="utf-8")


            with self.assertRaises(FileNotFoundError):
                validate_model_dir(model_dir)





    def test_resolve_model_ref_allows_cached_model_name(self) -> None:
        self.assertEqual(resolve_model_ref("small"), "small")





    def test_resolve_model_ref_rejects_empty_value(self) -> None:
        with self.assertRaises(ValueError):
            resolve_model_ref("")




    def test_transcribe_audio_reports_segment_progress(self) -> None:
        class FakeSegment:
            def __init__(self, start: float, end: float, text: str):
                self.start = start
                self.end = end
                self.text = text


        class FakeWhisperModel:
            def __init__(self, *args, **kwargs):
                pass


            def transcribe(self, *args, **kwargs):
                segments = [
                    FakeSegment(0, 5, " 첫 문장 "),
                    FakeSegment(5, 20, "두 번째 문장"),
                ]
                info = SimpleNamespace(duration=20, duration_after_vad=20)


                return iter(segments), info


        previous_module = sys.modules.get("faster_whisper")
        sys.modules["faster_whisper"] = SimpleNamespace(WhisperModel=FakeWhisperModel)
        progress_events: list[tuple[int, str]] = []


        try:
            transcript = transcribe_audio(
                "lecture.wav",
                model_ref="small",
                progress_callback=lambda percent, message: progress_events.append(
                    (percent, message)
                ),
            )
        finally:
            if previous_module is None:
                del sys.modules["faster_whisper"]
            else:
                sys.modules["faster_whisper"] = previous_module


        self.assertEqual(
            transcript,
            "[00:00 - 00:05] 첫 문장\n[00:05 - 00:20] 두 번째 문장",
        )
        self.assertEqual([event[0] for event in progress_events], [0, 0, 25, 99, 100])


if __name__ == "__main__":
    main()
