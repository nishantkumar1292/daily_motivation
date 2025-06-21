#!/bin/bash

set -e

echo "🚀 Setting up Daily Motivation Development Environment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update

# Install FFmpeg and other system dependencies
echo "🎬 Installing FFmpeg and media tools..."
sudo apt-get install -y \
    ffmpeg \
    git \
    curl \
    wget \
    vim \
    htop \
    tree

# Install Python dependencies
echo "🐍 Installing Python packages..."
pip install --upgrade pip setuptools wheel

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "📋 Installing from requirements.txt..."
    pip install -r requirements.txt
else
    echo "⚠️  No requirements.txt found, installing essential packages..."
    pip install \
        yt-dlp==2025.5.22 \
        tweepy==4.15.0 \
        python-dotenv==1.1.0 \
        openai-whisper==20240930 \
        openai \
        fuzzywuzzy==0.18.0 \
        PyYAML==6.0.2
fi

# Install additional development tools
echo "🛠️ Installing development tools..."
pip install \
    black \
    flake8 \
    jupyter \
    ipython

# Verify GPU access
echo "🎮 Checking GPU availability..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi
    echo "✅ GPU detected and available!"
else
    echo "⚠️  GPU not detected. Some features may run slower."
fi

# Test Whisper installation
echo "🎤 Testing Whisper installation..."
python -c "import whisper; print('✅ Whisper installed successfully')" || echo "❌ Whisper installation failed"

# Test other key imports
echo "🧪 Testing key dependencies..."
python -c "
try:
    import yt_dlp
    import openai
    import tweepy
    print('✅ All key dependencies imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
"

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p videos
mkdir -p extracted_snippets
mkdir -p test_videos

# Set up git (if not already configured)
echo "🔧 Setting up Git configuration..."
if [ -z "$(git config --global user.name)" ]; then
    echo "⚠️  Git user.name not set. You may want to configure it:"
    echo "   git config --global user.name 'Your Name'"
fi

if [ -z "$(git config --global user.email)" ]; then
    echo "⚠️  Git user.email not set. You may want to configure it:"
    echo "   git config --global user.email 'your.email@example.com'"
fi

# Create a sample .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating sample .env file..."
    cat > .env << EOF
# Add your API keys here
OPENAI_API_KEY=your_openai_api_key_here
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
TWITTER_COMMUNITY_ID=your_community_id_here
EOF
    echo "📝 Sample .env file created - please update with your actual API keys"
fi

echo "🎉 Setup complete! Your development environment is ready."
echo ""
echo "📋 Next steps:"
echo "   1. Update .env file with your API keys"
echo "   2. Test with: python -c 'import whisper; print(\"Ready to go!\")'"
echo "   3. Run your script: python post_long_form_video.py"
echo ""
echo "🔍 Useful commands:"
echo "   - Check GPU: nvidia-smi"
echo "   - Test Whisper: python -c 'import whisper; m=whisper.load_model(\"tiny\"); print(\"Whisper works!\")'"
echo "   - View logs: tail -f *.log"
