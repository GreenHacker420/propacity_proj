# Deployment Guide for Product Review Analyzer

This guide will help you deploy the Product Review Analyzer application on your server at greenhacker.studio and make it accessible via both the domain name (greenhacker.studio) and IP address (13.62.6.5).

## Prerequisites

- Access to your server (SSH)
- Python 3.11 installed
- Node.js and npm installed
- MongoDB Atlas account with a connection string

## Step 1: Clone the Repository

```bash
# Connect to your server
ssh your_username@greenhacker.studio

# Navigate to the directory where you want to install the application
cd /path/to/installation/directory

# Clone the repository (if not already done)
git clone https://github.com/your-username/propacity.git
cd propacity
```

## Step 2: Set Up the Backend

```bash
# Create a Python virtual environment
python3.11 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Install production dependencies
pip install gunicorn uvloop httptools

# Download NLTK resources
python -c "import nltk; nltk.download('punkt'); nltk.download('vader_lexicon')"
```

## Step 3: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Create .env file
cat > .env << EOL
MONGODB_URI=your_mongodb_atlas_connection_string
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key_for_jwt
DEVELOPMENT_MODE=false
EOL
```

## Step 4: Build the Frontend

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Build the frontend
npm run build

# Return to the project root
cd ..
```

## Step 5: Configure Nginx

```bash
# Create Nginx configuration file
sudo nano /etc/nginx/sites-available/product-review-analyzer
```

Copy the content from the `nginx_config.conf` file provided and paste it into the editor. Make sure to update the paths to match your actual installation directory.

```bash
# Create a symbolic link to enable the site
sudo ln -s /etc/nginx/sites-available/product-review-analyzer /etc/nginx/sites-enabled/

# Remove the default site if it's enabled
sudo rm -f /etc/nginx/sites-enabled/default

# Test the Nginx configuration
sudo nginx -t

# If the test is successful, restart Nginx
sudo systemctl restart nginx
```

## Step 6: Set Up Systemd Service

```bash
# Create a systemd service file
sudo nano /etc/systemd/system/product-review-analyzer.service
```

Copy the content from the `product-review-analyzer.service` file provided and paste it into the editor. Make sure to update the paths and username to match your actual installation.

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable product-review-analyzer

# Start the service
sudo systemctl start product-review-analyzer

# Check the status of the service
sudo systemctl status product-review-analyzer
```

## Step 7: Verify the Deployment

Open your browser and navigate to either:
- http://greenhacker.studio
- http://13.62.6.5

Both should display your Product Review Analyzer application.

## Troubleshooting

### Check Nginx Logs

```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Check Application Logs

```bash
sudo journalctl -u product-review-analyzer -f
```

### Restart Services

```bash
sudo systemctl restart nginx
sudo systemctl restart product-review-analyzer
```

### Check Firewall Settings

Make sure port 80 is open:

```bash
sudo ufw status
sudo ufw allow 80/tcp
```

## Updating the Application

To update the application:

```bash
# Navigate to your project directory
cd /path/to/your/propacity

# Pull the latest changes
git pull

# Activate the virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r backend/requirements.txt

# Build the frontend
cd frontend
npm install
npm run build
cd ..

# Restart the service
sudo systemctl restart product-review-analyzer
```
