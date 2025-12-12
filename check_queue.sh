#!/bin/bash
# Quick script to check Celery queue status

echo "=== Redis Queue Status ==="
echo ""
echo "1. Checking Celery queue length:"
redis-cli LLEN celery 2>/dev/null || redis-cli -h localhost -p 6379 LLEN celery

echo ""
echo "2. Recent Celery keys in Redis:"
redis-cli KEYS "*celery*" 2>/dev/null | head -5 || redis-cli -h localhost -p 6379 KEYS "*celery*" | head -5

echo ""
echo "3. To monitor queue in real-time, run:"
echo "   watch -n 1 'redis-cli LLEN celery'"
echo ""
echo "4. To see all queues, run:"
echo "   redis-cli KEYS '*celery*'"

