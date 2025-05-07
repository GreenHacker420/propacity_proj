FROM python:3.11.12

# Set working directory
WORKDIR /app

# Install Node.js
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy NLTK download script and run it
COPY backend/download_nltk_resources.py backend/
RUN python backend/download_nltk_resources.py

# Copy package.json and install Node.js dependencies
COPY frontend/package.json frontend/package-lock.json frontend/
RUN cd frontend && npm install

# Copy the rest of the application
COPY . .

# Build the frontend
RUN cd frontend && \
    # Ensure the build directory exists
    mkdir -p dist && \
    # Try to build, but continue even if it fails
    npm run build || echo "Frontend build failed, but continuing with deployment"

# Expose the port
EXPOSE 8000

# Make start.sh executable
RUN chmod +x start.sh

# Start the application
CMD ["./start.sh"]
