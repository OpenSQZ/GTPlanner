# Pull Request Templates

This directory contains specialized PR templates for different types of contributions to GTPlanner's intelligent tool recommendation system.

## Available Templates

### 🔧 API Tool Contribution (`api_tool.md`)
Use this template when contributing API-based tools to the system.

**When to use:**
- Web APIs and REST services
- Cloud-based processing tools
- External service integrations
- Real-time data processing APIs

**Direct link:** [Create API Tool PR](../../compare?template=api_tool.md)

### 📦 Python Package Tool (`python_package_tool.md`)
Use this template when contributing Python packages from PyPI.

**When to use:**
- PyPI packages and libraries
- Local processing tools
- Data analysis packages
- Utility libraries

**Direct link:** [Create Python Package PR](../../compare?template=python_package_tool.md)

### 📚 Documentation Changes (`documentation.md`)
Use this template for documentation updates and improvements.

**When to use:**
- README updates
- API documentation changes
- Translation updates
- Tutorial/guide additions
- Documentation bug fixes

**Direct link:** [Create Documentation PR](../../compare?template=documentation.md)

### 🛠️ General Contributions (`general.md`)
Use this template for general code changes and improvements.

**When to use:**
- Bug fixes
- Feature additions
- Code refactoring
- Performance improvements
- Build/CI changes

**Direct link:** [Create General PR](../../compare?template=general.md)

## How to Use Templates

### Method 1: URL Parameter
Add `?template=template_name.md` to your PR creation URL:
```
https://github.com/wang316902972/GTPlanner/compare?template=api_tool.md
```

### Method 2: GitHub Interface
1. Click "New pull request"
2. GitHub will show template options if multiple templates exist
3. Select the appropriate template for your contribution

### Method 3: Manual Selection
1. Create a new PR normally
2. Copy the content from the appropriate template file
3. Replace the default template content

## Template Guidelines

### Quality Standards
All contributions must meet these standards:
- ✅ Complete and accurate information
- ✅ Working examples and code snippets
- ✅ Proper testing and validation
- ✅ Clear documentation and descriptions
- ✅ No security vulnerabilities

### Tool Contribution Requirements
For API and Python package tools:
- **Unique identifier** following naming conventions
- **Comprehensive documentation** with examples
- **Quality assurance** checklist completion
- **Testing verification** with results
- **Maintenance status** information

### Required Fields by Tool Type

**APIS Tools:**
- `id`, `type`, `summary`, `description`, `examples`
- `base_url`: API base URL
- `endpoints`: Array with `summary`, `method`, `path`, `inputs`, `outputs`

**PYTHON_PACKAGE Tools:**
- `id`, `type`, `summary`, `description`, `examples`
- `requirement`: PyPI installation requirement (e.g., "package-name==1.0.0")

### Review Process
1. **Automated checks** - Template completeness
2. **Technical review** - Functionality and accuracy
3. **Quality assessment** - Standards compliance
4. **Security review** - Safety and best practices
5. **Community feedback** - User experience validation

## Template Maintenance

These templates are maintained by the GTPlanner team. For template improvements or new template requests:

1. Open an issue with the `template` label
2. Describe the needed changes or new template type
3. Provide justification and use cases
4. Follow the standard contribution process

## Support

If you need help choosing the right template or filling it out:
- Check the [Contributing Guide](../../CONTRIBUTING.md)
- Open a discussion in the repository
- Contact the maintainers

---

**Remember:** Using the correct template helps ensure faster review and better organization of contributions!
