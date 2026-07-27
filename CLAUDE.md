# Project Overview

This is a full-stack SaaS application.

Always understand the existing code before making changes.
Prefer extending the current architecture over rewriting it.

---

# Tech Stack

Frontend:
- React
- TypeScript
- Vite

Backend:
- FastAPI
- Python

Database:
- PostgreSQL

Version Control:
- Git + GitHub

---

# Coding Standards

- Write clean, modular code.
- Follow existing naming conventions.
- Prefer reusable components and functions.
- Keep files focused on a single responsibility.
- Avoid unnecessary dependencies.

---

# Before Making Changes

Always:

1. Read related files first.
2. Explain the plan briefly.
3. Make the smallest change necessary.
4. Preserve existing functionality.
5. Update imports if needed.

---

# Debugging

When fixing bugs:

- Find the root cause.
- Don't apply temporary hacks.
- Run tests if available.
- Verify the fix doesn't break other features.

---

# Terminal Usage

You may:

- Run npm commands.
- Run pip commands.
- Start development servers.
- Run tests.
- Use Git for status, diff, commit, and branch operations.

Ask before running destructive commands such as deleting files, resetting Git history, or dropping databases.

---

# Git Workflow

Never commit directly to main.

Create feature branches when implementing major features.

Write clear commit messages.

---

# Database Rules

- Use PostgreSQL.
- Use proper foreign keys.
- Use cascade delete only when appropriate.
- Never delete production data without confirmation.

---

# Security

- Never expose secrets.
- Never commit .env files.
- Validate all user input.
- Follow authentication best practices.

---

# Communication Style

Be concise.

If there are multiple solutions:

- Recommend the best one.
- Briefly explain why.
- Mention trade-offs only if they matter.

When unsure, ask before making major architectural decisions.

---

# Goal

Help build a production-quality SaaS that is maintainable, secure, scalable, and well documented.

# IMPORTANT
If you feel token will be over next cmd then stop it right there and inform token are gonna be over.

The product: A user pastes an Instagram Reel or YouTube Shorts URL. The backend downloads it and analyzes its exact cut timings, beat sync, transitions, camera movements, text overlays, and color grading. It converts this into an Edit Blueprint. The user uploads their own photos and videos. The AI matches their assets to the right slots. Missing footage is filled with aesthetic animated text and motion graphics. The final rendered video mirrors the exact editing style of the reference using the user's own content.
Tech stack: FastAPI backend, PostgreSQL database, Celery and Redis for async jobs, AWS S3 for storage, yt-dlp for downloading, OpenCV and PySceneDetect for scene detection, librosa, Demucs, and Whisper for audio analysis, CLIP and face detection for asset matching, FFmpeg for rendering, Stripe for payments, Railway for hosting, React for frontend.
My laptop: HP Pavilion. Heavy AI processing goes to Google Colab or RunPod, not my laptop.
My budget: Minimal. Use free tiers wherever possible. Only spend on GPU compute for final demo renders.
Goal: Build a fully working backend, connect it to a React frontend I will describe via screenshots, and produce 2-3 polished working demos good enough to pitch to investors. This is not a public launch yet.
Rules for every session:
1. Always write complete working code. Never write placeholder or incomplete functions.
2. If a package is missing or an error occurs, fix it yourself using terminal commands.
3. Before starting any new phase, explain in plain English what you are about to build and why.
4. If you need a login or API key, ask for exactly one thing at a time with clear instructions on where to find it.
5. Never assume I understand technical terms. Explain anything non-obvious in simple words.
6. At the end of every session write a short summary of what was built and what is next.
