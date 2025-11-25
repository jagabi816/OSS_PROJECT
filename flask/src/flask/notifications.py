"""
Flask 알림 시스템

오류 발생 시 실시간 알림을 발송하고 대시보드에 표시합니다.
"""
import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.request import Request, urlopen
from urllib.error import URLError


@dataclass
class Alert:
    """알림 데이터"""
    id: str
    timestamp: float
    alert_type: str  # 'error', 'warning', 'info'
    title: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    read: bool = False


class WebhookNotifier:
    """웹훅을 통한 알림 발송 (디스코드, 슬랙 등)"""
    
    def __init__(self, webhook_url: Optional[str] = None, enabled: bool = True):
        """초기화
        
        Args:
            webhook_url: 웹훅 URL (디스코드, 슬랙 등)
            enabled: 알림 활성화 여부
        """
        self.webhook_url = webhook_url
        self.enabled = enabled and webhook_url is not None
        self._lock = threading.Lock()
    
    def send_discord_notification(
        self,
        title: str,
        description: str,
        error_type: Optional[str] = None,
        path: Optional[str] = None,
        status_code: Optional[int] = None,
        timestamp: Optional[float] = None
    ) -> bool:
        """디스코드 웹훅으로 알림 발송
        
        Args:
            title: 알림 제목
            description: 알림 설명
            error_type: 오류 타입
            path: 요청 경로
            status_code: HTTP 상태 코드
            timestamp: 발생 시간
            
        Returns:
            bool: 발송 성공 여부
        """
        if not self.enabled:
            return False
        
        try:
            # 디스코드 Embed 형식
            color = 15158332 if status_code and status_code >= 500 else 16776960  # 빨강 또는 노랑
            
            fields = []
            if path:
                fields.append({"name": "경로", "value": path, "inline": True})
            if status_code:
                fields.append({"name": "상태 코드", "value": str(status_code), "inline": True})
            if error_type:
                fields.append({"name": "오류 타입", "value": error_type, "inline": True})
            
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "fields": fields,
                "timestamp": datetime.fromtimestamp(timestamp or time.time()).isoformat() if timestamp else None
            }
            
            payload = {
                "embeds": [embed]
            }
            
            # 비동기로 발송 (메인 스레드 블로킹 방지)
            thread = threading.Thread(
                target=self._send_webhook_async,
                args=(payload,),
                daemon=True
            )
            thread.start()
            return True
            
        except Exception as e:
            print(f"웹훅 발송 오류: {e}")
            return False
    
    def send_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """알림 발송 (일반적인 인터페이스)
        
        Args:
            alert_type: 알림 타입 ('error', 'warning', 'info')
            title: 알림 제목
            message: 알림 메시지
            details: 추가 상세 정보 (path, status_code, error_type 등)
            
        Returns:
            bool: 발송 성공 여부
        """
        if not self.enabled:
            return False
        
        # details에서 정보 추출
        path = details.get("path") if details else None
        status_code = details.get("status_code") if details else None
        error_type = details.get("error_type") if details else None
        
        # send_discord_notification 호출
        return self.send_discord_notification(
            title=title,
            description=message,
            error_type=error_type,
            path=path,
            status_code=status_code,
            timestamp=time.time()
        )
    
    def _send_webhook_async(self, payload: Dict[str, Any]) -> None:
        """비동기로 웹훅 발송"""
        try:
            req = Request(
                self.webhook_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Flask-Webhook-Notifier/1.0'
                },
                method='POST'
            )
            response = urlopen(req, timeout=5)
            # 성공적으로 발송됨 (200-299 상태 코드)
            if response.getcode() not in range(200, 300):
                print(f"⚠️ 웹훅 발송 실패: HTTP {response.getcode()}")
            else:
                print(f"✅ 디스코드 웹훅 알림이 성공적으로 발송되었습니다.")
        except URLError as e:
            error_msg = str(e)
            if hasattr(e, 'code'):
                if e.code == 401:
                    print(f"⚠️ 디스코드 웹훅 오류 (401 Unauthorized):")
                    print(f"   - 웹훅 토큰이 잘못되었거나 만료되었습니다.")
                    print(f"   - 디스코드에서 웹훅을 다시 생성하고 새 URL을 사용하세요.")
                    print(f"   - 웹훅 URL: {self.webhook_url[:60]}...")
                elif e.code == 403:
                    print(f"⚠️ 디스코드 웹훅 오류 (403 Forbidden):")
                    print(f"   - 웹훅 URL이 잘못되었거나 권한이 없습니다.")
                    print(f"   - 디스코드 앱을 통해 생성한 웹훅인 경우, 권한 설정을 확인하세요.")
                    print(f"   - 채널 설정에서 직접 생성한 웹훅을 사용하는 것을 권장합니다.")
                    print(f"   - 웹훅 URL: {self.webhook_url[:60]}...")
                elif e.code == 404:
                    print(f"⚠️ 디스코드 웹훅 오류 (404 Not Found):")
                    print(f"   - 웹훅이 삭제되었거나 URL이 잘못되었습니다.")
                    print(f"   - 디스코드에서 웹훅을 다시 생성하고 새 URL을 사용하세요.")
                else:
                    print(f"⚠️ 웹훅 요청 실패 (HTTP {e.code}): {error_msg}")
            else:
                print(f"⚠️ 웹훅 요청 실패: {error_msg}")
        except Exception as e:
            print(f"⚠️ 웹훅 발송 오류: {e}")


