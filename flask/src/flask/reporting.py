"""
Flask 주간 이메일 보고서 기능

매주 월요일 지정된 시간에 지난 주 통계를 이메일로 발송합니다.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class WeeklyReport:
    """주간 리포트 데이터"""
    start_date: datetime
    end_date: datetime
    total_requests: int
    total_errors: int
    error_rate: float
    avg_response_time: float
    top_endpoints: List[Dict[str, Any]]
    error_breakdown: Dict[str, int]
    status_code_distribution: Dict[int, int]
    hourly_distribution: Dict[int, int]
    daily_distribution: Dict[int, int]


class ReportGenerator:
    """주간 리포트 생성기"""
    
    def __init__(self, monitoring_collector):
        """초기화
        
        Args:
            monitoring_collector: MonitoringCollector 인스턴스
        """
        self.monitoring = monitoring_collector
    
    def generate_weekly_report(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> WeeklyReport:
        """지정된 기간의 주간 리포트 생성
        
        Args:
            start_date: 시작 날짜/시간
            end_date: 종료 날짜/시간
            
        Returns:
            WeeklyReport: 주간 리포트 데이터
        """
        stats = self.monitoring.get_weekly_statistics(start_date, end_date)
        
        return WeeklyReport(
            start_date=start_date,
            end_date=end_date,
            total_requests=stats["total_requests"],
            total_errors=stats["total_errors"],
            error_rate=stats["error_rate"],
            avg_response_time=stats["avg_response_time"],
            top_endpoints=stats["top_endpoints"],
            error_breakdown=stats["error_breakdown"],
            status_code_distribution=stats["status_code_distribution"],
            hourly_distribution=stats["hourly_distribution"],
            daily_distribution=stats["daily_distribution"]
        )
    
    def format_report_html(self, report: WeeklyReport) -> str:
        """리포트를 HTML 형식으로 포맷팅
        
        Args:
            report: WeeklyReport 인스턴스
            
        Returns:
            str: HTML 형식의 리포트
        """
        weekday_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        
        # 요일별 분포 텍스트
        daily_text = "\n".join([
            f"  • {weekday_names[day]}: {count}건"
            for day, count in sorted(report.daily_distribution.items())
        ]) if report.daily_distribution else "  • 데이터 없음"
        
        # 상위 엔드포인트 텍스트
        top_endpoints_text = "\n".join([
            f"  {i+1}. {ep['endpoint']} - {ep['count']}회 (오류: {ep['error_count']}건, 평균 응답: {ep['avg_duration']:.2f}ms)"
            for i, ep in enumerate(report.top_endpoints[:5])
        ]) if report.top_endpoints else "  • 데이터 없음"
        
        # 오류 분류 텍스트
        error_breakdown_text = "\n".join([
            f"  • {error_type}: {count}건"
            for error_type, count in sorted(
                report.error_breakdown.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        ]) if report.error_breakdown else "  • 오류 없음"
        
        # 상태 코드 분포 텍스트
        status_codes_text = "\n".join([
            f"  • {code}: {count}건"
            for code, count in sorted(report.status_code_distribution.items())
        ]) if report.status_code_distribution else "  • 데이터 없음"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #1f2937;
            margin-top: 30px;
            border-left: 4px solid #667eea;
            padding-left: 10px;
        }}
        .summary-box {{
            background: #f3f4f6;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .metric {{
            display: inline-block;
            margin: 10px 20px 10px 0;
            padding: 10px 15px;
            background: white;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-label {{
            font-size: 0.9em;
            color: #6b7280;
        }}
        .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #1f2937;
        }}
        .error-highlight {{
            color: #dc2626;
            font-weight: bold;
        }}
        .success-highlight {{
            color: #059669;
            font-weight: bold;
        }}
        ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        li {{
            padding: 5px 0;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            color: #6b7280;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>📊 Flask 애플리케이션 주간 리포트</h1>
    <p><strong>보고 기간:</strong> {report.start_date.strftime('%Y년 %m월 %d일')} ~ {report.end_date.strftime('%Y년 %m월 %d일')}</p>
    
    <div class="summary-box">
        <h2 style="margin-top: 0;">📈 요약</h2>
        <div class="metric">
            <div class="metric-label">총 요청 수</div>
            <div class="metric-value">{report.total_requests:,}건</div>
        </div>
        <div class="metric">
            <div class="metric-label">총 오류 수</div>
            <div class="metric-value error-highlight">{report.total_errors:,}건</div>
        </div>
        <div class="metric">
            <div class="metric-label">오류율</div>
            <div class="metric-value {'error-highlight' if report.error_rate > 0.05 else 'success-highlight'}">{report.error_rate * 100:.2f}%</div>
        </div>
        <div class="metric">
            <div class="metric-label">평균 응답 시간</div>
            <div class="metric-value">{report.avg_response_time:.2f}ms</div>
        </div>
    </div>
    
    <h2>⚠️ 오류 현황</h2>
    <p><strong>총 오류:</strong> {report.total_errors:,}건</p>
    <p><strong>오류율:</strong> <span class="{'error-highlight' if report.error_rate > 0.05 else ''}">{report.error_rate * 100:.2f}%</span></p>
    <h3>오류 타입별 분류:</h3>
    <pre>{error_breakdown_text}</pre>
    
    <h2>⚡ 성능 지표</h2>
    <p><strong>평균 응답 시간:</strong> {report.avg_response_time:.2f}ms</p>
    
    <h2>🔥 인기 엔드포인트 (Top 5)</h2>
    <pre>{top_endpoints_text}</pre>
    
    <h2>📊 상태 코드 분포</h2>
    <pre>{status_codes_text}</pre>
    
    <h2>📅 요일별 요청 분포</h2>
    <pre>{daily_text}</pre>
    
    <div class="footer">
        <p>이 리포트는 Flask 모니터링 시스템에서 자동으로 생성되었습니다.</p>
        <p>생성 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}</p>
    </div>
</body>
</html>
"""
        return html
    
    def format_report_text(self, report: WeeklyReport) -> str:
        """리포트를 텍스트 형식으로 포맷팅
        
        Args:
            report: WeeklyReport 인스턴스
            
        Returns:
            str: 텍스트 형식의 리포트
        """
        weekday_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        
        text = f"""
Flask 애플리케이션 주간 리포트
보고 기간: {report.start_date.strftime('%Y년 %m월 %d일')} ~ {report.end_date.strftime('%Y년 %m월 %d일')}

📈 요약
- 총 요청 수: {report.total_requests:,}건
- 총 오류 수: {report.total_errors:,}건
- 오류율: {report.error_rate * 100:.2f}%
- 평균 응답 시간: {report.avg_response_time:.2f}ms

⚠️ 오류 현황
- 총 오류: {report.total_errors:,}건
- 오류율: {report.error_rate * 100:.2f}%

🔥 인기 엔드포인트 (Top 5)
"""
        for i, ep in enumerate(report.top_endpoints[:5], 1):
            text += f"{i}. {ep['endpoint']} - {ep['count']}회 (오류: {ep['error_count']}건)\n"
        
        text += f"\n📊 상태 코드 분포\n"
        for code, count in sorted(report.status_code_distribution.items()):
            text += f"- {code}: {count}건\n"
        
        text += f"\n📅 요일별 요청 분포\n"
        for day, count in sorted(report.daily_distribution.items()):
            text += f"- {weekday_names[day]}: {count}건\n"
        
        text += f"\n생성 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}\n"
        
        return text


