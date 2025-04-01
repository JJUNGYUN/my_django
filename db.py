import pymysql

if __name__=='__main__':
    db = pymysql.connect(
        host="localhost",  # MySQL 서버 주소 (로컬이면 localhost)
        user="root",       # MySQL 사용자 이름
        password="1234",  # MySQL 비밀번호
        database="mydb",  # 사용할 데이터베이스 이름
        charset="utf8mb4",  # 한글 사용을 위한 인코딩 설정
        cursorclass=pymysql.cursors.DictCursor  # 결과를 딕셔너리 형태로 반환
    )
    db.close()
    