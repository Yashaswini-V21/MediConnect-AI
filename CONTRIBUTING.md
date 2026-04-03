# Contributing to  MediConnect-AI

First off, thank you for considering contributing to MediConnect-AI! 🎉

This project is a **capstone project** for the **IBM SkillBuild AIML Internship** in partnership with **Edunet Foundation**. While this is primarily an internship project, we welcome feedback and suggestions from the community.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

---

## 📜 Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful and constructive in all interactions.

### Our Standards

- **Be Respectful**: Treat everyone with respect and consideration
- **Be Collaborative**: Work together and help each other
- **Be Professional**: Keep discussions focused and productive
- **Be Inclusive**: Welcome contributors of all backgrounds and experience levels

---

## 🤝 How Can I Contribute?

### Reporting Bugs 🐛

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title** and **description**
- **Steps to reproduce** the issue
- **Expected behavior** vs **actual behavior**
- **Screenshots** if applicable
- **Environment details** (OS, browser, versions)

### Suggesting Enhancements ✨

Enhancement suggestions are welcome! Please provide:

- **Clear use case** for the enhancement
- **Detailed description** of the proposed functionality
- **Mockups or examples** if applicable
- **Explanation** of why this would be useful

### Contributing Code 💻

Areas where you can contribute:

- **Bug Fixes**: Fix reported issues
- **Features**: Implement new features from roadmap
- **UI/UX**: Improve design and user experience
- **Documentation**: Enhance docs and guides
- **Tests**: Add unit and integration tests
- **Translations**: Add support for more languages
- **Performance**: Optimize code and queries

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 16+ and npm
- **Python** 3.10+
- **Git** for version control
- Code editor (VS Code recommended)

### Setup Development Environment

1. **Fork the repository**
   ```bash
   # Click the "Fork" button on GitHub
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/MediConnect-AI.git
   cd MediConnect-AI
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/Yashaswini-V21/MediConnect-AI.git
   ```

4. **Install dependencies**
   ```bash
   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Frontend
   cd ../frontend
   npm install
   ```

5. **Configure environment**
   ```bash
   # Create backend/.env
   JWT_SECRET_KEY=your_dev_secret_key
   FLASK_SECRET_KEY=your_flask_secret
   ```

6. **Run development servers**
   ```bash
   # Terminal 1 - Backend
   cd backend
   python app.py
   
   # Terminal 2 - Frontend
   cd frontend
   npm start
   ```

---

## 🔄 Development Workflow

### 1. Create a Branch

Always create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `style/` - UI/UX improvements
- `refactor/` - Code refactoring
- `test/` - Adding tests

### 2. Make Changes

- Write clean, readable code
- Follow existing code style
- Add comments for complex logic
- Update documentation if needed

### 3. Test Your Changes

- Test functionality thoroughly
- Ensure no existing features break
- Test on different screen sizes (responsive)
- Check browser console for errors

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add hospital rating system"
```

### 5. Stay Updated

Keep your branch up to date with upstream:

```bash
git fetch upstream
git rebase upstream/main
```

### 6. Push Changes

```bash
git push origin feature/your-feature-name
```

---

## 📝 Coding Standards

### Python (Backend)

- Follow **PEP 8** style guide
- Use **snake_case** for variables and functions
- Add **docstrings** to functions and classes
- Keep functions **small and focused**
- Use **type hints** where applicable

**Example:**
```python
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    
    Args:
        lat1, lon1: First coordinate
        lat2, lon2: Second coordinate
        
    Returns:
        Distance in kilometers
    """
    # Implementation
    pass
```

### JavaScript/React (Frontend)

- Use **ES6+** syntax
- Use **functional components** with hooks
- Follow **camelCase** for variables and functions
- Use **PascalCase** for components
- Add **PropTypes** or TypeScript types
- Keep components **small and reusable**

**Example:**
```javascript
const HospitalCard = ({ hospital, onSelect }) => {
  const [isLoading, setIsLoading] = useState(false);
  
  const handleClick = () => {
    setIsLoading(true);
    onSelect(hospital.id);
  };
  
  return (
    <div className="hospital-card">
      {/* Component JSX */}
    </div>
  );
};
```

### CSS/Tailwind

- Use **Tailwind utility classes** first
- Create **custom classes** only when necessary
- Follow **mobile-first** approach
- Use **CSS variables** for themes
- Keep **specificity low**

---

## 💬 Commit Guidelines

We follow **Conventional Commits** for clear git history:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Examples

```bash
feat(symptom-checker): add voice input support

fix(hospitals): resolve GPS navigation error for missing coordinates

docs(readme): update deployment instructions

style(dashboard): improve mobile responsive layout
```

---

## 🔍 Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Changes tested thoroughly
- [ ] No console errors or warnings
- [ ] Commit messages follow conventions

### Submitting PR

1. **Push** your branch to your fork
2. **Create Pull Request** from your fork to main repository
3. **Fill out PR template** completely
4. **Link related issues** using keywords (Fixes #123)
5. **Request review** from maintainers

### PR Title Format

```
feat: add hospital rating system
fix: resolve CORS error in symptom API
docs: update API documentation
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
How was this tested?

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes
```

### After Submission

- **Respond** to review comments promptly
- **Make requested changes** if needed
- **Update PR** with additional commits
- **Be patient** - reviews may take time

---

## 🎯 Development Focus Areas

### High Priority

- 🐛 Bug fixes and error handling
- 📱 Mobile responsiveness improvements
- ♿ Accessibility enhancements
- 🌐 Additional language translations
- 🔒 Security improvements

### Medium Priority

- ✨ UI/UX enhancements
- 📊 New analytics features
- 🏥 Hospital data expansion
- 🧪 Test coverage increase
- 📝 Documentation improvements

### Nice to Have

- 🎨 Animation improvements
- 🔔 Additional notification types
- 📈 Performance optimizations
- 🌙 Theme customization options

---

## 📚 Resources

### Documentation

- [README.md](README.md) - Project overview
- [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) - API reference
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment guide

### External Resources

- [React Documentation](https://react.dev/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

## ❓ Questions?

If you have questions about contributing:

1. Check existing [documentation](docs/)
2. Search [closed issues](https://github.com/Yashaswini-V21/MediConnect-AI/issues?q=is%3Aissue+is%3Aclosed)
3. Open a [new issue](https://github.com/Yashaswini-V21/MediConnect-AI/issues/new) with the "question" label

---

## 🙏 Thank You!

Your contributions help make healthcare more accessible. Every contribution, no matter how small, is valuable and appreciated!

**Happy Coding!** 💙

---

<div align="center">

**MediConnect-AI** - IBM SkillBuild AIML Internship

Made with 💙 by the community, for better healthcare access

</div>
