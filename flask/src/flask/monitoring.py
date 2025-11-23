"""
Flask 애플리케이션 모니터링 기능

요청 처리 속도, 오류 발생 비율, 애플리케이션 상태 등을 추적합니다.
"""
import time
import threading
from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class RequestMetrics:
    """개별 요청의 메트릭"""
    timestamp: float
    path: str
    method: str
    status_code: int
    duration: float  # 밀리초
    error_occurred: bool = False
    error_type: Optional[str] = None
    endpoint: Optional[str] = None


class MonitoringCollector:
    """모니터링 데이터 수집 및 집계"""
    
    def __init__(self, max_history: int = 1000):
        """초기화
        
        Args:
            max_history: 저장할 최대 요청 기록 수
        """
        self._max_history = max_history
        self._request_history: deque = deque(maxlen=max_history)
        self._lock = threading.Lock()
        
        # 집계 데이터
        self._total_requests = 0
        self._total_errors = 0
        self._status_code_counts: Dict[int, int] = defaultdict(int)
        self._path_counts: Dict[str, int] = defaultdict(int)
        self._method_counts: Dict[str, int] = defaultdict(int)
        self._error_type_counts: Dict[str, int] = defaultdict(int)
        self._endpoint_counts: Dict[str, int] = defaultdict(int)
        
        # 성능 메트릭
        self._response_times: deque = deque(maxlen=1000)
        self._start_time = time.time()
    
    def record_request(
        self,
        path: str,
        method: str,
        status_code: int,
        duration: float,
        error_occurred: bool = False,
        error_type: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> None:
        """요청 메트릭을 기록합니다.
        
        Args:
            path: 요청 경로
            method: HTTP 메서드
            status_code: HTTP 상태 코드
            duration: 응답 시간 (밀리초)
            error_occurred: 오류 발생 여부
            error_type: 오류 타입 (있는 경우)
            endpoint: 엔드포인트 이름 (있는 경우)
        """
        with self._lock:
            timestamp = time.time()
            metrics = RequestMetrics(
                timestamp=timestamp,
                path=path,
                method=method,
                status_code=status_code,
                duration=duration,
                error_occurred=error_occurred,
                error_type=error_type,
                endpoint=endpoint
            )
            
            self._request_history.append(metrics)
            
            # 집계 데이터 업데이트
            self._total_requests += 1
            self._status_code_counts[status_code] += 1
            self._path_counts[path] += 1
            self._method_counts[method] += 1
            if endpoint:
                self._endpoint_counts[endpoint] += 1
            self._response_times.append(duration)
            
            if error_occurred:
                self._total_errors += 1
                if error_type:
                    self._error_type_counts[error_type] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """전체 통계를 반환합니다.
        
        Returns:
            dict: 통계 데이터
        """
        with self._lock:
            uptime = time.time() - self._start_time
            recent_requests = list(self._request_history)
            
            if not recent_requests:
                return {
                    "uptime_seconds": uptime,
                    "total_requests": 0,
                    "requests_per_second": 0.0,
                    "error_rate": 0.0,
                    "average_response_time_ms": 0.0,
                    "status_codes": {},
                    "top_paths": {},
                    "top_methods": {},
                    "error_types": {}
                }
            
            # 평균 응답 시간
            avg_response_time = sum(m.duration for m in recent_requests) / len(recent_requests)
            
            # 오류율
            error_rate = (
                self._total_errors / self._total_requests
                if self._total_requests > 0 else 0.0
            )
            
            # 초당 요청 수
            requests_per_second = (
                self._total_requests / uptime if uptime > 0 else 0.0
            )
            
            # 응답 시간 백분위수 계산
            sorted_times = sorted([m.duration for m in recent_requests])
            n = len(sorted_times)
            percentiles = {
                "p50": sorted_times[int(n * 0.50)] if n > 0 else 0.0,
                "p95": sorted_times[int(n * 0.95)] if n > 0 else 0.0,
                "p99": sorted_times[int(n * 0.99)] if n > 0 else 0.0,
            }
            
            # 상위 경로 (최대 10개)
            top_paths = dict(
                sorted(self._path_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            )
            
            return {
                "uptime_seconds": uptime,
                "total_requests": self._total_requests,
                "total_errors": self._total_errors,
                "requests_per_second": requests_per_second,
                "error_rate": error_rate,
                "average_response_time_ms": avg_response_time,
                "min_response_time_ms": min(m.duration for m in recent_requests),
                "max_response_time_ms": max(m.duration for m in recent_requests),
                "response_time_percentiles": percentiles,
                "status_codes": dict(self._status_code_counts),
                "top_paths": top_paths,
                "top_methods": dict(self._method_counts),
                "top_endpoints": dict(sorted(self._endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "error_types": dict(self._error_type_counts),
                "recent_request_count": len(recent_requests)
            }
    
    def get_recent_requests(self, limit: int = 100) -> List[Dict[str, Any]]:
        """최근 요청 메트릭을 반환합니다.
        
        Args:
            limit: 반환할 최대 요청 수
            
        Returns:
            list: 최근 요청 메트릭 리스트
        """
        with self._lock:
            recent = list(self._request_history)[-limit:]
            return [
                {
                    "timestamp": m.timestamp,
                    "datetime": datetime.fromtimestamp(m.timestamp).isoformat(),
                    "path": m.path,
                    "method": m.method,
                    "status_code": m.status_code,
                    "duration_ms": m.duration,
                    "error_occurred": m.error_occurred,
                    "error_type": m.error_type,
                    "endpoint": m.endpoint
                }
                for m in recent
            ]
    
    def get_error_rate(self, time_window: int = 60) -> float:
        """지정된 시간 윈도우 내의 오류 발생 비율을 반환합니다.
        
        Args:
            time_window: 시간 윈도우 (초)
            
        Returns:
            float: 오류 발생 비율 (0.0 ~ 1.0)
        """
        with self._lock:
            cutoff_time = time.time() - time_window
            recent_requests = [
                m for m in self._request_history
                if m.timestamp >= cutoff_time
            ]
            
            if not recent_requests:
                return 0.0
            
            error_count = sum(1 for m in recent_requests if m.error_occurred)
            return error_count / len(recent_requests)
    
    def get_average_response_time(self, time_window: int = 60) -> float:
        """지정된 시간 윈도우 내의 평균 응답 시간을 반환합니다.
        
        Args:
            time_window: 시간 윈도우 (초)
            
        Returns:
            float: 평균 응답 시간 (밀리초)
        """
        with self._lock:
            cutoff_time = time.time() - time_window
            recent_requests = [
                m for m in self._request_history
                if m.timestamp >= cutoff_time
            ]
            
            if not recent_requests:
                return 0.0
            
            return sum(m.duration for m in recent_requests) / len(recent_requests)
    
    def get_endpoint_stats(self) -> Dict[str, Dict[str, Any]]:
        """엔드포인트별 통계를 반환합니다.
        
        Returns:
            dict: 엔드포인트별 상세 통계
        """
        with self._lock:
            endpoint_data: Dict[str, List[RequestMetrics]] = defaultdict(list)
            
            for metric in self._request_history:
                if metric.endpoint:
                    endpoint_data[metric.endpoint].append(metric)
            
            stats = {}
            for endpoint, metrics in endpoint_data.items():
                if not metrics:
                    continue
                
                durations = [m.duration for m in metrics]
                error_count = sum(1 for m in metrics if m.error_occurred)
                
                stats[endpoint] = {
                    "request_count": len(metrics),
                    "average_response_time_ms": sum(durations) / len(durations),
                    "min_response_time_ms": min(durations),
                    "max_response_time_ms": max(durations),
                    "error_count": error_count,
                    "error_rate": error_count / len(metrics) if metrics else 0.0,
                    "status_codes": dict(
                        (code, sum(1 for m in metrics if m.status_code == code))
                        for code in set(m.status_code for m in metrics)
                    )
                }
            
            return stats
    
    def get_requests_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[RequestMetrics]:
        """지정된 날짜 범위의 요청 데이터를 반환합니다.
        
        Args:
            start_date: 시작 날짜/시간
            end_date: 종료 날짜/시간
            
        Returns:
            list: 해당 기간의 RequestMetrics 리스트
        """
        with self._lock:
            start_timestamp = start_date.timestamp()
            end_timestamp = end_date.timestamp()
            
            return [
                metric for metric in self._request_history
                if start_timestamp <= metric.timestamp <= end_timestamp
            ]
    
    def get_weekly_statistics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """주간 통계를 집계합니다.
        
        Args:
            start_date: 시작 날짜/시간
            end_date: 종료 날짜/시간
            
        Returns:
            dict: 주간 통계 데이터
        """
        try:
            # get_requests_by_date_range는 내부에서 lock을 잡으므로 여기서는 lock 밖에서 호출
            requests = self.get_requests_by_date_range(start_date, end_date)
            
            if not requests:
                return {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_requests": 0,
                    "total_errors": 0,
                    "error_rate": 0.0,
                    "avg_response_time": 0.0,
                    "top_endpoints": [],
                    "error_breakdown": {},
                    "status_code_distribution": {},
                    "hourly_distribution": {},
                    "daily_distribution": {}
                }
            
            # 기본 통계
            total_requests = len(requests)
            total_errors = sum(1 for r in requests if r.error_occurred)
            error_rate = total_errors / total_requests if total_requests > 0 else 0.0
            avg_response_time = sum(r.duration for r in requests) / total_requests
            
            # 엔드포인트별 통계
            endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
                "count": 0,
                "errors": 0,
                "total_duration": 0.0
            })
            
            for req in requests:
                endpoint = req.endpoint or req.path
                endpoint_stats[endpoint]["count"] += 1
                endpoint_stats[endpoint]["total_duration"] += req.duration
                if req.error_occurred:
                    endpoint_stats[endpoint]["errors"] += 1
            
            # 상위 엔드포인트 정렬
            top_endpoints = sorted(
                [
                    {
                        "endpoint": endpoint,
                        "count": stats["count"],
                        "error_count": stats["errors"],
                        "error_rate": stats["errors"] / stats["count"] if stats["count"] > 0 else 0.0,
                        "avg_duration": stats["total_duration"] / stats["count"] if stats["count"] > 0 else 0.0
                    }
                    for endpoint, stats in endpoint_stats.items()
                ],
                key=lambda x: x["count"],
                reverse=True
            )[:10]
            
            # 오류 타입별 분류
            error_breakdown: Dict[str, int] = defaultdict(int)
            for req in requests:
                if req.error_occurred and req.error_type:
                    error_breakdown[req.error_type] += 1
            
            # 상태 코드 분포
            status_code_distribution: Dict[int, int] = defaultdict(int)
            for req in requests:
                status_code_distribution[req.status_code] += 1
            
            # 시간대별 분포
            hourly_distribution: Dict[int, int] = defaultdict(int)
            for req in requests:
                hour = datetime.fromtimestamp(req.timestamp).hour
                hourly_distribution[hour] += 1
            
            # 요일별 분포
            daily_distribution: Dict[int, int] = defaultdict(int)
            for req in requests:
                weekday = datetime.fromtimestamp(req.timestamp).weekday()  # 0=월요일
                daily_distribution[weekday] += 1
            
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate": error_rate,
                "avg_response_time": avg_response_time,
                "top_endpoints": top_endpoints,
                "error_breakdown": dict(error_breakdown),
                "status_code_distribution": dict(status_code_distribution),
                "hourly_distribution": dict(hourly_distribution),
                "daily_distribution": dict(daily_distribution)
            }
        except Exception as e:
            print(f"⚠️ 주간 통계 생성 중 오류: {e}")
            import traceback
            traceback.print_exc()
            # 기본값 반환
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_requests": 0,
                "total_errors": 0,
                "error_rate": 0.0,
                "avg_response_time": 0.0,
                "top_endpoints": [],
                "error_breakdown": {},
                "status_code_distribution": {},
                "hourly_distribution": {},
                "daily_distribution": {}
            }

