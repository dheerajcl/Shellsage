Here's the complete raw markdown for the README.md:

```markdown
# Shell Sage 🐚✨

**Intelligent Terminal Companion | Error Analysis & Command Generation**  
*(Development Preview - v0.1.0)*

---

## Features

### 🔍 AI-Powered Error Diagnosis
- Automatic error analysis with contextual suggestions
- Multi-step corrective workflows
- Git-aware troubleshooting

### 🪄 Natural Language to Commands
```bash
shellsage ask "compress all .log files older than 7 days"
# → find . -name "*.log" -mtime +7 -exec gzip {} \;
```

### ⚡ Interactive Workflows
- Confirm before executing generated commands
- Step-by-step complex operations
- Safety checks for destructive commands

---

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/shell-sage
cd shell-sage

#Install dependencies:
./install.sh

```

## Basic Usage

### Error Analysis
```bash
# Manual analysis
shellsage run "invalid-command"

# Automatic analysis (after install)
git checkt main  # Typo → suggests correction
```

### Command Generation
```bash
shellsage ask "set up python virtual environment"
# 1. python -m venv env
# 2. source env/bin/activate
```

---

## Development Status 🚧

Shell Sage is currently in **alpha development**.  
**Known Limitations**:
- Limited Windows support
- API dependency for AI features
- Occasional false positives in error detection

**Roadmap**:
- [ ] Local LLM support
- [ ] Plugin system
- [ ] Offline mode
- [ ] Windows PowerShell integration

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feat/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feat/amazing-feature`)
5. Open Pull Request

---


> **Note**: This project is not affiliated with any API providers.  
> Requires internet connection for AI features.  
> Use at your own risk with critical operations.
```
