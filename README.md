# study-ssalmeok

강의 녹음 파일을 STT로 전사한 뒤, ChatGPT에 바로 넣을 수 있는 강의 요약용 프롬프트 파일로 변환하는 GUI 도구입니다.

## 구조

```text
study-ssalmeok/
├─ src/
│  ├─ main.py             # GUI 실행 진입점
│  ├─ application/        # 전체 변환 파이프라인 조립
│  ├─ domain/             # 옵션, 결과 모델
│  ├─ services/           # STT, 텍스트 정제, 청크 분할, 프롬프트 생성
│  ├─ ui/                 # PySide6 GUI
│  └─ config.py           # 기본 설정값
├─ scripts/
│  └─ build_exe.ps1       # Windows exe 빌드 스크립트
└─ tests/                 # 핵심 순수 함수 테스트
```

## 설치

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## STT 모델 준비

exe에는 STT 모델을 포함하지 않습니다. 사용자가 faster-whisper CTranslate2 모델을 직접 준비해야 합니다.

방법 1: Hugging Face 캐시에 다운로드한 뒤 앱에서 모델명 입력

```bash
pip install huggingface-hub
huggingface-cli download Systran/faster-whisper-small
```

이 경우 앱의 `STT 모델` 입력칸에는 `small` 또는 `Systran/faster-whisper-small`을 입력합니다.

방법 2: 원하는 폴더에 다운로드한 뒤 앱에서 폴더 선택

```bash
huggingface-cli download Systran/faster-whisper-small --local-dir models\faster-whisper-small
```

이 경우 앱의 `STT 모델` 입력칸에는 `models\faster-whisper-small` 폴더를 선택합니다. 로컬 모델 폴더에는 최소한 `config.json`, `model.bin` 파일이 있어야 합니다.

## 실행

```bash
python src\main.py
```

설치 후에는 다음 명령도 사용할 수 있습니다.

```bash
study-ssalmeok
```

앱에서 오디오 파일, STT 모델명 또는 모델 폴더, 출력 폴더를 선택한 뒤 변환을 시작합니다.

## exe 빌드

빌드 도구 설치:

```bash
pip install -e ".[build]"
```

Windows 배포 파일 생성:

```bash
.\scripts\build_exe.ps1
```

더블클릭으로 빌드하려면 프로젝트 루트의 `build_exe.bat`을 실행합니다.

빌드 결과:

```text
dist/
└─ StudySsalmeok/
   └─ StudySsalmeok.exe
```

배포할 때는 `dist\StudySsalmeok` 폴더 전체를 압축해서 전달합니다. STT 모델 폴더는 별도로 전달하거나 사용자가 직접 다운로드하게 합니다.

## 출력

변환 결과는 기본적으로 `output/lecture_YYYYMMDD_HHMMSS/` 아래에 저장됩니다.

```text
lecture_YYYYMMDD_HHMMSS/
├─ transcript.txt
├─ cleaned.txt
├─ chunks/
│  └─ chunk_001.txt
└─ prompts/
   └─ prompt_001.md
```
