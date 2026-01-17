"""Tests for cache, monitoring, and enhanced features."""
import pytest
import time
from dredge.cache import MemoryCache, FileCache, ResultCache
from dredge.monitoring import MetricsCollector, Tracer, Timer
from dredge.string_theory import StringTheoryNN, get_optimal_device, get_device_info
import torch
import tempfile
import shutil


class TestCache:
    """Test caching functionality."""
    
    def test_memory_cache_basic(self):
        """Test basic memory cache operations."""
        cache = MemoryCache()
        
        # Set and get
        assert cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Non-existent key
        assert cache.get("nonexistent") is None
        
        # Delete
        assert cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_memory_cache_ttl(self):
        """Test memory cache TTL expiration."""
        cache = MemoryCache()
        
        # Set with short TTL
        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_file_cache_basic(self):
        """Test basic file cache operations."""
        tmpdir = tempfile.mkdtemp()
        try:
            cache = FileCache(cache_dir=tmpdir)
            
            # Set and get
            assert cache.set("key1", {"data": "value1"})
            result = cache.get("key1")
            assert result == {"data": "value1"}
            
            # Clear
            assert cache.clear()
            assert cache.get("key1") is None
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_result_cache_spectrum(self):
        """Test result cache for spectrum data."""
        cache = ResultCache()
        
        # Set spectrum
        result = {"energy_spectrum": [0.5, 1.0, 1.5]}
        cache.set_spectrum(max_modes=10, dimensions=10, result=result)
        
        # Get spectrum
        cached = cache.get_spectrum(max_modes=10, dimensions=10)
        assert cached == result
        
        # Different parameters should miss
        assert cache.get_spectrum(max_modes=20, dimensions=10) is None
    
    def test_result_cache_unified_inference(self):
        """Test result cache for unified inference."""
        cache = ResultCache()
        
        # Set result
        result = {"coupled_amplitude": 1.5, "success": True}
        cache.set_unified_inference(
            dredge_insight="test",
            quasimoto_coords=[0.5],
            string_modes=[1, 2],
            result=result
        )
        
        # Get result
        cached = cache.get_unified_inference(
            dredge_insight="test",
            quasimoto_coords=[0.5],
            string_modes=[1, 2]
        )
        assert cached == result


class TestMonitoring:
    """Test monitoring functionality."""
    
    def test_metrics_collector_counter(self):
        """Test metrics counter."""
        collector = MetricsCollector()
        
        collector.increment_counter("test_counter", 1.0)
        collector.increment_counter("test_counter", 2.0)
        
        metrics = collector.get_metrics()
        assert metrics['counters']['test_counter'] == 3.0
    
    def test_metrics_collector_gauge(self):
        """Test metrics gauge."""
        collector = MetricsCollector()
        
        collector.set_gauge("test_gauge", 42.0)
        collector.set_gauge("test_gauge", 100.0)
        
        metrics = collector.get_metrics()
        assert metrics['gauges']['test_gauge'] == 100.0
    
    def test_metrics_collector_timer(self):
        """Test metrics timer."""
        collector = MetricsCollector()
        
        collector.record_timer("test_timer", 0.5)
        collector.record_timer("test_timer", 1.0)
        
        metrics = collector.get_metrics()
        timer_stats = metrics['timers']['test_timer']
        assert timer_stats['count'] == 2
        assert timer_stats['min'] == 0.5
        assert timer_stats['max'] == 1.0
        assert timer_stats['avg'] == 0.75
    
    def test_timer_context_manager(self):
        """Test timer context manager."""
        collector = MetricsCollector()
        
        with Timer(collector, "test_operation"):
            time.sleep(0.01)
        
        metrics = collector.get_metrics()
        timer_stats = metrics['timers']['test_operation']
        assert timer_stats['count'] == 1
        assert timer_stats['avg'] > 0.01
    
    def test_tracer_span(self):
        """Test distributed tracing."""
        tracer = Tracer()
        
        span = tracer.start_span("test_operation")
        span.set_tag("test_tag", "test_value")
        span.log("Test log message")
        time.sleep(0.01)
        span.finish()
        
        spans = tracer.get_spans()
        assert len(spans) > 0
        
        span_dict = spans[-1]
        assert span_dict['name'] == "test_operation"
        assert span_dict['tags']['test_tag'] == "test_value"
        assert span_dict['duration'] > 0.01