class EmailReporter:
    """이메일 리포트 발송"""
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str
    ):
        """초기화
        
        Args:
            smtp_server: SMTP 서버 주소
            smtp_port: SMTP 포트
            sender_email: 발신자 이메일
            sender_password: 발신자 비밀번호
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
    
    def send_weekly_report(
        self,
        recipients: List[str],
        report: WeeklyReport,
        html_content: str,
        text_content: str
    ) -> bool:
        """주간 리포트 이메일 발송
        
        Args:
            recipients: 수신자 이메일 목록
            report: WeeklyReport 인스턴스
            html_content: HTML 형식 리포트
            text_content: 텍스트 형식 리포트
            
        Returns:
            bool: 발송 성공 여부
        """
        try:
            # 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Flask 주간 리포트 ({report.start_date.strftime('%Y-%m-%d')} ~ {report.end_date.strftime('%Y-%m-%d')})"
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(recipients)
            
            # 텍스트 및 HTML 본문 첨부
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # SMTP 서버 연결 및 발송 (타임아웃 설정 - 5초로 단축)
            print(f"      SMTP 연결 시도: {self.smtp_server}:{self.smtp_port}")
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=5) as server:
                print(f"      STARTTLS 시작...")
                server.starttls()
                print(f"      로그인 시도...")
                server.login(self.sender_email, self.sender_password)
                print(f"      이메일 발송 중...")
                server.send_message(msg)
                print(f"      이메일 발송 완료!")
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ 이메일 인증 오류: {e}")
            print(f"   발신자 이메일과 비밀번호를 확인하세요.")
            print(f"   Gmail의 경우 앱 비밀번호를 사용해야 합니다.")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ SMTP 오류: {e}")
            return False
        except Exception as e:
            print(f"❌ 이메일 발송 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

