# app.py
from flask import Flask, render_template, jsonify
import time
import random

# Flask 앱 생성
app = Flask(__name__)

# 메인 페이지 라우트 설정
@app.route("/")
def index():
    return render_template("index.html", title="Flask Monitoring Dashboard")

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

# 서버 실행
if __name__ == "__main__":
    app.run(debug=True)  # http://127.0.0.1:5000


