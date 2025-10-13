import smtplib

my_email = 'jwsh171210@gmail.com'
password = 'rngcqdqnezhesifn'  # 앱 비밀번호 16자리 (공백 없음)

try:
    connection = smtplib.SMTP('smtp.gmail.com', 587)
    connection.starttls()  # TLS 암호화
    connection.login(user=my_email, password=password)
    connection.sendmail(
        from_addr=my_email,
        to_addrs='jwsh171210@naver.com',
        msg='Subject:Hello\n\nThis is the body of my email.'
    )
    print('메일 전송 성공!')
except Exception as e:
    print('메일 전송 실패:', e)
finally:
    connection.close()