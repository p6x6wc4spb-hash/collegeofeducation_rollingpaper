from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import os
from pymongo import MongoClient
import pytz  # <--- KST 시간대 처리를 위해 추가

# MongoDB 연결 설정
MONGO_URI = os.environ.get('MONGO_URI')

if not MONGO_URI:
    print("경고: MONGO_URI 환경 변수가 설정되지 않았습니다. MongoDB 연결 오류 발생 가능성이 높습니다.")
    MONGO_URI = "mongodb://localhost:27017/" 

try:
    client = MongoClient(MONGO_URI)
    db = client.rolling_paper_db
    messages_collection = db.messages
except Exception as e:
    print(f"MongoDB 클라이언트 초기화 오류: {e}")
    messages_collection = None


def load_messages():
    if messages_collection is None:
        print("데이터베이스 연결 실패, 빈 메시지 목록 반환")
        return []
    try:
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

def save_message(message_data):
    if messages_collection is None:
        print("데이터베이스 연결 실패, 메시지 저장 불가")
        return
    try:
        messages_collection.insert_one(message_data)
    except Exception as e:
        print(f"MongoDB 저장 중 오류 발생: {e}")

app = Flask(__name__)

# [수정] KST 시간대와 공개 날짜를 명시적으로 설정하여 서버 시간대 문제를 해결합니다.
KST = pytz.timezone('Asia/Seoul')

# 현재 KST 시각: 11월 12일 15시 08분 (KST)
# 테스트를 위해 오늘 오후 3시 15분으로 설정합니다. (현재 시간보다 미래)
RELEASE_DATE = KST.localize(datetime(datetime.now().year, 11, 12, 17, 15, 0))


@app.route('/', methods=['GET'])
def index():
    messages = load_messages()
    
    # [수정] 현재 서버 시간을 UTC에서 KST로 변환하여 사용합니다.
    current_time_utc = datetime.now(pytz.utc)
    current_time_kst = current_time_utc.astimezone(KST)
    
    # 메시지 공개 여부 결정 (KST 기준으로 비교)
    is_released = current_time_kst >= RELEASE_DATE
    
    # D-day 계산 로직
    days_left = 0
    if not is_released:
        time_left = RELEASE_DATE - current_time_kst
        days_left = time_left.days
        
    return render_template('index.html', 
                           messages=messages, 
                           is_released=is_released,
                           release_date_str=RELEASE_DATE.strftime('%Y년 %m월 %d일 %H시 %M분'),
                           days_left=days_left)


@app.route('/write_message', methods=['POST'])
def write_message():
    content = request.form['content'].strip()
    if not content:
        return redirect(url_for('index'))

    # 메시지 객체 생성 시 시간은 KST 기준으로 저장
    message_data = {
        'content': content,
        'timestamp': datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
    }
    
    save_message(message_data)
    return redirect(url_for('index'))


if __name__ == '__main__':

    app.run(debug=True)
    # Force deploy

