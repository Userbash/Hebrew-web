from ai_bridge.core.metrics import MetricsCollector


def test_metrics_snapshot_average_latency():
    metrics = MetricsCollector()
    metrics.increment("task.done")
    metrics.observe_latency("a1", 100)
    metrics.observe_latency("a1", 300)

    snapshot = metrics.snapshot()

    assert snapshot["counters"]["task.done"] == 1
    assert snapshot["avg_latency_ms"]["a1"] == 200
