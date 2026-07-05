# CommunityPulse — AI Decision Intelligence Platform

## Deployment Guide

### Frontend (Vercel)
- Deployed at: `https://your-vercel-domain.vercel.app`
- Source: `/frontend/index.html`

### Backend (Render / Railway / Google Cloud Run)
- Deploy the `/backend` folder as a Python FastAPI app
- Set environment: `PORT=8000`
- Build command: `pip install -r requirements.txt`
- Start command: `python -m uvicorn main:app --host 0.0.0.0 --port 8000`

### Update Frontend API URL
After deploying backend, update the API URL in `/frontend/index.html`:
```javascript
const API = "https://your-backend-domain.com";  // Change from localhost:8000
```

Then redeploy frontend to Vercel.
