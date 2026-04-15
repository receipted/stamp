FROM python:3.13-slim

# Install git for repo cloning
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir pydantic

# Copy source
COPY src/ src/
COPY serve.py .
COPY substrate_cli.py .

# Expose port
ENV SUBSTRATE_PORT=8080
EXPOSE 8080

CMD ["python", "serve.py"]
