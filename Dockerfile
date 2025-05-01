# --- Base Image for Backend ---
FROM python:3.11-slim AS backend

WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev git && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend .

# --- Base Image for Frontend ---
FROM node:20-alpine AS frontend
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install --frozen-lockfile || npm install

COPY frontend .
RUN npm run build

# --- Final Image ---
FROM python:3.11-slim as final
WORKDIR /app

# Copy backend from backend image
COPY --from=backend /app/backend ./backend

# Copy frontend build from frontend image
COPY --from=frontend /app/frontend/.next ./frontend/.next
COPY --from=frontend /app/frontend/public ./frontend/public
COPY --from=frontend /app/frontend/package.json ./frontend/package.json
COPY --from=frontend /app/frontend/node_modules ./frontend/node_modules

# Expose ports
EXPOSE 8000 3000

# Start both backend (FastAPI) and frontend (Next.js) using a process manager
RUN pip install --no-cache-dir uvicorn
RUN pip install --no-cache-dir supervisor

COPY supervisord.conf ./supervisord.conf

CMD ["supervisord", "-c", "./supervisord.conf"]
