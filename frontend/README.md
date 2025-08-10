# AI Study Architect Frontend

React + TypeScript frontend for the AI Study Architect - an educational platform that uses Socratic questioning to build deep understanding.

## Prerequisites

- Node.js 18+ and npm
- Backend API running on http://localhost:8000
- For production: Backend deployed to Render or similar

## Setup

1. Install dependencies:
```bash
npm install
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:5173

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run test` - Run tests
- `npm run lint` - Run ESLint
- `npm run typecheck` - Run TypeScript type checking

## Authentication Flow

1. User registers at `/register`
2. After registration, automatically logs in
3. Access token stored in localStorage
4. Refresh token used to get new access tokens
5. Protected routes redirect to login if not authenticated

## Project Structure

```
src/
├── components/     # Reusable UI components
│   └── auth/      # Authentication components
├── contexts/      # React contexts (AuthContext)
├── services/      # API services
├── hooks/         # Custom React hooks
├── types/         # TypeScript type definitions
├── utils/         # Utility functions
└── App.tsx        # Main application component
```

## Testing the Authentication

1. Start the backend API:
```bash
cd ../backend
uvicorn app.main:app --reload
```

2. Start the frontend:
```bash
npm run dev
```

3. Navigate to http://localhost:5173
4. Try to access any page - you'll be redirected to login
5. Click "Sign up" to create a new account
6. After registration, you'll be logged in automatically
7. The user menu in the top right shows your username
8. Click logout to sign out

## Deployment

### Vercel (Recommended)
```bash
# Build for production
npm run build

# Deploy to Vercel
npx vercel

# Or connect GitHub repo on vercel.com for auto-deploy
```

### Environment Variables for Production
```env
VITE_API_URL=https://ai-study-architect.onrender.com
```

## Features Implemented

- ✅ Login page with form validation
- ✅ Registration page with password requirements
- ✅ Protected routes that require authentication
- ✅ Automatic token refresh
- ✅ User menu with logout
- ✅ Responsive design with Material-UI
- ✅ Form validation with react-hook-form
- ✅ API integration with axios
- ✅ CSRF token support