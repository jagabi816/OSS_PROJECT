# Flask Monitoring Extension Project

Flask 프레임워크에 모니터링 기능을 추가한 프로젝트입니다.

## 프로젝트 개요

서버와 애플리케이션의 상태를 실시간으로 확인하거나 오류 발생 현황을 파악할 수 있는 기본적인 관측 기능이 부족합니다. 이러한 한계로 인해 서비스의 운영 상태를 체계적으로 관리하기 어렵고, 문제 발생 시 신속한 대응이 어렵다는 점을 확인하였습니다. 이에 팀 내 회의를 거쳐, Flask의 기본 구조를 유지하면서 모니터링 기능을 추가하기로 하였습니다.

## 주요 기능

### 모니터링 기능
- ✅ 요청 처리 속도 추적 (평균, 최소, 최대, 백분위수)
- ✅ 오류 발생 비율 및 오류 타입 분석
- ✅ 엔드포인트별 상세 통계
- ✅ 실시간 요청 로그
- ✅ 애플리케이션 상태 모니터링
- ✅ 웹 기반 모니터링 대시보드

### 구현 내용
- Flask 내부에 모니터링 모듈 통합 (`flask/src/flask/monitoring.py`)
- Flask 클래스에 모니터링 메서드 추가
- 웹 대시보드를 통한 직관적인 상태 확인
- 테스트 기능을 통한 모니터링 검증

## 프로젝트 구조

```
flask_test/
├── flask/                      # Flask 프레임워크 소스 코드
│   └── src/
│       └── flask/
│           ├── monitoring.py   # 모니터링 모듈 (추가됨)
│           └── app.py          # Flask 클래스 (수정됨)
│
└── mywebapp/                   # 애플리케이션 코드
    ├── application.py          # 메인 애플리케이션
    ├── templates/
    │   └── index.html         # 모니터링 대시보드
    └── static/
        └── style.css          # 대시보드 스타일
```

## 설치 및 실행

### 1. 프로젝트 클론
```bash
git clone https://github.com/jagabi816/OSS_PROJECT.git
cd OSS_PROJECT
```

### 2. 의존성 설치
```bash
# Python 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Flask 및 필요한 패키지 설치
pip install flask werkzeug jinja2
```

### 3. 애플리케이션 실행
```bash
cd mywebapp
python application.py
```

### 4. 브라우저에서 접속
```
http://127.0.0.1:5000
```

## 사용 방법

### 모니터링 API 엔드포인트

- `GET /monitoring/stats` - 전체 통계 조회
- `GET /monitoring/requests` - 최근 요청 목록
- `GET /monitoring/endpoints` - 엔드포인트별 통계
- `GET /health` - 헬스 체크

### 테스트 엔드포인트

- `GET /test/normal` - 정상 요청 테스트
- `GET /test/slow` - 느린 요청 테스트 (1-3초 지연)
- `GET /test/error` - ValueError 발생 테스트
- `GET /test/notfound` - 404 오류 테스트
- `GET /test/server-error` - 500 서버 오류 테스트

### 웹 대시보드

브라우저에서 `http://127.0.0.1:5000`에 접속하면 모니터링 대시보드를 확인할 수 있습니다.

- 실시간 통계 카드
- 테스트 버튼을 통한 요청/오류 발생 테스트
- 최근 요청 로그 테이블
- 엔드포인트별 상세 통계
- 자동 새로고침 기능

## 기술 스택

- Python 3.x
- Flask (수정된 버전)
- HTML/CSS/JavaScript
- Werkzeug
- Jinja2

## 개발자

- 프로젝트: OSS_PROJECT
- GitHub: jagabi816

## 라이선스

이 프로젝트는 Flask 프레임워크를 기반으로 하며, Flask의 라이선스를 따릅니다.

