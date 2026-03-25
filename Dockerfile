FROM python:3.13-slim

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:$PATH"

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    tesseract-ocr \
    libtesseract-dev \
    clamav \
    clamav-daemon \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# install uv
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod +x /install.sh && /install.sh && rm /install.sh

WORKDIR /app

# install dependencies
COPY pyproject.toml uv.lock ./
RUN uv pip install --system .

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]