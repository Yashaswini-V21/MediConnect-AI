# 💻 MediConnect-AI: Frontend Web Application

This directory houses the modern, highly responsive React.js single-page application (SPA) frontend for the MediConnect-AI SaaS platform. It provides patients, hospital administrators, and emergency operators with a premium, sleek, and intuitive user interface.

---

## 🎨 Technology Stack & Architecture

* **Framework**: React.js (Create React App structure)
* **Styling**: TailwindCSS & Custom Premium CSS transitions
* **Icons**: Lucide React
* **Animations**: Framer Motion (for smooth micro-interactions)
* **API Connection**: Axios client with centralized interceptors for automatic JWT authentication injection.
* **State Management**: React Context (centralized `AuthContext` for user roles and authentication state).

---

## 📂 Project Structure

```
frontend/
├── public/                     # Static Web Assets (index.html, manifest.json)
└── src/
    ├── components/             # Modular Component Library
    │   ├── admin/              # Admin Portal components
    │   ├── auth/               # Signup, Login, and OTP components
    │   ├── common/             # Layouts, Navbar, Footer, Loaders
    │   └── profile/            # Refactored Profile widgets
    │       └── AppointmentsTab.jsx # Extracted appointments & rating modal
    │
    ├── context/                # Context Providers (AuthContext.js)
    ├── hooks/                  # Custom hooks (useAuth.js)
    ├── locales/                # Multi-lingual translations
    ├── pages/                  # 16 High-Fidelity UI Pages
    │   ├── Landing.jsx         # Beautiful SaaS entry page
    │   ├── Home.jsx            # User primary dashboard
    │   ├── Profile.jsx         # Highly clean user profile page
    │   ├── SymptomChecker.jsx  # Interactive AI diagnosis interface
    │   └── admin/              # Dedicated back-office dashboard
    │
    ├── services/               # API clients (api.js connecting to Flask)
    ├── styles/                 # Global styling config & theme tokens
    └── index.js                # App entrypoint
```

---

## 🚀 Setup & Launch Instructions

### Prerequisites
Ensure you have **Node.js (v18+)** and **npm** installed on your system.

### 1. Installation
Navigate into this folder and install the required modules:
```bash
npm install
```

### 2. Environment Configuration
Create a `.env` file based on `.env.example` in this directory:
```bash
copy .env.example .env
```
Fill in the environment variables:
* `REACT_APP_API_URL`: Points to your Flask backend server (e.g. `http://localhost:5000` for local dev).
* `REACT_APP_FIREBASE_*`: Copy your Web SDK Configuration parameters from your Firebase Project settings console.

### 3. Running in Development
Start the Webpack dev server:
```bash
npm start
```
The application will launch on [http://localhost:3000](http://localhost:3000) (or `http://localhost:3001` if port 3000 is occupied).

---

## 💎 Design and Aesthetics Best Practices
* **Harmonious Palettes**: Avoid generic colors. The UI uses rich gradient themes transitioning from Indigo to Deep Violet and Emerald.
* **Micro-Animations**: Uses `Framer Motion` to provide delightful entry animations, hover scaling on quick actions, and premium modal transitions.
* **Highly Responsive Layouts**: Fully responsive dashboard grid using custom Tailwind flex/grid mappings that flow perfectly across mobile, tablet, and widescreen layouts.
