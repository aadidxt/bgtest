# 🪄 Background Remover App

A simple yet powerful web app for AI-powered image background removal with a modern, responsive UI.

## ✨ Features
- Clean, modern interface that fits on one screen
- Enter API key directly in the app (no pre-configuration needed)
- Image preview - see your image immediately after selection
- AI-powered background removal (rembg U²-Net)
- One-click processing with instant result display
- Download processed images as PNG with transparent background
- Fully responsive design - works on all devices
- No scrolling required - everything visible at once

## 📂 Project Structure
```
bg/
├── run.py                  # Flask server entry point
├── app.html               # Main web interface (single page)
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── README.md             # This file
└── app/
    ├── __init__.py       # Flask app initialization
    ├── auth.py           # API key validation
    ├── routes.py         # API endpoints
    └── services/
        └── bg_remove.py  # Background removal logic
```

## 🚀 Quick Start

### Local Setup
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API key (in .env file):**
   ```
   API_KEYS=your-api-key-here
   ```

3. **Run the app:**
   ```bash
   python run.py
   ```

4. **Open in browser:**
   - Visit: `http://localhost:5000/`

### Docker Setup
```bash
docker build -t bg-remover .
docker run -p 5000:5000 bg-remover
```

Then open `http://localhost:5000/`

## 💡 How to Use

1. **Load the app** - Open http://localhost:5000/ (no API key required yet)
2. **Enter API Key** - Paste your API key in the input field and click "Save API Key"
3. **Select Image** - Click the file input to choose an image (JPG/PNG)
4. **Preview** - Selected image displays instantly in the preview box
5. **Remove Background** - Click the "Remove Background" button to process
6. **Download** - Once processed, click "Download" to save the transparent PNG

## 📋 Requirements
- Python 3.8+
- Flask 3.0
- rembg 2.0 (AI model downloads ~170MB on first run)
- python-dotenv 1.0

See `requirements.txt` for full dependencies.

## ⚙️ Configuration

### API Keys
Set API keys in `.env` file:
```
API_KEYS=key1,key2,key3
```

### Environment Variables
- `API_KEYS` - Comma-separated valid API keys

## 🔧 API Endpoints

### POST `/api/v1/remove-bg`
Removes background from uploaded image.

**Headers:**
- `x-api-key`: Your API key

**Body:**
- `image`: Image file (multipart form data)

**Response:**
- PNG image with transparent background

## 🎨 UI Features
- **Gradient background** - Modern purple gradient design
- **Responsive layout** - Adapts to all screen sizes
- **Image scaling** - Images maintain aspect ratio in preview boxes
- **Status updates** - Real-time feedback on API key and processing status
- **Download button** - Easy download of processed images

## ⚠️ Important Notes
- First run downloads the AI model (~170MB) - this may take a few minutes
- The app requires a valid API key to process images
- API key is stored locally in your browser
- Images are processed immediately without caching

## 📦 Deployment

The app is Docker-ready. Use the provided `Dockerfile` for containerization and deployment to any hosting platform (AWS, Heroku, Railway, etc.).

## 🎯 Perfect For
- Web developers wanting to add AI image processing
- Learning about full-stack web applications
- Integrating background removal into workflows
- Understanding API authentication and file uploads

## 💬 Notes
- No database required - stateless API
- CPU-only processing (can be changed to GPU)
- API key validation on each request ensures security
- Clean, maintainable codebase for easy customization
