import logging
import time
from typing import Dict, Any
from config.config import PERFORMANCE_METRICS

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self):
        self.last_request_time = time.time()
        self.scaling_factor = 1.0
        self.metrics = {
            'response_times': [],
            'error_rates': [],
            'memory_usage': [],
            'cpu_usage': []
        }

    def _check_performance_metrics(self):
        """Sistem performans metriklerini kontrol eder"""
        current_time = time.time()
        response_time = current_time - self.last_request_time
        
        if response_time > PERFORMANCE_METRICS['response_time_threshold']:
            self.scaling_factor = min(self.scaling_factor * PERFORMANCE_METRICS['scaling_factor'], 2.0)
        else:
            self.scaling_factor = max(self.scaling_factor / PERFORMANCE_METRICS['scaling_factor'], 0.5)
        
        self.last_request_time = current_time
        self._update_metrics('response_times', response_time)

    def _update_metrics(self, metric_name: str, value: float):
        """Performans metriklerini günceller"""
        self.metrics[metric_name].append(value)
        if len(self.metrics[metric_name]) > PERFORMANCE_METRICS['metric_window_size']:
            self.metrics[metric_name].pop(0)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Güncel performans metriklerini döndürür"""
        return {
            'scaling_factor': self.scaling_factor,
            'avg_response_time': sum(self.metrics['response_times']) / len(self.metrics['response_times']) if self.metrics['response_times'] else 0,
            'error_rate': sum(self.metrics['error_rates']) / len(self.metrics['error_rates']) if self.metrics['error_rates'] else 0,
            'avg_memory_usage': sum(self.metrics['memory_usage']) / len(self.metrics['memory_usage']) if self.metrics['memory_usage'] else 0,
            'avg_cpu_usage': sum(self.metrics['cpu_usage']) / len(self.metrics['cpu_usage']) if self.metrics['cpu_usage'] else 0
        }

    def log_error(self, error: Exception):
        """Hata durumunu kaydeder"""
        self._update_metrics('error_rates', 1.0)
        logger.error(f"Performans hatası: {str(error)}")

    def update_resource_usage(self, memory_usage: float, cpu_usage: float):
        """Kaynak kullanımını günceller"""
        self._update_metrics('memory_usage', memory_usage)
        self._update_metrics('cpu_usage', cpu_usage)

    def get_scaling_factor(self) -> float:
        """Güncel ölçeklendirme faktörünü döndürür"""
        self._check_performance_metrics()
        return self.scaling_factor 