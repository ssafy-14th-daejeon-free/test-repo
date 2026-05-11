# localhost:8000 보안 점검 보고서

점검 일시: 2026-05-11 16:16 KST  
대상: `http://localhost:8000/` Django 블로그 서비스  
범위: 로컬 서비스에 대한 비파괴 동적 점검, 저장소 정적 점검, Django 보안 체크

## 요약

운영 환경에 노출되면 즉시 조치해야 할 항목은 2개입니다.

- `DEBUG=True` 상태로 상세 오류 페이지가 외부에 노출됩니다.
- `/accounts/local-login/`가 누구에게나 `localtester` 세션을 발급할 수 있습니다.

반대로, 기본 CSRF 방어, Markdown 저장 XSS 방어, 검색 SQLi 방어, 비로그인 초안 접근 차단은 정상 동작을 확인했습니다.

## 재현한 공격/탐지 결과

| 항목 | 결과 | 근거 |
| --- | --- | --- |
| 로컬 테스트 로그인 | 취약 | 로그인 페이지에서 CSRF 토큰 획득 후 `POST /accounts/local-login/` 요청 시 `302 /` 및 `sessionid` 발급 |
| 상세 오류 페이지 노출 | 취약 | `Host: evil.example`로 요청 시 `400 DisallowedHost` 상세 페이지에 traceback, Django/Python 버전, `/app` 경로, 설정 테이블 노출 |
| CSRF 누락 POST | 방어됨 | 인증 세션에서 CSRF 없이 `POST /posts/new/` 요청 시 `403` |
| 저장 Markdown XSS | 방어됨 | `<script>`, `javascript:`, `onerror`, `<img>` payload 저장 후 상세 페이지에서 실행 가능한 unsafe marker 미검출 |
| 검색 SQLi 유사 payload | 방어됨 | `q=' OR 1=1 --` 요청 시 `200`, DB 오류/traceback 없음 |
| 비로그인 초안 접근 | 방어됨 | `GET /me/drafts/` 비인증 요청 시 `/accounts/login/?next=/me/drafts/`로 redirect |

테스트 중 생성한 `__SECURITY_TEST_XSS_*` 게시글은 앱의 삭제 플로우로 정리했습니다.

## 발견 사항

### HIGH: `DEBUG=True` 상세 오류 페이지 노출

위치:
- `config/settings.py:30`
- `docker-compose.yaml:22`

영향:
공격자가 예외를 유발하면 traceback, 내부 경로, Django/Python 버전, settings 값 일부를 볼 수 있습니다. 실제 재현에서 `DisallowedHost` 오류 페이지가 `/app`, `Django 6.0.5`, `Python 3.13.13`, middleware/settings 정보를 반환했습니다.

권고:
- 운영에서는 `DJANGO_DEBUG=0`으로 실행합니다.
- 운영 전용 settings 또는 환경 변수 검증을 두어 `DEBUG=True`로 부팅되지 않게 합니다.
- 표준 4xx/5xx 오류 페이지를 사용합니다.

### HIGH: 인증 없는 로컬 테스트 계정 로그인

위치:
- `accounts/urls.py:8`
- `accounts/views.py:36`
- `templates/registration/login.html:13`

영향:
외부 사용자가 로그인 페이지에서 CSRF 토큰을 받은 뒤 `/accounts/local-login/`에 POST하면 `localtester` 계정으로 로그인할 수 있습니다. 운영에 남아 있으면 인증 우회성 공용 계정이 됩니다.

권고:
- 운영 빌드에서는 라우트와 버튼을 제거합니다.
- 꼭 필요하면 `settings.DEBUG`와 `request.get_host()`/클라이언트 IP가 localhost인지 확인하는 가드를 둡니다.
- 테스트 계정 생성을 웹 엔드포인트가 아니라 관리 명령 또는 fixture로 옮깁니다.

### MEDIUM: 운영 보안 설정 미적용 및 고정 secret

위치:
- `config/settings.py:24`
- `config/settings.py:30`
- `docker-compose.yaml:24`

근거:
`.venv\Scripts\python.exe manage.py check --deploy` 결과 6개 경고가 발생했습니다.

- `SECURE_HSTS_SECONDS` 미설정
- `SECURE_SSL_REDIRECT` 미설정
- `SECRET_KEY`가 `django-insecure-` 계열 또는 짧은 값
- `SESSION_COOKIE_SECURE` 미설정
- `CSRF_COOKIE_SECURE` 미설정
- `DEBUG=True`

영향:
운영 배포 시 세션 탈취, CSRF 토큰 노출, secret 재사용, HTTP downgrade 위험이 커집니다.

