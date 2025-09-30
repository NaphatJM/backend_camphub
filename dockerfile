FROM python:3.12-slim

# Set working directory
WORKDIR /usr/src/app

# Copy project files
COPY pyproject.toml .
COPY . .

# ติดตั้ง pip, Poetry และ dependencies
RUN pip install --upgrade pip \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
