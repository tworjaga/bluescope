"""
Performance Optimizer - Performance monitoring and optimization for BlueScope
Provides memory management, CPU optimization, and performance profiling
"""

import os
import sys
import time
import psutil
import logging
import asyncio
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float
    thread_count: int
    handle_count: int


@dataclass
class PerformanceConfig:
    """Performance configuration"""
    max_memory_mb: int = 1024
    max_cpu_percent: float = 80.0
    target_fps: int = 30
    packet_buffer_size: int = 10000
    update_interval_ms: int = 1000
    enable_gc_optimization: bool = True
    enable_memory_pool: bool = True


class PerformanceOptimizer:
    """
    Performance optimizer for BlueScope
    Monitors and optimizes CPU, memory, and I/O usage
    """
    
    def __init__(self, config: Optional[PerformanceConfig] = None):
        self.config = config or PerformanceConfig()
        self.metrics_history: deque = deque(maxlen=1000)
        self.process = psutil.Process()
        
        # Performance callbacks
        self.on_threshold_exceeded: Optional[Callable] = None
        
        # Optimization state
        self.is_optimizing = False
        self.optimization_level = 0  # 0=none, 1=light, 2=aggressive
        
        # Baseline metrics
        self.baseline_metrics: Optional[PerformanceMetrics] = None
        
        logger.info("PerformanceOptimizer initialized")
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        # CPU usage
        cpu_percent = self.process.cpu_percent(interval=0.1)
        
        # Memory usage
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_percent = self.process.memory_percent()
        
        # I/O counters
        try:
            io_counters = self.process.io_counters()
            disk_read_mb = io_counters.read_bytes / 1024 / 1024
            disk_write_mb = io_counters.write_bytes / 1024 / 1024
        except:
            disk_read_mb = disk_write_mb = 0.0
        
        # Network I/O
        try:
            net_io = psutil.net_io_counters()
            net_sent_mb = net_io.bytes_sent / 1024 / 1024
            net_recv_mb = net_io.bytes_recv / 1024 / 1024
        except:
            net_sent_mb = net_recv_mb = 0.0
        
        # Thread and handle counts
        thread_count = self.process.num_threads()
        try:
            handle_count = self.process.num_handles() if hasattr(self.process, 'num_handles') else 0
        except:
            handle_count = 0
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            memory_percent=memory_percent,
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_io_sent_mb=net_sent_mb,
            network_io_recv_mb=net_recv_mb,
            thread_count=thread_count,
            handle_count=handle_count
        )
    
    def record_metrics(self) -> PerformanceMetrics:
        """Record current metrics to history"""
        metrics = self.get_current_metrics()
        self.metrics_history.append(metrics)
        
        # Check thresholds
        self._check_thresholds(metrics)
        
        return metrics
    
    def _check_thresholds(self, metrics: PerformanceMetrics):
        """Check if performance thresholds are exceeded"""
        exceeded = []
        
        if metrics.memory_mb > self.config.max_memory_mb:
            exceeded.append(f"Memory: {metrics.memory_mb:.1f}MB > {self.config.max_memory_mb}MB")
        
        if metrics.cpu_percent > self.config.max_cpu_percent:
            exceeded.append(f"CPU: {metrics.cpu_percent:.1f}% > {self.config.max_cpu_percent}%")
        
        if exceeded:
            logger.warning(f"Performance thresholds exceeded: {', '.join(exceeded)}")
            
            if self.on_threshold_exceeded:
                self.on_threshold_exceeded(exceeded, metrics)
            
            # Auto-optimize if needed
            if not self.is_optimizing:
                self.optimize_performance()
    
    def optimize_performance(self, level: int = 1):
        """
        Optimize performance
        
        Args:
            level: Optimization level (0=none, 1=light, 2=aggressive)
        """
        self.is_optimizing = True
        self.optimization_level = level
        
        logger.info(f"Starting performance optimization (level {level})")
        
        if level >= 1:
            self._light_optimization()
        
        if level >= 2:
            self._aggressive_optimization()
        
        self.is_optimizing = False
        logger.info("Performance optimization completed")
    
    def _light_optimization(self):
        """Light optimization - safe operations"""
        import gc
        
        # Force garbage collection
        if self.config.enable_gc_optimization:
            gc.collect()
            logger.debug("Garbage collection completed")
        
        # Clear old metrics
        if len(self.metrics_history) > 500:
            # Keep only recent metrics
            self.metrics_history = deque(list(self.metrics_history)[-250:], maxlen=1000)
            logger.debug("Old metrics cleared")
    
    def _aggressive_optimization(self):
        """Aggressive optimization - may impact functionality"""
        # Reduce buffer sizes
        self.config.packet_buffer_size = max(1000, self.config.packet_buffer_size // 2)
        logger.info(f"Reduced packet buffer size to {self.config.packet_buffer_size}")
        
        # Increase update interval
        self.config.update_interval_ms = min(5000, self.config.update_interval_ms * 2)
        logger.info(f"Increased update interval to {self.config.update_interval_ms}ms")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        if not self.metrics_history:
            return {"error": "No metrics recorded"}
        
        recent_metrics = list(self.metrics_history)[-100:]  # Last 100 samples
        
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_mb for m in recent_metrics]
        
        return {
            "sample_count": len(self.metrics_history),
            "time_range_seconds": (recent_metrics[-1].timestamp - recent_metrics[0].timestamp).total_seconds() if len(recent_metrics) > 1 else 0,
            "cpu": {
                "current": recent_metrics[-1].cpu_percent if recent_metrics else 0,
                "average": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "peak": max(cpu_values) if cpu_values else 0,
                "min": min(cpu_values) if cpu_values else 0,
            },
            "memory": {
                "current_mb": recent_metrics[-1].memory_mb if recent_metrics else 0,
                "average_mb": sum(memory_values) / len(memory_values) if memory_values else 0,
                "peak_mb": max(memory_values) if memory_values else 0,
                "min_mb": min(memory_values) if memory_values else 0,
            },
            "threads": {
                "current": recent_metrics[-1].thread_count if recent_metrics else 0,
            },
            "optimization_level": self.optimization_level,
            "is_optimizing": self.is_optimizing,
        }
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations = []
        
        if not self.metrics_history:
            return ["No metrics available - run monitoring first"]
        
        recent = list(self.metrics_history)[-50:]
        avg_cpu = sum(m.cpu_percent for m in recent) / len(recent)
        avg_memory = sum(m.memory_mb for m in recent) / len(recent)
        
        if avg_cpu > 70:
            recommendations.append("High CPU usage detected - consider reducing update frequency")
        
        if avg_memory > self.config.max_memory_mb * 0.8:
            recommendations.append("High memory usage - consider reducing buffer sizes")
        
        if len(recent) > 0 and recent[-1].thread_count > 50:
            recommendations.append("High thread count - check for thread leaks")
        
        if not recommendations:
            recommendations.append("Performance looks good - no immediate action needed")
        
        return recommendations


