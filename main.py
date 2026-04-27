import os
from datetime import datetime
from stt import transcribe_audio

def clean_text(text):
    fillers = ["어...", "음...", "그니까"]
    for f in fillers:
        text = text.replace(f, "")
    return text

def generate_prompt(text):
    return f"""
너는 대학 강의를 시험 대비용으로 정리하는 전문가야.

다음 강의 내용을 기반으로:
1. 핵심 개념 정리
2. 시험 포인트
3. 예상 문제 생성

[강의 내용]
{text}
"""

def main():
    file_path = input("오디오 파일 경로 입력: ")

    if not os.path.exists(file_path):
        print("파일 없음")
        return

    print("STT 진행 중...")
    transcript = transcribe_audio(file_path)

    print("텍스트 정제 중...")
    cleaned = clean_text(transcript)

    print("프롬프트 생성 중...")
    prompt = generate_prompt(cleaned)

    os.makedirs("output", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with open(f"output/transcript_{timestamp}.txt", "w", encoding="utf-8") as f:
        f.write(transcript)

    with open(f"output/cleaned_{timestamp}.txt", "w", encoding="utf-8") as f:
        f.write(cleaned)

    with open(f"output/prompt_{timestamp}.md", "w", encoding="utf-8") as f:
        f.write(prompt)

    print("완료! output 폴더 확인")

if __name__ == "__main__":
    main()