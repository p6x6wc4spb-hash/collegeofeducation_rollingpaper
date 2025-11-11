from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import os
from pymongo import MongoClient

# MongoDB 연결 설정
# Render 환경 변수에 설정된 MONGO_URI를 사용합니다.
MONGO_URI = os.environ.get('MONGO_URI')

# MONGO_URI가 설정되지 않은 경우를 대비한 안전 장치 (실제 배포 시에는 Render 설정 필수)
if not MONGO_URI:
    print("경고: MONGO_URI 환경 변수가 설정되지 않았습니다. MongoDB 연결이 실패할 수 있습니다.")
    MONGO_URI = "mongodb://localhost:27017/" 

try:
    client = MongoClient(MONGO_URI)
    db = client.rolling_paper_db  # 데이터베이스 이름
    messages_collection = db.messages # 메시지 컬렉션(테이블)
except Exception as e:
    print(f"MongoDB 클라이언트 초기화 오류: {e}")
    # 데이터베이스 연결 실패 시에도 앱이 최소한 실행되도록 더미 객체 설정 (선택 사항)
    messages_collection = None


# 메시지를 MongoDB에서 로드하고 로그에 출력하는 함수
def load_messages():
    if messages_collection is None:
        print("데이터베이스 연결 실패, 빈 메시지 목록 반환")
        return []
    try:
        # MongoDB에서 모든 메시지를 찾아서 타임스탬프 순으로 정렬합니다.
        messages = list(messages_collection.find().sort("timestamp", 1))
        
        # 기획자 확인을 위한 로그 출력
        print("--- 현재까지 들어온 롤링페이퍼 메시지 (MongoDB 영구 저장) ---")
        for msg in messages:
            print(f"Content: {msg['content']}, Timestamp: {msg['timestamp']}")
        print("-----------------------------------")
        
        return messages
    except Exception as e:
        print(f"MongoDB 로딩 중 오류 발생: {e}")
        return []

# 새로운 메시지를 MongoDB에 저장하는 함수
def save_message(message_data):
    if messages_collection is None:
        print("데이터베이스 연결 실패, 메시지 저장 불가")
        return
    try:
        messages_collection.insert_one(message_data)
    except Exception as e:
        print(f"MongoDB 저장 중 오류 발생: {e}")

app = Flask(__name__)

# 공개 날짜 설정: 현재 연도의 12월 25일 00시 00분 (KST 기준)
RELEASE_DATE = datetime(datetime.now().year, 12, 25, 0, 0, 0)


# [수정] GET 요청(페이지 보기)만 처리하며, D-day 로직을 포함합니다.
@app.route('/', methods=['GET'])
def index():
    messages = load_messages()
    current_time = datetime.now()
    
    # 메시지 공개 여부 결정 (크리스마스 이후인지 확인)
    is_released = current_time >= RELEASE_DATE
    
    # --- D-day 계산 로직 복원 ---
    days_left = 0
    if not is_released:
        time_left = RELEASE_DATE - current_time
        days_left = time_left.days
    # -----------------------------
        
    return render_template('index.html', 
                           messages=messages, 
                           is_released=is_released,
                           release_date_str=RELEASE_DATE.strftime('%Y년 %m월 %d일'),
                           days_left=days_left) # <-- D-day 값을 HTML로 전달


# [추가] 롤링페이퍼 작성 요청(POST)만 처리하는 라우트를 별도로 정의합니다.
@app.route('/write_message', methods=['POST'])
def write_message():
    # 1. 메시지 내용 검증 및 데이터 준비
    content = request.form['content'].strip()
    if not content:
        return redirect(url_for('index'))

    # 2. 메시지 객체 생성
    message_data = {
        'content': content,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # 3. MongoDB에 메시지 저장
    save_message(message_data)
    
    # 4. 저장 후 메인 페이지로 리다이렉트
    return redirect(url_for('index'))


if __name__ == '__main__':
    # 로컬 테스트 시에만 사용합니다. 배포 시에는 gunicorn이 실행합니다.
    app.run(debug=True)