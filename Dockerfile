FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:$PATH"

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    # OCR tools
    tesseract-ocr \
    libtesseract-dev \
    # PDF processing tools
    poppler-utils \
    # File identification
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

RUN python manage.py collectstatic --no-input

EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", \
     "--bind", "[::]:8000", \
     "--workers", "4", \
     "--timeout", "120"]