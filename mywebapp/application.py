# app.py
from flask import Flask, render_template, jsonify, request
import time
import random

# Flask 앱 생성
app = Flask(__name__)

# 디스코드 웹훅 설정 (선택사항)
# 디스코드 웹훅 URL을 설정하려면 아래에 실제 URL을 입력하세요
# 웹훅 생성 방법: Discord 서버 설정 > 연동 > 웹후크 > 새 웹후크 만들기
DISCORD_WEBHOOK_URL = "본인 웹훅"

# 웹훅 알림 설정
if DISCORD_WEBHOOK_URL and DISCORD_WEBHOOK_URL != "{DISCORD_WEBHOOK_URL}":
    app.setup_webhook_notifier(webhook_url=DISCORD_WEBHOOK_URL, enabled=True)
    print(f"✅ 디스코드 웹훅 알림이 활성화되었습니다.")

# 주간 이메일 보고서 설정 (선택사항)
# Gmail 사용 시 앱 비밀번호가 필요합니다. (Google 계정 > 보안 > 2단계 인증 > 앱 비밀번호)
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",  # Gmail SMTP 서버
    "smtp_port": 587,
    "sender_email": "본인 이메일일",  # 발신자 이메일
    "sender_password": "자신 비밀번호 입력",  # Gmail 앱 비밀번호 (공백 포함 문자열)
    "recipients": ["본인 이메일"],  # 수신자 이메일 목록
    "schedule_day": "monday",  # 매주 월요일
    "schedule_time": "09:00"  # 오전 9시
}

# 주간 보고서 활성화
sender_email = EMAIL_CONFIG.get("sender_email", "")
sender_password = EMAIL_CONFIG.get("sender_password", "")
recipients = EMAIL_CONFIG.get("recipients", [])

# 플레이스홀더가 아닌 실제 값이 입력되었는지 확인
if (sender_email and sender_email != "{본인이메일}" and 
    sender_password and sender_password != "{GMAIL_APP_PASSWORD}" and
    recipients and recipients != ["{본인이메일}"]):
    app.setup_weekly_reporting(
        smtp_server=EMAIL_CONFIG["smtp_server"],
        smtp_port=EMAIL_CONFIG["smtp_port"],
        sender_email=sender_email,
        sender_password=sender_password,
        recipients=recipients,
        schedule_day=EMAIL_CONFIG["schedule_day"],
        schedule_time=EMAIL_CONFIG["schedule_time"]
    )
else:
    print("ℹ️ 주간 이메일 보고서가 설정되지 않았습니다. EMAIL_CONFIG를 설정하세요.")

# 메인 페이지 라우트 설정
@app.route("/")
def index():
    return render_template("index.html", title="Flask 웹 애플리케이션")

# 모니터링 대시보드 페이지
@app.route("/monitoring")
def monitoring_dashboard():
    """모니터링 대시보드 페이지"""
    return render_template("monitoring.html")

# 테스트용 라우트
@app.route("/test/normal")
def test_normal():
    """정상 요청 테스트"""
    return jsonify({"message": "정상 요청이 성공적으로 처리되었습니다.", "status": "success"})

@app.route("/test/slow")
def test_slow():
    """느린 요청 테스트 (1-3초 지연)"""
    delay = random.uniform(1.0, 3.0)
    time.sleep(delay)
    return jsonify({
        "message": f"느린 요청이 {delay:.2f}초 후 처리되었습니다.",
        "delay_seconds": delay,
        "status": "success"
    })

@app.route("/test/error")
def test_error():
    """오류 발생 테스트"""
    raise ValueError("테스트용 오류입니다. 모니터링에서 확인할 수 있습니다.")

@app.route("/test/notfound")
def test_notfound():
    """404 오류 테스트"""
    from flask import abort
    abort(404)

@app.route("/test/server-error")
def test_server_error():
    """500 서버 오류 테스트"""
    from flask import abort
    abort(500)

# 모니터링 라우트
@app.route("/monitoring/stats")
def monitoring_stats():
    """모니터링 통계 조회"""
    return jsonify(app.get_monitoring_stats())

@app.route("/monitoring/requests")
def monitoring_requests():
    """최근 요청 조회"""
    return jsonify(app.get_request_metrics(limit=100))

@app.route("/monitoring/endpoints")
def monitoring_endpoints():
    """엔드포인트별 통계 조회"""
    return jsonify(app.get_endpoint_stats())

@app.route("/health")
def health():
    """헬스 체크"""
    stats = app.get_monitoring_stats()
    error_rate = app.get_error_rate(time_window=60)
    
    # 간단한 헬스 체크 로직
    if error_rate > 0.1:  # 오류율 10% 초과
        status = "degraded"
    elif error_rate > 0.05:  # 오류율 5% 초과
        status = "warning"
    else:
        status = "healthy"
    
    return jsonify({
        "status": status,
        "uptime_seconds": stats.get("uptime_seconds", 0),
        "error_rate": error_rate
    })

# 알림 API 라우트
@app.route("/api/alerts")
def get_alerts():
    """최근 알림 목록 조회"""
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = request.args.get('limit', 10, type=int)
    return jsonify(app.get_recent_alerts(limit=limit, unread_only=unread_only))

@app.route("/api/alerts/unread-count")
def get_unread_count():
    """읽지 않은 알림 수 조회"""
    return jsonify({"count": app.get_unread_alert_count()})

@app.route("/api/alerts/<alert_id>/read", methods=["POST"])
def mark_alert_read(alert_id):
    """알림 읽음 처리"""
    success = app.mark_alert_read(alert_id)
    return jsonify({"success": success})

@app.route("/api/alerts/read-all", methods=["POST"])
def mark_all_alerts_read():
    """모든 알림 읽음 처리"""
    count = app._alert_manager.mark_all_read()
    return jsonify({"success": True, "count": count})

# 테스트 리포트 발송 (개발/테스트용)
@app.route("/api/reports/test", methods=["GET", "POST"])
def send_test_report():
    """테스트 리포트 즉시 발송"""
    try:
        success = app.send_test_report()
        if success:
            return jsonify({
                "success": True, 
                "message": "✅ 테스트 리포트가 성공적으로 발송되었습니다. 이메일을 확인하세요. (서버 콘솔 로그도 확인하세요.)"
            })
        else:
            return jsonify({
                "success": False, 
                "message": "❌ 테스트 리포트 발송에 실패했습니다. 서버 콘솔의 오류 메시지를 확인하세요."
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"❌ 오류 발생: {str(e)}"
        }), 500

# 서버 실행
if __name__ == "__main__":
    app.run(debug=True)  # http://127.0.0.1:5000


