"""
Dev utility: creates a throwaway user/project/render_job, enqueues the
real Celery render task, and prints DB status once a second until it
finishes. Lets you watch the job queue work end to end without needing
a real project/render API yet.

Run from the backend/ folder with the venv active:
    python scripts\\test_render_job.py

Requires: docker containers running (docker compose up -d) and a
Celery worker running in another window:
    celery -A app.celery_app worker --pool=solo --loglevel=info
"""
import sys
import time
import uuid

sys.path.insert(0, ".")

from app.db.session import SessionLocal
from app.models.project import Project, ProjectStatus, SourcePlatform
from app.models.render_job import RenderJob
from app.models.user import User
from app.tasks.render import run_render_job

db = SessionLocal()

email = f"test_render_{uuid.uuid4().hex[:8]}@example.com"
user = User(email=email, hashed_password="not_a_real_hash")
db.add(user)
db.flush()

project = Project(
    user_id=user.id,
    title="Manual Test Project",
    source_url="https://instagram.com/reel/manualtest",
    source_platform=SourcePlatform.instagram,
    status=ProjectStatus.rendering,
)
db.add(project)
db.flush()

job = RenderJob(project_id=project.id)
db.add(job)
db.commit()
db.refresh(job)

job_id = job.id
user_id = user.id

async_result = run_render_job.delay(str(job_id))
print(f"Enqueued render_job={job_id} celery_task={async_result.id}")
print("Watching status (updates every second)...\n")

for _ in range(30):
    db.expire_all()
    row = db.get(RenderJob, job_id)
    print(f"  status={row.status.value:<10} progress={row.progress_percent:>3}%")
    if row.status.value in ("completed", "failed"):
        if row.status.value == "failed":
            print(f"  error: {row.error_message}")
        else:
            print(f"  output_s3_key: {row.output_s3_key}")
        break
    time.sleep(1)

db.close()

print(f"\nDone. To clean this test row up, run:")
print(f"  docker exec reelapp_postgres psql -U reelapp -d reelapp -c \"DELETE FROM users WHERE email = '{email}';\"")
