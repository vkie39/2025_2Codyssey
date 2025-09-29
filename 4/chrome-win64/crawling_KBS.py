import os
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# ---------------------------
# 자격증명: 환경변수 우선, 없으면 하드코딩(테스트용)
# ---------------------------
# 실제 배포 시에는 아래 하드코딩을 제거하고 환경변수만 사용하세요.
ID = os.getenv("NAVER_ID", "jwsh171210")
PW = os.getenv("NAVER_PW", "sh071090")  # 실제 비번은 환경변수로 넣으세요

# ---------------------------
# WebDriver 설정
# ---------------------------
# 필요하면 ChromeOptions/Headless 등 추가 가능
options = webdriver.ChromeOptions()
# 예: options.add_argument("--headless=new")  # 헤드리스 모드(브라우저 표시 없이 실행) — 디버깅 시에는 주석 처리 권장
# 필요 시 user-agent, proxy, profile 등 설정 추가
d = webdriver.Chrome(options=options)

# 명시적 대기(WebDriverWait) 인스턴스 (타임아웃 15초)
w = WebDriverWait(d, 15)

# ---------------------------
# 보조 함수: 사람처럼 타이핑
# ---------------------------
def human_type(element, text, min_gap=0.04, max_gap=0.16):
    """
    element: selenium WebElement - 입력 대상
    text: 문자열 - 보낼 텍스트
    min_gap/max_gap: 각 문자 입력 사이 지연(초)
    설명: 각 문자마다 send_keys하고 작은 랜덤 지연을 넣어 '사람 타이핑'처럼 보이게 함
    """
    for ch in text:
        element.send_keys(ch)
        # 문자마다 아주 짧은 랜덤 지연(사람이 타이핑하는 리듬처럼)
        time.sleep(random.uniform(min_gap, max_gap))

# ---------------------------
# 폼 채우기 및 제출 함수
# ---------------------------
def fill_and_submit():
    """
    1) 아이디/패스워드 input 요소를 기다려서 찾음
    2) 기존 텍스트 지우고 human_type으로 입력
    3) 제출 버튼 클릭 전에 랜덤으로 약 4.5~6.5초 대기 (사람 동작 지연)
    4) 버튼이 없으면 엔터 전송으로 폼 제출
    """
    # 입력 요소 찾기 (CSS 선택자에 여러 경우를 포함)
    uid = w.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#id, input[name='id']")))
    pw  = w.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#pw, input[name='pw'], input[type='password']")))

    # 기존 텍스트 정리 및 사람처럼 입력
    try:
        uid.clear()
    except Exception:
        # 일부 input은 clear() 실패 가능 — 무시
        pass
    human_type(uid, ID)

    try:
        pw.clear()
    except Exception:
        pass
    human_type(pw, PW)

    # 제출 직전의 '사람 지연' : 고정 5초 대신 랜덤(4.5~6.5초)
    # -> 항상 같은 패턴을 줄이기 위해 약간의 랜덤을 둡니다.
    time.sleep(random.uniform(4.5, 6.5))

    # 제출 버튼 찾기 (여러 후보)
    login_btn = d.find_element(By.CSS_SELECTOR, "#log\\.login")
    login_btn.click()

# ---------------------------
# 메인 흐름
# ---------------------------
try:
    # 1) 로그인 폼으로 직행 (mode=form - 로그인 폼 페이지)
    d.get("https://nid.naver.com/nidlogin.login?mode=form&url=https://www.naver.com/")

    # 2) 바로 입력 시도. 만약 폼이 iframe 안에 있거나 로딩이 늦다면 TimeoutException 발생
    try:
        fill_and_submit()
    except TimeoutException:
        # 페이지 내 iframe들을 검사해서 첫 iframe 안에서 다시 시도
        iframes = d.find_elements(By.CSS_SELECTOR, "iframe")
        if iframes:
            # 첫 iframe에 스위치 후 시도 (많은 사이트는 첫 iframe에 로그인 폼을 둠)
            d.switch_to.frame(iframes[0])
            try:
                fill_and_submit()
            finally:
                # 항상 메인 컨텐츠로 되돌아오기
                d.switch_to.default_content()
        else:
            # iframe도 없고 타임아웃이라면 예외 재전파
            raise

    # 3) 로그인 성공 대기: 쿠키에 특정 이름들이 있으면 성공으로 판단
    # NID_SES / NID_AUT 등 (사이트 내부 정책에 따라 이름이 다를 수 있음)
    def has_login_cookie(driver):
        try:
            cookies = driver.get_cookies()
        except WebDriverException:
            return False
        return any(c.get("name") in ("NID_SES", "NID_AUT", "NID_LOGIN") for c in cookies)

    # 최대 20초 동안 쿠키 생성 여부 확인(로그인 후 리다이렉션 / 세션 설정 대기)
    WebDriverWait(d, 20).until(has_login_cookie)

    # 4) 로그인 후 메인 페이지에서 추가 데이터 추출
    d.get("https://www.naver.com/")
    # 루트 요소가 준비될 때까지 대기
    w.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#root")))

    # (예) 페이지에 주입된 전역 변수에서 svt 얻기 (EAGER-DATA는 네이버 내부 객체명 — 없을 수도 있음)
    try:
        svt = d.execute_script(
            "return (window['EAGER-DATA'] && window['EAGER-DATA'].GV && window['EAGER-DATA'].GV.svt) || null;"
        )
    except Exception:
        svt = None

    # 닉네임 추출: 여러 선택자 후보를 순회
    nick = None
    for sel in ("#account #account_text", "#account [class*='name']", "#account [class*='nickname']", ".name_area, .nick, .user_name"):
        try:
            elems = d.find_elements(By.CSS_SELECTOR, sel)
            if elems and elems[0].text.strip():
                nick = elems[0].text.strip()
                break
        except Exception:
            continue

    # 결과 출력
    print({"svt": svt, "userId": ID, "nickName": nick})

except Exception as exc:
    # 에러 발생 시 간단한 로그 출력
    print("오류 발생:", repr(exc))
finally:
    # 드라이버 안전 종료 — 항상 실행되어 리소스 해제
    try:
        d.quit()
    except Exception:
        pass