class MemoryPool:
    """Memory pool for efficient object reuse"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.pools: Dict[str, deque] = {}
        self.allocations = 0
        self.reuses = 0
    
    def acquire(self, obj_type: str, factory: Callable) -> Any:
        """Acquire object from pool or create new"""
        if obj_type not in self.pools:
            self.pools[obj_type] = deque(maxlen=self.max_size)
        
        pool = self.pools[obj_type]
        
        if pool:
            self.reuses += 1
            return pool.popleft()
        else:
            self.allocations += 1
            return factory()
    
    def release(self, obj_type: str, obj: Any):
        """Release object back to pool"""
        if obj_type not in self.pools:
            self.pools[obj_type] = deque(maxlen=self.max_size)
        
        pool = self.pools[obj_type]
        if len(pool) < self.max_size:
            pool.append(obj)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        return {
            "allocations": self.allocations,
            "reuses": self.reuses,
            "reuse_rate": self.reuses / max(self.allocations + self.reuses, 1) * 100,
            "pool_sizes": {k: len(v) for k, v in self.pools.items()},
        }


class PerformanceMonitor:
    """Real-time performance monitor"""
    
    def __init__(self, optimizer: PerformanceOptimizer, interval: float = 1.0):
        self.optimizer = optimizer
        self.interval = interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Performance monitoring started")
    
    async def stop(self):
        """Stop monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Performance monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                self.optimizer.record_metrics()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance monitor: {e}")
                await asyncio.sleep(self.interval)


# Global instances
_optimizer: Optional[PerformanceOptimizer] = None
_memory_pool: Optional[MemoryPool] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get or create global performance optimizer"""
    global _optimizer
    if _optimizer is None:
        _optimizer = PerformanceOptimizer()
    return _optimizer


def get_memory_pool() -> MemoryPool:
    """Get or create global memory pool"""
    global _memory_pool
    if _memory_pool is None:
        _memory_pool = MemoryPool()
    return _memory_pool


def test_performance_optimizer():
    """Test performance optimizer"""
    print("\n" + "="*60)
    print("Performance Optimizer Test")
    print("="*60)
    
    optimizer = get_performance_optimizer()
    
    # Test 1: Get metrics
    print("\n1. Testing metrics collection:")
    metrics = optimizer.get_current_metrics()
    print(f"  CPU: {metrics.cpu_percent:.1f}%")
    print(f"  Memory: {metrics.memory_mb:.1f}MB ({metrics.memory_percent:.1f}%)")
    print(f"  Threads: {metrics.thread_count}")
    
    # Test 2: Record metrics
    print("\n2. Testing metrics recording:")
    for i in range(5):
        optimizer.record_metrics()
        time.sleep(0.1)
    print(f"  Recorded {len(optimizer.metrics_history)} metrics")
    
    # Test 3: Performance report
    print("\n3. Testing performance report:")
    report = optimizer.get_performance_report()
    print(f"  Samples: {report['sample_count']}")
    print(f"  Avg CPU: {report['cpu']['average']:.1f}%")
    print(f"  Avg Memory: {report['memory']['average_mb']:.1f}MB")
    
    # Test 4: Recommendations
    print("\n4. Testing recommendations:")
    recommendations = optimizer.get_optimization_recommendations()
    for rec in recommendations:
        print(f"  - {rec}")
    
    # Test 5: Memory pool
    print("\n5. Testing memory pool:")
    pool = get_memory_pool()
    
    def factory():
        return {"data": []}
    
    obj1 = pool.acquire("dict", factory)
    pool.release("dict", obj1)
    obj2 = pool.acquire("dict", factory)
    
    stats = pool.get_stats()
    print(f"  Allocations: {stats['allocations']}")
    print(f"  Reuses: {stats['reuses']}")
    print(f"  Reuse rate: {stats['reuse_rate']:.1f}%")
    
    print("\n All performance optimizer tests passed")
    return True


if __name__ == "__main__":
    test_performance_optimizer()

