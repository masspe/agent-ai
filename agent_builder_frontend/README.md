# Agent Builder Frontend v3 Pro

A modern Next.js React application for building, managing, and deploying AI agents with an intuitive interface.

## ✨ Features

- **Modern Stack**: Built with Next.js 14, React 18, and TypeScript
- **Agent Management**: Create, edit, and manage AI agents
- **Agent Wizard**: Step-by-step agent creation process
- **Agent Store**: Marketplace for sharing and discovering agents
- **Dashboard**: Overview and quick actions
- **User Management**: Authentication and profile management
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Real-time Updates**: Dynamic interface with instant feedback

## 🚀 Quick Start

### Prerequisites

- **Node.js 18+** (with npm)
- **Backend API** running (see `../Fast-CRUD/README.md`)

### Installation

```bash
# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local

# Start development server
npm run dev
```

The application will be available at: http://localhost:3000

## 🔧 Configuration

Create `.env.local` file with your backend API configuration:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
# Add other environment variables as needed
```

## 📁 Project Structure

```
agent_builder_frontend/
├── app/                    # App Router (Next.js 13+)
│   ├── agents/            # Agent management pages
│   │   ├── page.tsx       # Agent list
│   │   ├── new/           # Create new agent
│   │   ├── [id]/         # Agent details/edit
│   │   └── wizard/        # Step-by-step creation
│   ├── store/             # Agent marketplace
│   │   ├── page.tsx       # Store listing
│   │   ├── new/           # Publish agent
│   │   └── [id]/         # Store item details
│   ├── dashboard/         # Main dashboard
│   ├── login/             # Authentication
│   ├── me/                # User profile
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page (redirects)
├── components/            # Reusable components
│   └── Nav.tsx           # Navigation component
├── lib/                   # Utilities and helpers
├── styles/                # Global styles
│   └── globals.css        # Tailwind CSS imports
├── middleware.ts          # Next.js middleware
├── next.config.js         # Next.js configuration
├── tailwind.config.js     # Tailwind CSS configuration
├── tsconfig.json          # TypeScript configuration
└── package.json           # Dependencies and scripts
```

## 🖥️ Available Pages

### Dashboard (`/dashboard`)
- Welcome screen with quick actions
- Navigation to main features
- Overview of user's agents and activity

### Agent Management (`/agents`)
- **List View** (`/agents`): Browse all agents
- **Create New** (`/agents/new`): Direct agent creation form  
- **Agent Details** (`/agents/[id]`): View and edit specific agent
- **Wizard** (`/agents/wizard`): Step-by-step agent creation process

### Agent Store (`/store`)
- **Store Listing** (`/store`): Browse public agents
- **Publish Agent** (`/store/new`): Make agent available in store
- **Store Details** (`/store/[id]`): View store item details

### User Management
- **Login** (`/login`): User authentication
- **Profile** (`/me`): User profile and settings

## 🎨 Styling & UI

- **Tailwind CSS**: Utility-first CSS framework
- **Responsive Design**: Mobile-first approach
- **Custom Components**: Reusable UI components
- **Modern Interface**: Clean, intuitive design

### Key CSS Classes Used

```css
.btn          /* Button styling */
.card         /* Card container */
.container    /* Main container with responsive padding */
```

## 🔌 API Integration

The frontend integrates with the FastAPI backend through REST API calls:

### Authentication
- Login via `/auth/token` endpoint
- JWT token stored and included in authenticated requests
- Protected routes require valid authentication

### Agent Operations
- **List Agents**: `GET /agents`
- **Create Agent**: `POST /agents`
- **Get Agent**: `GET /agents/{id}`
- **Update Agent**: `PUT /agents/{id}`
- **Delete Agent**: `DELETE /agents/{id}`

### Store Operations
- **List Store Items**: `GET /store` (or equivalent endpoint)
- **Publish Agent**: `POST /store`
- **Get Store Item**: `GET /store/{id}`

## 🛠️ Development

### Available Scripts

```bash
# Development server with hot reload
npm run dev

# Production build
npm run build

# Start production server
npm run start

# Type checking
npm run type-check

# Linting
npm run lint
```

### Development Features

- **Hot Reload**: Automatic browser refresh on code changes
- **TypeScript**: Full type safety and IntelliSense
- **ESLint**: Code quality and consistency
- **Fast Refresh**: Preserves component state during development

### Adding New Pages

1. Create new file in `app/` directory following Next.js App Router conventions
2. Use TypeScript for type safety
3. Follow existing patterns for API integration
4. Add navigation links in `components/Nav.tsx` if needed

### Adding New Components

1. Create component in `components/` directory
2. Use TypeScript with proper prop types
3. Follow React best practices and hooks
4. Style with Tailwind CSS classes

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

This creates an optimized production build in the `.next` directory.

### Deployment Options

#### Vercel (Recommended)
```bash
npm install -g vercel
vercel
```

#### Static Export
```bash
npm run build
npm run export
```

#### Docker
Create `Dockerfile`:
```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables

For production, configure these environment variables:

```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
# Add other production-specific variables
```

## 🔒 Security Considerations

- **Environment Variables**: Use `NEXT_PUBLIC_` prefix only for client-side variables
- **API Keys**: Never expose sensitive keys in client-side code
- **Authentication**: JWT tokens handled securely
- **CORS**: Backend configured with appropriate CORS settings
- **Content Security Policy**: Configure CSP headers for production

## 📱 Browser Support

- **Modern Browsers**: Chrome, Firefox, Safari, Edge (latest versions)
- **Mobile Browsers**: iOS Safari, Chrome Mobile
- **JavaScript Required**: Application requires JavaScript enabled

## 🔍 Troubleshooting

### Common Issues

**Page not loading**
- Check backend is running at correct URL
- Verify `NEXT_PUBLIC_API_URL` in `.env.local`
- Check browser console for errors

**Authentication issues**
- Ensure backend `/auth/token` endpoint is accessible
- Check JWT token expiration
- Verify CORS configuration in backend

**Build errors**
- Check TypeScript types are correct
- Ensure all dependencies are installed
- Verify Next.js configuration

**API connection issues**
- Confirm backend is running and accessible
- Check network/firewall restrictions
- Verify API endpoint URLs

### Development Tips

1. **Use Browser DevTools**: Inspect network requests and console logs
2. **TypeScript Errors**: Pay attention to type checking during development
3. **Hot Reload Issues**: Restart dev server if hot reload stops working
4. **Environment Variables**: Restart dev server after changing `.env.local`

## 🧪 Testing

### Manual Testing Checklist

- [ ] Login/logout functionality
- [ ] Agent creation and editing
- [ ] Agent wizard flow
- [ ] Store browsing and publishing
- [ ] Dashboard navigation
- [ ] Responsive design on mobile
- [ ] API error handling

### Test User Journey

1. **Login**: Access login page and authenticate
2. **Dashboard**: Navigate to main dashboard
3. **Create Agent**: Use wizard or direct creation
4. **Manage Agents**: Edit, view, delete agents
5. **Store**: Browse and publish agents
6. **Profile**: View and update user profile

## 🤝 Contributing

1. Follow existing code patterns and TypeScript conventions
2. Use Tailwind CSS for styling
3. Test on multiple browser sizes
4. Ensure proper error handling
5. Update documentation for new features

## 📚 Learn More

- **Next.js Documentation**: https://nextjs.org/docs
- **React Documentation**: https://react.dev
- **TypeScript**: https://www.typescriptlang.org/docs
- **Tailwind CSS**: https://tailwindcss.com/docs

---

For backend API documentation, see `../Fast-CRUD/README.md`.
