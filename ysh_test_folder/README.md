# Django Blog MVP

Django Templates로 프론트엔드와 백엔드를 함께 처리하는 velog형 블로그 MVP입니다.

## 실행

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py runserver
```

## 주요 기능

- 회원가입, 로그인, 로그아웃
- Markdown 글 작성, 수정, 삭제
- 최신 글 목록, 글 상세, 태그별 목록, 사용자 프로필
- 로그인 사용자 좋아요 토글
