from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import os
from pymongo import MongoClient

# MongoDB 연결 설정
# Render에서 설정할 환경 변수(Environment Variable)를 통해 접속합니다.
MONGO_URI = os.environ.get('MONGO_URI')
if not MONGO_URI:
    # 안전장치: MONGO_URI가 설정되지 않은 경우를 대비 (로컬 테스트용)
    print("경고: MONGO_URI 환경 변수가 설정되지 않았습니다. 임시 로컬 DB를 사용할 수 있습니다.")
    # 실제 배포시에는 MONGO_URI 설정이 필수입니다.
    pass 

client = MongoClient(MONGO_URI)
db = client.rolling_paper_db  # 데이터베이스 이름
messages_collection = db.messages # 메시지 컬렉션(테이블)

# 메시지를 JSON 파일 대신 MongoDB에서 로드하는 함수
def load_messages():
    # MongoDB에서 모든 메시지를 찾아서 최신 순으로 정렬합니다.
    messages = list(messages_collection.find().sort("timestamp", 1))
    
    # 메시지를 미리 확인하고 싶다면 로그에 출력합니다. (필요 없으면 삭제해도 됩니다)
    print("--- 현재까지 들어온 롤링페이퍼 메시지 (MongoDB) ---")
    for msg in messages:
        # ObjectId와 같은 불필요한 정보는 제외하고 출력합니다.
        print(f"Content: {msg['content']}, Timestamp: {msg['timestamp']}")
    print("-----------------------------------")
    
    return messages

# 새로운 메시지를 MongoDB에 저장하는 함수
def save_message(message_data):
    # MongoDB에 새로운 메시지 문서를 삽입합니다.
    messages_collection.insert_one(message_data)

app = Flask(__name__)

# 공개 날짜 설정: 현재 연도의 12월 25일 00시 00분
RELEASE_DATE = datetime(datetime.now().year, 12, 25, 0, 0, 0)


@app.route('/', methods=['GET', 'POST'])
def index():
    messages = load_messages()
    current_time = datetime.now()
    
    # 메시지 공개 여부 결정
    is_released = current_time >= RELEASE_DATE
    
    if request.method == 'POST':
        # 1. 메시지 내용 검증 및 데이터 준비
        content = request.form['content'].strip()
        if not content:
            # 내용이 비어있으면 다시 돌려보냅니다.
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

    return render_template('index.html', 
                           messages=messages, 
                           is_released=is_released,
                           release_date_str=RELEASE_DATE.strftime('%Y년 %m월 %d일'))


if __name__ == '__main__':
    # Render 환경에서는 gunicorn이 실행하므로 이 부분은 로컬 테스트용입니다.
    # 로컬 테스트 시에는 'python app.py'로 실행합니다.
    app.run(debug=True)