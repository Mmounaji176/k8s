#!/bin/bash

echo "🔧 Face Recognition Stream Fix Commands"
echo "======================================="

# Set pod names from the debugging output
DJANGO_POD="django-backend-gpu0-f7ddbbbfd-h8ng6"
MEDIAMTX_POD="mediamtx-normal-5f94d755f9-plvrv"

echo "📋 Step 1: Check Django backend logs for stream errors"
echo "kubectl logs $DJANGO_POD -n face-recognition-system --tail=100 | grep -E '(stream|ffmpeg|rtsp|error)'"
kubectl logs $DJANGO_POD -n face-recognition-system --tail=100 | grep -E "(stream|ffmpeg|rtsp|error)"

echo ""
echo "📋 Step 2: Check current Celery tasks"
kubectl exec $DJANGO_POD -n face-recognition-system -c django-backend -- celery -A Backend inspect active || echo "Celery inspect failed"

echo ""
echo "📋 Step 3: Check MediaMTX configuration"
kubectl exec $MEDIAMTX_POD -n face-recognition-system -- cat /mediamtx.yml | head -50

echo ""
echo "📋 Step 4: Test FFmpeg availability in Django pod"
kubectl exec $DJANGO_POD -n face-recognition-system -c django-backend -- which ffmpeg
kubectl exec $DJANGO_POD -n face-recognition-system -c django-backend -- ffmpeg -version | head -3

echo ""
echo "📋 Step 5: Test network connectivity Django -> MediaMTX"
kubectl exec $DJANGO_POD -n face-recognition-system -c django-backend -- ping -c 3 mediamtx-normal-service

echo ""
echo "📋 Step 6: Test RTSP connection manually"
echo "Testing simple RTSP connection..."
kubectl exec $DJANGO_POD -n face-recognition-system -c django-backend -- timeout 10s ffmpeg -f lavfi -i testsrc=duration=5:size=320x240:rate=1 -f rtsp -rtsp_transport tcp rtsp://mediamtx-normal-service:8554/live/test 2>&1 | head -20

echo ""
echo "📋 Step 7: Check if any stream tasks are stuck"
kubectl exec $DJANGO_POD -n face-recognition-system -c django-backend -- python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
import django
django.setup()
from Backend.celery import app
import redis
r = redis.from_url('redis://:admin@redis-primary-service:6379/0')
print('Redis keys:', r.keys('*celery*')[:10])
print('Active connections:', r.client_list())
" 2>/dev/null || echo "Redis check failed"

echo ""
echo "🎯 NEXT STEPS:"
echo "=============="
echo "1. If FFmpeg test fails -> FFmpeg/MediaMTX connectivity issue"
echo "2. If FFmpeg works but stream doesn't -> Check stream task parameters"
echo "3. If MediaMTX config shows issues -> Update MediaMTX configuration"
echo "4. Check if multiple stream tasks are running simultaneously"

echo ""
echo "🔧 Quick fixes to try:"
echo "====================="
echo "# Kill any stuck stream tasks:"
echo "kubectl exec $DJANGO_POD -n face-recognition-system -c django-backend -- pkill -f 'AiLine.predict.main'"
echo ""
echo "# Restart MediaMTX if needed:"
echo "kubectl delete pod $MEDIAMTX_POD -n face-recognition-system"
echo ""
echo "# Test MediaMTX directly:"
echo "kubectl port-forward -n face-recognition-system svc/mediamtx-normal-service 8554:8554 &"
echo "# Then open VLC and try: rtsp://localhost:8554/live/test"