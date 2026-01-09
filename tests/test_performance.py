"""Performance tests for DREDGE x Dolly server."""
import json
import time
import pytest
from dredge.server import create_app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app = create_app()
    return app.test_client()


def test_lift_endpoint_performance(client):
    """Test that the lift endpoint processes requests efficiently."""
    # Warm up
    payload = {'insight_text': 'Performance test insight.'}
    client.post('/lift', data=json.dumps(payload), content_type='application/json')
    
    # Measure time for multiple requests
    num_requests = 100
    start_time = time.time()
    
    for i in range(num_requests):
        payload = {'insight_text': f'Performance test insight {i}.'}
        response = client.post(
            '/lift',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert response.status_code == 200
    
    elapsed_time = time.time() - start_time
    avg_time_per_request = elapsed_time / num_requests
    
    # Assert reasonable performance (should be well under 10ms per request)
    # With the optimized hash function, this should be very fast
    assert avg_time_per_request < 0.01, f"Average request time too slow: {avg_time_per_request:.4f}s"
    
    print(f"\n✓ Processed {num_requests} requests in {elapsed_time:.3f}s")
    print(f"✓ Average time per request: {avg_time_per_request*1000:.2f}ms")


def test_hash_id_consistency(client):
    """Test that the same input produces the same ID consistently."""
    payload = {'insight_text': 'Consistent test input.'}
    
    # Make multiple requests with the same input
    ids = []
    for _ in range(5):
        response = client.post(
            '/lift',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = json.loads(response.data)
        ids.append(data['id'])
    
    # All IDs should be identical for the same input
    assert len(set(ids)) == 1, "Hash IDs should be consistent for the same input"


def test_hash_id_uniqueness(client):
    """Test that different inputs produce different IDs."""
    ids = set()
    
    for i in range(100):
        payload = {'insight_text': f'Unique test input {i}.'}
        response = client.post(
            '/lift',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = json.loads(response.data)
        ids.add(data['id'])
    
    # Should have 100 unique IDs (hash collisions are extremely unlikely)
    assert len(ids) >= 99, f"Expected ~100 unique IDs, got {len(ids)}"
