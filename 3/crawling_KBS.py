#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List, Tuple
import sys
import requests
from bs4 import BeautifulSoup  # pip install bs4

ROOT = 'https://news.kbs.co.kr'
MAIN_URL = ROOT + '/news/pc/main/main.html'
TIMEOUT = 10

# 타입 별칭: (제목, 링크)
Headline = Tuple[str, str]
IssueItem = Tuple[str, str]


def fetch_html(url: str) -> str:
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers, timeout=TIMEOUT)
    if not resp.encoding or resp.encoding.lower() == 'iso-8859-1':
        resp.encoding = resp.apparent_encoding or 'utf-8'
    return resp.text


def to_abs_url(href: str) -> str:
    """상대경로를 절대경로로 보정한다."""
    if href.startswith('http://') or href.startswith('https://'):
        return href
    if href.startswith('/'):
        return ROOT + href
    return ROOT.rstrip('/') + '/' + href.lstrip('/')


def collect_main_headlines(soup: BeautifulSoup, limit: int = 20) -> List[Headline]:
    container = soup.select_one('div.box.head-line.main-head-line.main-page-head-line')
    if not container:
        return []

    results: List[Headline] = []
    for a in container.select('a.box-content'):
        href = a.get('href', '')
        link = to_abs_url(href)

        title_tag = a.select_one('p.title')
        if not title_tag:
            continue
        # <br> 등을 공백으로 치환하여 텍스트 추출
        title = title_tag.get_text(' ', strip=True)
        if not title:
            continue

        results.append((title, link))
        if len(results) >= limit:
            break

    return results


def collect_issue_block(soup: BeautifulSoup, limit: int = 20) -> Tuple[str, List[IssueItem]]:

    container = soup.select_one('div.issue-main-video.half-box-wrapper')
    if not container:
        return '이슈', []

    issue_title_tag = container.select_one('h4.title')
    issue_title = issue_title_tag.get_text(' ', strip=True) if issue_title_tag else '이슈'

    items: List[IssueItem] = []
    # 활성 탭만 대상이면 아래 줄을 'li.tab-contents-list.on a.box-content'로 바꿔도 됩니다.
    for a in container.select('a.box-content'):
        href = a.get('href', '')
        if not href:
            continue
        link = to_abs_url(href)

        title_tag = a.select_one('p.title')
        if not title_tag:
            continue
        title = title_tag.get_text(' ', strip=True)
        if not title:
            continue

        items.append((title, link))
        if len(items) >= limit:
            break

    return issue_title, items



def main() -> None:
    try:
        html_text = fetch_html(MAIN_URL) #내려받은 메인 페이지의 HTML문자열
    except requests.RequestException as exc:
        print(f'[오류] 페이지 요청 실패: {exc}', file=sys.stderr)
        sys.exit(1)

    soup = BeautifulSoup(html_text, 'html.parser')

    # 1) 메인 헤드라인(요약 제거, 2튜플)
    main_headlines = collect_main_headlines(soup, limit=20)

    # 2) 이슈 박스(이슈 제목 + 항목들)
    issue_title, issue_items = collect_issue_block(soup, limit=20)

    if not main_headlines and not issue_items:
        print('[알림] 항목을 찾지 못했습니다. 페이지 구조를 확인하세요.')
        sys.exit(0)

    if main_headlines:
        print('[메인 헤드라인]')
        for i, (title, link) in enumerate(main_headlines, 1):
            print(f'{i:2d}. {title}')
            print(f'    - {link}')
        print()

    if issue_items:
        print(f'[이슈] {issue_title}')
        for i, (title, link) in enumerate(issue_items, 1):
            print(f'{i:2d}. {title}')
            print(f'    - {link}')


if __name__ == '__main__':
    main()