class TestEnhancedStringTheory:
    """Test enhanced string theory features."""
    
    def test_device_detection(self):
        """Test device detection."""
        device = get_optimal_device()
        assert device in ['cpu', 'cuda', 'mps']
        
        info = get_device_info()
        assert 'optimal_device' in info
        assert 'cpu_available' in info
        assert info['cpu_available'] is True
    
    def test_string_theory_nn_layers(self):
        """Test StringTheoryNN with different layer counts."""
        # Single layer
        model1 = StringTheoryNN(dimensions=10, num_layers=1)
        assert model1.num_layers == 1
        
        # Multiple layers
        model3 = StringTheoryNN(dimensions=10, num_layers=3)
        assert model3.num_layers == 3
        
        # Max layers
        model10 = StringTheoryNN(dimensions=10, num_layers=10)
        assert model10.num_layers == 10
        
        # Clamp to max
        model_over = StringTheoryNN(dimensions=10, num_layers=15)
        assert model_over.num_layers == 10
    
    def test_string_theory_nn_forward(self):
        """Test StringTheoryNN forward pass."""
        model = StringTheoryNN(dimensions=10, num_layers=2, device='cpu')
        
        # Create input tensor
        x = torch.randn(5, 10)  # batch of 5
        
        # Forward pass
        output = model(x)
        
        assert output.shape == (5, 1)
        assert not torch.isnan(output).any()
    
    def test_string_theory_nn_batch_norm(self):
        """Test StringTheoryNN with batch normalization."""
        model = StringTheoryNN(
            dimensions=10,
            num_layers=3,
            use_batch_norm=True,
            device='cpu'
        )
        
        assert model.use_batch_norm is True
        
        # Forward pass
        x = torch.randn(8, 10)  # batch of 8
        output = model(x)
        
        assert output.shape == (8, 1)
    
    def test_string_theory_nn_device_info(self):
        """Test getting device info from model."""
        model = StringTheoryNN(dimensions=10, device='cpu')
        
        info = model.get_device_info()
        assert info['device'] == 'cpu'
        assert 'cuda_available' in info
        assert 'num_layers' in info


class TestIntegration:
    """Integration tests for enhanced features."""
    
    def test_mcp_server_with_cache(self):
        """Test MCP server with caching enabled."""
        from dredge.mcp_server import QuasimotoMCPServer
        
        server = QuasimotoMCPServer(use_cache=True, enable_metrics=True)
        
        # First call - cache miss
        result1 = server.string_spectrum({
            "max_modes": 10,
            "dimensions": 10
        })
        assert result1['success']
        assert result1.get('cached', False) is False
        
        # Second call - cache hit
        result2 = server.string_spectrum({
            "max_modes": 10,
            "dimensions": 10
        })
        assert result2['success']
        assert result2.get('cached', False) is True
    
    def test_mcp_server_metrics(self):
        """Test MCP server metrics collection."""
        from dredge.mcp_server import QuasimotoMCPServer
        
        server = QuasimotoMCPServer(use_cache=False, enable_metrics=True)
        
        # Perform operations
        server.list_capabilities()
        server.string_spectrum({"max_modes": 5, "dimensions": 10})
        
        # Get metrics
        metrics_result = server.get_metrics()
        assert metrics_result['success']
        assert 'metrics' in metrics_result
        
        # Check cache stats
        cache_result = server.get_cache_stats()
        assert cache_result['success'] is False  # Cache disabled
    
    def test_mcp_server_cache_stats(self):
        """Test MCP server cache statistics."""
        from dredge.mcp_server import QuasimotoMCPServer
        
        server = QuasimotoMCPServer(use_cache=True, enable_metrics=False)
        
        # Perform cached operation
        server.string_spectrum({"max_modes": 5, "dimensions": 10})
        
        # Get cache stats
        result = server.get_cache_stats()
        assert result['success']
        assert 'cache_stats' in result
