

from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import json
import os

app = Flask(__name__)
# 메시지를 저장할 JSON 파일 경로 설정
DATA_FILE = 'messages.json'
# 공개 날짜 설정: 현재 연도의 12월 25일 00시 00분
# (현재 2025년 11월이므로, 2025년 크리스마스로 설정됩니다.)
# 연도를 현재 연도인 2025년으로 고정하여 오류를 방지합니다.
RELEASE_DATE = datetime(2025, 12, 25, 0, 0, 0)

# 헬퍼 함수: 메시지 데이터를 파일에서 읽어옴
def load_messages():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            messages = json.load(f)
            # --- 아래 세 줄을 추가합니다 ---
            print("--- 현재까지 들어온 롤링페이퍼 메시지 ---") 
            for msg in messages:
                print(msg)
            print("-----------------------------------")
            # --- 추가 완료 ---
            return messages
    except json.JSONDecodeError:
        return []
    
# 헬퍼 함수: 메시지 데이터를 파일에 저장
def save_messages(messages):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)

# 롤링페이퍼 보기/공개 로직
@app.route('/')
def index():
    current_time = datetime.now()
    messages = load_messages()
    
    # 크리스마스 이후인지 확인하는 핵심 로직
    is_open = current_time >= RELEASE_DATE
    
    # D-day 계산 (공개 전이라면)
    if not is_open:
        time_left = RELEASE_DATE - current_time
        days_left = time_left.days
    else:
        days_left = 0
        
    return render_template('index.html', 
                           is_open=is_open, 
                           messages=messages, 
                           days_left=days_left)

# 익명 메시지 작성 및 저장 로직
@app.route('/write', methods=['POST'])
def write_message():
    message_content = request.form.get('content')
    
    if message_content and len(message_content.strip()) > 0:
        messages = load_messages()
        
        # 익명으로 저장: 작성자 정보(이름, IP 등)를 저장하지 않음
        new_message = {
            'content': message_content,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        messages.append(new_message)
        save_messages(messages)
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    # 디버그 모드는 개발 중에만 사용하고, 실제 배포 시에는 꺼야 합니다.
    app.run(debug=False, port=8080)
