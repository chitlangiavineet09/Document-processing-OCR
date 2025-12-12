# Restart Celery Worker After Updating Prompts

## Important Note

After updating LLM prompts in the Settings module, you **must restart the Celery worker** for the changes to take effect.

## Why?

The Celery worker process maintains its own cache of settings. When you update a prompt in the Settings UI:
- The backend API clears its cache ✅
- But the Celery worker still has the old value cached ⚠️

## How to Restart

1. **Find the Celery worker terminal window**
   - This is the terminal where you ran: `celery -A app.workers.celery_app worker --loglevel=info`

2. **Stop the worker**
   - Press `Ctrl+C` in that terminal

3. **Restart the worker**
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info
   ```

4. **Verify the new prompt is being used**
   - Upload a new document
   - Check the Celery worker logs for:
     - `Prompt 'ocr_prompt' loaded from database (CUSTOM prompt, ...)`
     - `Prompt source: CUSTOM (from database settings - ...)`

## Alternative: Restart All Services

If you want to restart everything:
```bash
# Stop backend (Ctrl+C in backend terminal)
# Stop Celery worker (Ctrl+C in worker terminal)

# Then restart:
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Celery Worker
cd backend
celery -A app.workers.celery_app worker --loglevel=info
```

