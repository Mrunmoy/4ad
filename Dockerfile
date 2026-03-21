# Stage 1: Build Phaser client
FROM node:20-alpine AS client-build
WORKDIR /app/client
COPY client/package*.json ./
RUN npm ci
COPY client/ ./
RUN npm run build

# Stage 2: Production
FROM python:3.10-slim
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY src/ ./src/
COPY run.py ./
COPY pytest.ini ./

# Copy built frontend from stage 1
COPY --from=client-build /app/client/dist ./client/dist

# Create data directory for SQLite campaign persistence
RUN mkdir -p /app/data

ENV FLASK_ENV=production
ENV PR_NOTIFY_DB=/app/data/campaign.db

EXPOSE 5000

CMD ["python", "run.py"]
