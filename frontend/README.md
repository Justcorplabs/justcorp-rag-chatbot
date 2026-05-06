# Frontend — JustCorp Labs AI Knowledge Base Chatbot

React frontend for the JustCorp Labs AI Knowledge Base Chatbot.

## Purpose

This frontend provides a clean, professional interface for uploading business documents, asking questions, and viewing AI-generated answers with sources.

It is designed to present the project as a polished JustCorp Labs portfolio product.

## Features

- Professional landing section
- JustCorp Labs branding
- API online/offline status
- PDF upload interface
- Uploaded documents list
- Delete document option
- Example questions
- Chat interface
- Answer display
- Source/context panel
- Responsive design
- Business-focused UI style

## Tech Stack

- React
- Vite
- JavaScript
- CSS
- lucide-react icons

## Folder Structure

```text
frontend/
│
├── public/
│   └── justcorp-logo.jpg
│
├── src/
│   ├── components/
│   │   ├── Header.jsx
│   │   ├── UploadPanel.jsx
│   │   ├── DocumentList.jsx
│   │   ├── ExampleQuestions.jsx
│   │   ├── ChatPanel.jsx
│   │   └── SourcePanel.jsx
│   │
│   ├── App.jsx
│   ├── api.js
│   ├── main.jsx
│   └── styles.css
│
├── package.json
├── .env.example
└── README.md
```

## Setup

Install dependencies:

```powershell
npm install
```

## Environment Variables

Create `.env` from `.env.example`:

```powershell
Copy-Item .env.example .env
```

Frontend `.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

This points the React app to the FastAPI backend.

## Run Frontend

```powershell
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

## Build for Production

```powershell
npm run build
```

The production build will be created inside:

```text
dist/
```

## Deployment

Recommended frontend deployment platforms:

- Netlify
- Vercel

For Netlify:

- Base directory: `frontend`
- Build command: `npm run build`
- Publish directory: `dist`

Environment variable:

```env
VITE_API_BASE_URL=https://your-backend-url.onrender.com
```

## Notes

The frontend requires the backend to be running for full functionality.

If the status badge says **API Offline**, check that the backend is running at:

```text
http://127.0.0.1:8000
```