권고:
- 운영 secret은 환경별 난수로 관리하고 저장소/compose 샘플에는 실사용 값을 두지 않습니다.
- HTTPS 뒤에서 `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`를 적용합니다.
- HSTS는 HTTPS 구성이 검증된 뒤 단계적으로 활성화합니다.

### MEDIUM: 로그인/가입/작성 기능에 rate limit 부재

위치:
- `accounts/views.py`
- `templates/registration/login.html`
- 프로젝트 middleware/dependency 구성 전반

영향:
로그인 brute force, 회원가입 스팸, 게시글/댓글 자동 생성에 취약합니다.

권고:
- reverse proxy 또는 Django 레벨에서 IP/계정 기준 rate limit을 둡니다.
- 로그인 실패 횟수 제한, 지연 응답, 계정 잠금 정책을 둡니다.
- 관리자 로그인도 별도 보호합니다.

### LOW: 사용자 제공 외부 이미지 URL로 추적 가능

위치:
- `blog/models.py:78`
- `templates/blog/_post_cards.html:6`
- `templates/blog/post_detail.html:29`

영향:
게시글 작성자가 외부 이미지 URL을 넣으면 방문자의 브라우저가 해당 외부 서버에 직접 요청합니다. 방문자 IP, user-agent, referer 등 메타데이터가 제3자에게 노출될 수 있습니다.

권고:
- 이미지 도메인 allowlist를 둡니다.
- 이미지 프록시/캐시를 사용합니다.
- 운영 정책상 외부 이미지가 필요 없으면 업로드/관리형 미디어로 전환합니다.

### LOW: 조회수 무제한 증가

위치:
- `blog/views.py:120`
- `blog/models.py:127`

영향:
비로그인 사용자가 상세 페이지를 반복 요청해 조회수를 임의로 올릴 수 있습니다. 보안 침해보다는 지표 무결성 문제입니다.

권고:
- 세션/IP/시간창 기준 중복 조회를 제한합니다.
- 조회수 업데이트를 rate limit 또는 비동기 집계로 분리합니다.

## 양호한 방어 확인

- CSRF middleware가 활성화되어 있고 POST 요청에서 토큰 누락이 차단됩니다 (`config/settings.py:56`).
- Markdown은 `markdown` 변환 후 `bleach.clean()`과 `protocols=["http", "https", "mailto"]`로 정화됩니다 (`blog/utils.py:37`).
- 게시글/댓글/프로필 출력은 Django 템플릿 자동 escaping을 사용합니다.
- 검색은 Django ORM `Q(...__icontains=...)` 기반이라 테스트 payload에서 SQL 오류가 발생하지 않았습니다.
- 비공개 초안 목록은 `@login_required`로 보호됩니다.
- 응답 헤더에 `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`, `Cross-Origin-Opener-Policy: same-origin`이 포함됩니다.

## 의존성 점검

설치 확인:

- `Django 6.0.5`
- `Markdown 3.10.2`
- `bleach 6.3.0`
- `psycopg[binary] >=3.2,<4`

`pip-audit`는 현재 가상환경에 없어 자동 CVE 스캔은 실행하지 못했습니다. 수동 확인 기준으로 Django 6.0.5는 2026-05-05 보안 릴리스이며, 공식 문서는 6.0.5가 6.0.4의 low severity 보안 이슈 3건을 수정했다고 설명합니다. Django 6.0.6은 2026-06-03 예정 릴리스로 표시되어 있어 점검일 현재 즉시 적용 가능한 다음 패치로 보이지 않습니다. Bleach 6.3.0의 PyPI 변경 기록은 해당 릴리스의 security fixes가 없다고 표시합니다.

참고:
- https://docs.djangoproject.com/en/6.0/releases/6.0.5/
- https://docs.djangoproject.com/en/6.0/releases/6.0.6/
- https://pypi.org/pypi/bleach

## 실행한 검증

- `curl -i http://localhost:8000/`
- `curl -i http://localhost:8000/accounts/login/`
- `curl -i -H "Host: evil.example" http://localhost:8000/`
- Python stdlib 기반 세션 테스트: local-login, 게시글 생성/삭제, XSS payload, CSRF 누락, SQLi 유사 검색, 비인증 초안 접근
- `.venv\Scripts\python.exe manage.py check --deploy`
- `.venv\Scripts\python.exe manage.py test` -> 19 tests passed

## 우선 조치 순서

1. 운영/공유 환경에서는 `DEBUG=False` 강제 및 오류 페이지 비노출화.
2. `/accounts/local-login/` 제거 또는 localhost/debug 한정 가드 추가.
3. 운영 secret, HTTPS, secure cookie, HSTS 설정 분리.
4. 로그인/가입/작성 endpoint rate limit 적용.
5. 외부 이미지 정책과 조회수 중복 집계 정책 결정.
