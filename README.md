# Agent AI - Intelligent Agent Builder Platform

A full-stack application for building, managing, and deploying AI agents with an intuitive interface and powerful backend.

## 🏗️ Architecture

This project consists of two main components:

- **Backend** (`Fast-CRUD/`): FastAPI-based Python backend with automatic CRUD generation
- **Frontend** (`agent_builder_frontend/`): Next.js React application with TypeScript

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** for backend
- **Node.js 18+** for frontend  
- **MariaDB/MySQL** database
- **Git** for version control

### 1. Clone the Repository

```bash
git clone https://github.com/masspe/agent-ai.git
cd agent-ai
```

### 2. Backend Setup

```bash
cd Fast-CRUD

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and settings

# Start the server
python -m uvicorn app.main:app --reload
```

Backend will be available at: http://localhost:8000

### 3. Frontend Setup

```bash
cd agent_builder_frontend

# Install dependencies
npm install

# Configure environment  
cp .env.local.example .env.local
# Edit .env.local with your backend URL

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:3000

## 📁 Project Structure

```
agent-ai/
├── Fast-CRUD/                 # FastAPI Backend
│   ├── app/
│   │   ├── models/           # Database models
│   │   ├── routers/          # API routes
│   │   ├── security/         # Authentication & security
│   │   └── main.py           # FastAPI application
│   ├── requirements.txt      # Python dependencies
│   └── README.md             # Backend documentation
│
├── agent_builder_frontend/    # Next.js Frontend
│   ├── app/                  # App directory (Next.js 13+)
│   │   ├── agents/          # Agent management pages
│   │   ├── store/           # Agent store pages  
│   │   └── dashboard/       # Dashboard page
│   ├── components/          # Reusable React components
│   ├── package.json         # Node.js dependencies
│   └── README.md            # Frontend documentation
│
└── README.md                # Main project documentation
```

## ✨ Features

### Backend Features
- **Auto-CRUD Generation**: Automatically creates REST APIs for all database tables
- **JWT Authentication**: Secure token-based authentication with Argon2 password hashing
- **Multi-Database Support**: Works with MariaDB and MySQL databases
- **Interactive Documentation**: Built-in Swagger UI for API exploration
- **Flexible Security**: Configurable access controls per table/endpoint
- **Composite Primary Keys**: Full support for complex database schemas

### Frontend Features
- **Modern React**: Built with Next.js 14 and TypeScript
- **Agent Management**: Create, edit, and manage AI agents
- **Agent Wizard**: Step-by-step agent creation process
- **Agent Store**: Marketplace for sharing and discovering agents
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Dynamic interface with instant feedback

## 🔐 Authentication

The system uses JWT (JSON Web Tokens) for authentication:

1. **Create Admin User**: `POST /auth/seed_admin`
2. **Login**: `POST /auth/token` 
3. **Access Protected Routes**: Include `Authorization: Bearer <token>` header

Default admin credentials (after seeding):
- Email: `admin@example.com`
- Password: `admin123`

## 📖 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🛠️ Development

### Backend Development
- Uses FastAPI with automatic reloading
- SQLAlchemy with automap for dynamic model generation
- Argon2 for secure password hashing
- CORS configured for frontend integration

### Frontend Development  
- Next.js with App Router (v13+)
- TypeScript for type safety
- Tailwind CSS for styling
- Automatic code splitting and optimization

## 🚀 Deployment

### Backend Deployment
- Use a production ASGI server (e.g., Gunicorn with Uvicorn workers)
- Configure environment variables securely
- Set up SSL/TLS termination
- Use a proper database server (not SQLite)

### Frontend Deployment
- Build the production version: `npm run build`
- Deploy to Vercel, Netlify, or any static hosting
- Configure environment variables for production API endpoints

## 🔧 Configuration

### Backend Configuration (`.env`)
```env
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/agent_app
FRONTEND_ORIGIN=http://localhost:3000
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
```

### Frontend Configuration (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For detailed setup instructions and troubleshooting:
- **Backend**: See `Fast-CRUD/README.md`
- **Frontend**: See `agent_builder_frontend/README.md`
- **Issues**: Create an issue on GitHub

---

**Happy building! 🚀**