from pathlib import Path
import os
import subprocess
import sys

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from application.converter import convert_audio_to_prompts
from config import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL_REF,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OVERLAP,
    SUPPORTED_AUDIO_EXTENSIONS,
)
from domain.models import ConversionOptions, ConversionResult


class ConvertWorker(QThread):
    log = Signal(str)
    done = Signal(object)
    error = Signal(str)





    def __init__(self, audio_path: str, options: ConversionOptions):
        super().__init__()


        self.audio_path = audio_path
        self.options = options





    def run(self) -> None:
        try:
            result = convert_audio_to_prompts(
                self.audio_path,
                options=self.options,
                logger=self.log.emit,
            )
        except Exception as exc:
            self.error.emit(str(exc))
            return


        self.done.emit(result)





class StudySsalmeokApp(QWidget):
    def __init__(self):
        super().__init__()


        self.worker: ConvertWorker | None = None
        self.last_output_dir = Path(DEFAULT_OUTPUT_DIR).resolve()


        self.setWindowTitle("공부 쌀먹")
        self.resize(760, 560)
        self.setMinimumSize(680, 500)


        self.create_widgets()
        self.create_layout()
        self.connect_signals()





    def create_widgets(self) -> None:
        self.audio_input = QLineEdit()
        self.model_input = QLineEdit(DEFAULT_MODEL_REF)
        self.output_input = QLineEdit(str(DEFAULT_OUTPUT_DIR))
        self.language_input = QLineEdit(DEFAULT_LANGUAGE)


        self.chunk_size_input = QSpinBox()
        self.chunk_size_input.setRange(1000, 100000)
        self.chunk_size_input.setSingleStep(500)
        self.chunk_size_input.setValue(DEFAULT_CHUNK_SIZE)


        self.overlap_input = QSpinBox()
        self.overlap_input.setRange(0, 50000)
        self.overlap_input.setSingleStep(100)
        self.overlap_input.setValue(DEFAULT_OVERLAP)


        self.select_audio_button = QPushButton("찾기")
        self.select_model_button = QPushButton("찾기")
        self.select_output_button = QPushButton("찾기")
        self.start_button = QPushButton("변환 시작")
        self.open_output_button = QPushButton("출력 폴더 열기")


        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)





    def create_layout(self) -> None:
        root = QVBoxLayout()


        title = QLabel("공부 쌀먹")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        subtitle = QLabel("강의 녹음 파일을 GPT 요약용 프롬프트 파일로 변환합니다.")


        root.addWidget(title)
        root.addWidget(subtitle)


        form = QGridLayout()
        self.add_path_row(form, 0, "오디오 파일", self.audio_input, self.select_audio_button)
        self.add_path_row(form, 1, "STT 모델", self.model_input, self.select_model_button)
        self.add_path_row(form, 2, "출력 폴더", self.output_input, self.select_output_button)


        form.addWidget(QLabel("언어"), 3, 0)
        form.addWidget(self.language_input, 3, 1)


        form.addWidget(QLabel("청크 크기"), 4, 0)
        form.addWidget(self.chunk_size_input, 4, 1)


        form.addWidget(QLabel("중복"), 5, 0)
        form.addWidget(self.overlap_input, 5, 1)


        root.addLayout(form)


        button_row = QHBoxLayout()
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.open_output_button)
        button_row.addStretch()


        root.addLayout(button_row)
        root.addWidget(QLabel("진행 로그"))
        root.addWidget(self.log_view)


        self.setLayout(root)





    def add_path_row(
        self,
        layout: QGridLayout,
        row: int,
        label: str,
        input_widget: QLineEdit,
        button: QPushButton,
    ) -> None:
        layout.addWidget(QLabel(label), row, 0)
        layout.addWidget(input_widget, row, 1)
        layout.addWidget(button, row, 2)





    def connect_signals(self) -> None:
        self.select_audio_button.clicked.connect(self.select_audio_file)
        self.select_model_button.clicked.connect(self.select_model_dir)
        self.select_output_button.clicked.connect(self.select_output_dir)
        self.start_button.clicked.connect(self.start_convert)
        self.open_output_button.clicked.connect(self.open_output_folder)





    def select_audio_file(self) -> None:
        patterns = " ".join(f"*{extension}" for extension in SUPPORTED_AUDIO_EXTENSIONS)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "오디오 파일 선택",
            "",
            f"Audio Files ({patterns});;All Files (*)",
        )


        if file_path:
            self.audio_input.setText(file_path)





    def select_model_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "STT 모델 폴더 선택")


        if folder:
            self.model_input.setText(folder)





    def select_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "출력 폴더 선택")


        if folder:
            self.output_input.setText(folder)





    def start_convert(self) -> None:
        if self.worker and self.worker.isRunning():
            return


        try:
            audio_path, options = self.build_conversion_request()
        except ValueError as exc:
            QMessageBox.warning(self, "입력 오류", str(exc))
            return


        self.log_view.clear()
        self.append_log("변환 시작")
        self.set_running(True)


        self.worker = ConvertWorker(audio_path, options)
        self.worker.log.connect(self.append_log)
        self.worker.done.connect(self.on_done)
        self.worker.error.connect(self.on_error)
        self.worker.start()





    def build_conversion_request(self) -> tuple[str, ConversionOptions]:
        audio_path = self.audio_input.text().strip()


        if not audio_path:
            raise ValueError("오디오 파일을 선택하세요.")


        model_ref = self.model_input.text().strip()


        if not model_ref:
            raise ValueError("STT 모델 폴더 또는 캐시 모델명을 입력하세요.")


        options = ConversionOptions(
            output_dir=Path(self.output_input.text().strip() or DEFAULT_OUTPUT_DIR),
            model_ref=model_ref,
            language=self.language_input.text().strip() or DEFAULT_LANGUAGE,
            chunk_size=self.chunk_size_input.value(),
            overlap=self.overlap_input.value(),
        )


        return audio_path, options





    def on_done(self, result: ConversionResult) -> None:
        self.last_output_dir = result.output_dir
        self.append_log(f"완료: 총 {result.prompt_count}개 프롬프트 생성")
        self.append_log(f"출력 폴더: {result.output_dir}")
        self.set_running(False)


        QMessageBox.information(
            self,
            "완료",
            f"프롬프트 {result.prompt_count}개를 생성했습니다.",
        )





    def on_error(self, message: str) -> None:
        self.append_log(f"오류 발생: {message}")
        self.set_running(False)
        QMessageBox.critical(self, "오류", message)





    def append_log(self, message: str) -> None:
        self.log_view.append(message)





    def set_running(self, running: bool) -> None:
        self.start_button.setEnabled(not running)





    def open_output_folder(self) -> None:
        open_folder(self.last_output_dir)





def open_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


    if sys.platform == "win32":
        os.startfile(path)
        return


    command = ["open", str(path)] if sys.platform == "darwin" else ["xdg-open", str(path)]
    subprocess.Popen(command)





def main() -> int:
    app = QApplication(sys.argv)
    window = StudySsalmeokApp()
    window.show()


    return app.exec()
