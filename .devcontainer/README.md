# Daily Motivation Devcontainer

This devcontainer provides a complete GPU-enabled development environment for the Daily Motivation project.

## What's Included

- **Python 3.11** with CUDA support
- **NVIDIA GPU** access with CUDA 12.2
- **FFmpeg** for video processing
- **All project dependencies** from requirements.txt
- **VS Code extensions** for Python development
- **Development tools** (black, flake8, jupyter)

## Quick Start

1. **Push your code to GitHub** (if not already done)
2. **Open your repository on GitHub**
3. **Click "Code" → "Codespaces" → "Create codespace on main"**
4. **Wait 3-5 minutes** for the environment to set up
5. **Update `.env` file** with your API keys
6. **Run your script**: `python post_long_form_video.py`

## Environment Features

### GPU Support
- Automatic NVIDIA GPU detection
- CUDA 12.2 with cuDNN 8
- GPU memory optimization for Whisper

### Pre-installed Tools
- **yt-dlp**: YouTube video downloading
- **OpenAI Whisper**: Audio transcription
- **FFmpeg**: Video/audio processing
- **OpenAI API**: GPT integration
- **Tweepy**: Twitter API client

### VS Code Extensions
- Python language support
- Debugging tools
- Jupyter notebook support
- YAML/JSON editing
- GitHub Copilot (if you have access)

## Configuration

### Environment Variables
The setup script creates a `.env` template. Update it with your actual keys:

```env
OPENAI_API_KEY=your_actual_key_here
TWITTER_API_KEY=your_actual_key_here
# ... etc
```

### GPU Settings
- Default CUDA device: GPU 0
- Automatic GPU detection
- Optimized for Whisper models

## Useful Commands

```bash
# Check GPU status
nvidia-smi

# Test Whisper installation
python -c "import whisper; m=whisper.load_model('tiny'); print('Whisper works!')"

# Run your main script
python post_long_form_video.py

# Check system resources
htop

# View project structure
tree
```

## Troubleshooting

### GPU Not Detected
- Restart the Codespace
- Check GitHub Codespaces GPU availability in your region

### Slow Performance
- Use smaller Whisper models (`tiny` or `base`) for development
- Check GPU memory usage with `nvidia-smi`

### Package Installation Issues
- Run `pip install -r requirements.txt` manually
- Check the setup log for any errors

## Development Workflow

1. **Edit code** in VS Code (just like local)
2. **Test quickly** with small videos first
3. **Use GPU efficiently** - don't leave long processes running
4. **Save work frequently** - Codespaces can timeout
5. **Check GPU usage** with `nvidia-smi` periodically

## Storage

- **Persistent**: Your code and `.env` file
- **Cached**: Python packages and models (faster restart)
- **Temporary**: Downloaded videos (clean up large files)

Enjoy your GPU-powered development environment! 🚀
