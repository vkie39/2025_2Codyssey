import smtplib
import csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

my_email = 'jwsh171210@gmail.com'
password = 'rngcqdqnezhesifn'  # 앱 비밀번호

# CSV에서 이메일 주소 읽기
to_addrs = []
with open('6/mail_target_list.csv', 'r', encoding='cp949') as f: #utf-8로 하면 한글 윈도우에서 만든 엑셀 파일이 cp949형식이라 오류 남
    reader = csv.DictReader(f)
    for row in reader:
        to_addrs.append(row['이메일'])

# HTML 메일 내용
subject = "안녕하세요! 테스트 메일입니다"
html_body = """
<html>
  <body>
    <h2 style="color:#2e6c80;">안녕하세요!</h2>
    <p>이 메일은 <b>HTML 형식</b>으로 전송되었습니다.<br>
    <a href="https://www.google.com">구글로 이동하기</a></p>
  </body>
</html>
"""

# MIME 구성
msg = MIMEMultipart('alternative')
msg['From'] = my_email
msg['To'] = ', '.join(to_addrs)
msg['Subject'] = subject
msg.attach(MIMEText(html_body, 'html'))

# 메일 전송
try:
    with smtplib.SMTP('smtp.gmail.com', 587) as connection:
        connection.starttls()
        connection.login(user=my_email, password=password)
        connection.sendmail(my_email, to_addrs, msg.as_string())
        print('메일 전송 성공!')
except Exception as e:
    print('메일 전송 실패:', e)
