from celery import Celery
from app.core.config import settings
import logging
from urllib.parse import urlparse

# Configure logging for Celery worker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Output to console
    ]
)

logger = logging.getLogger(__name__)

# Configure broker and backend URLs with SSL support for Upstash
broker_url = settings.CELERY_BROKER_URL
result_backend = settings.CELERY_RESULT_BACKEND

# SSL configuration for Upstash Redis (rediss://)
broker_transport_options = {}
result_backend_transport_options = {}

if broker_url.startswith('rediss://'):
    # Parse Redis URL for SSL configuration
    parsed = urlparse(broker_url)
    # Remove query parameters from URL - Kombu will use transport_options for SSL config
    clean_broker_url = f"rediss://{parsed.netloc}{parsed.path}" if parsed.path else f"rediss://{parsed.netloc}"
    broker_url = clean_broker_url
    # Configure SSL for Kombu - use 'none' as string for ssl_cert_reqs (Kombu accepts this)
    broker_transport_options = {
        'ssl_cert_reqs': 'none',  # Disable SSL certificate verification for Upstash
    }
    logger.info("Configured Celery broker with SSL for Upstash Redis")

if result_backend.startswith('rediss://'):
    # Parse Redis URL for SSL configuration
    parsed = urlparse(result_backend)
    # Remove query parameters from URL
    clean_result_backend = f"rediss://{parsed.netloc}{parsed.path}" if parsed.path else f"rediss://{parsed.netloc}"
    result_backend = clean_result_backend
    result_backend_transport_options = {
        'ssl_cert_reqs': 'none',  # Disable SSL certificate verification for Upstash
    }
    logger.info("Configured Celery result backend with SSL for Upstash Redis")

# Create Celery app instance
celery_app = Celery(
    "bill_processor",
    broker=broker_url,
    backend=result_backend,
    include=["app.workers.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    # SSL transport options for Upstash Redis
    broker_transport_options=broker_transport_options,
    result_backend_transport_options=result_backend_transport_options,
    # Configure worker logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

logger.info("Celery app configured successfully")
logger.info(f"Broker URL: {broker_url[:30]}...")
logger.info(f"Result backend: {result_backend[:30]}...")
# #region agent log
logger.info(f"[DEBUG-HYP-A] Worker startup - Full broker_url: {broker_url}")
logger.info(f"[DEBUG-HYP-A] Worker startup - Full result_backend: {result_backend}")
logger.info(f"[DEBUG-HYP-A] Worker startup - broker_transport_options: {broker_transport_options}")
logger.info(f"[DEBUG-HYP-E] After URL cleanup - broker_url: {broker_url}")
# #endregion