class AlertManager:
    """알림 관리자 - 대시보드 알림 관리"""
    
    def __init__(self, max_alerts: int = 50):
        """초기화
        
        Args:
            max_alerts: 최대 저장할 알림 수
        """
        self._max_alerts = max_alerts
        self._alerts: deque = deque(maxlen=max_alerts)
        self._lock = threading.Lock()
        self._alert_counter = 0
    
    def add_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """알림 추가
        
        Args:
            alert_type: 알림 타입 ('error', 'warning', 'info')
            title: 알림 제목
            message: 알림 메시지
            details: 추가 상세 정보
            
        Returns:
            str: 알림 ID
        """
        with self._lock:
            self._alert_counter += 1
            alert_id = f"alert_{int(time.time())}_{self._alert_counter}"
            
            alert = Alert(
                id=alert_id,
                timestamp=time.time(),
                alert_type=alert_type,
                title=title,
                message=message,
                details=details or {},
                read=False
            )
            
            self._alerts.append(alert)
            return alert_id
    
    def get_recent_alerts(self, limit: int = 10, unread_only: bool = False) -> List[Dict[str, Any]]:
        """최근 알림 목록 조회
        
        Args:
            limit: 반환할 최대 알림 수
            unread_only: 읽지 않은 알림만 반환
            
        Returns:
            list: 알림 목록
        """
        with self._lock:
            alerts = list(self._alerts)
            if unread_only:
                alerts = [a for a in alerts if not a.read]
            
            # 최신순으로 정렬
            alerts.sort(key=lambda x: x.timestamp, reverse=True)
            
            return [
                {
                    "id": alert.id,
                    "timestamp": alert.timestamp,
                    "datetime": datetime.fromtimestamp(alert.timestamp).isoformat(),
                    "type": alert.alert_type,
                    "title": alert.title,
                    "message": alert.message,
                    "details": alert.details,
                    "read": alert.read
                }
                for alert in alerts[:limit]
            ]
    
    def mark_alert_read(self, alert_id: str) -> bool:
        """알림을 읽음 처리
        
        Args:
            alert_id: 알림 ID
            
        Returns:
            bool: 성공 여부
        """
        with self._lock:
            for alert in self._alerts:
                if alert.id == alert_id:
                    alert.read = True
                    return True
            return False
    
    def mark_all_read(self) -> int:
        """모든 알림을 읽음 처리
        
        Returns:
            int: 읽음 처리된 알림 수
        """
        with self._lock:
            count = 0
            for alert in self._alerts:
                if not alert.read:
                    alert.read = True
                    count += 1
            return count
    
    def get_unread_count(self) -> int:
        """읽지 않은 알림 수 조회
        
        Returns:
            int: 읽지 않은 알림 수
        """
        with self._lock:
            return sum(1 for alert in self._alerts if not alert.read)

