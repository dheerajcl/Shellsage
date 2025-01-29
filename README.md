# Shell Sage 🐚✨

**Intelligent Terminal Companion | AI-Powered Terminal Assistant**  
*(Development Preview - v0.2.0)*

---

## Features

### 🌟 Next-Gen Terminal Experience
- 🏠 Local AI Support (Ollama) & Cloud AI (Groq)
- 🔍 Context-aware error diagnosis
- 🪄 Natural language to command translation
- ⚡ Safe command execution workflows

## 🔧 Core Capabilities

### Error Diagnosis

```bash
# Error analysis example
$ rm -rf /important-folder
🔎 Analysis → 🛠️ Fix: `rm -rf ./important-folder`
```

### Natural Language to Commands

```bash
# Command generation
$ shellsage ask "find large files over 1GB"
# → find / -type f -size +1G -exec ls -lh {} \;
```

### ⚡ Interactive Workflows
- Confirm before executing generated commands
- Step-by-step complex operations
- Safety checks for destructive commands

---

## Installation

### Prerequisites
- Python 3.8+
- (4GB+ recommended for local models)

```bash
# 1. Install Ollama for local AI
curl -fsSL https://ollama.com/install.sh | sh

# 2. Get base model (3.8GB) 
#for example
ollama pull llama3:8b-instruct-q4_1

# or API key (Currently GROQ, other options will be available soon!)
export GROQ_API_KEY=your_key_here
shellsage config --mode api

# 3. Clone & install Shell Sage
git clone https://github.com/dheerajcl/Terminal_assistant.git
cd Terminal_assistant
./install.sh
```

---

## Configuration

### First-Time Setup
```bash
# Interactive configuration wizard
shellsage setup

? Select operation mode: 
  ▸ Local (Privacy-first, needs 4GB+ RAM) 
    API (Faster but requires internet)

? Choose local model:
  ▸ llama3:8b-instruct-q4_1 (Recommended)
    mistral:7b-instruct-v0.3
    phi3:mini-128k-instruct
```

### Runtime Control

```bash
# Switch modes
shellsage config --mode local  # or 'api' (Only Groq is supported at present, other options will roll out soon!)
```

---

## Development Status 🚧

Shell Sage is currently in **alpha development**.  

**Known Limitations**:
- Limited Windows support
- Occasional false positives in error detection

**Roadmap**:
- [x] Local LLM support
- [x] Hybrid cloud(api)/local mode switching
- [x] Model configuration wizard
- [ ] Plugin system
- [ ] Windows PowerShell integration
- [ ] Local model quantization
- [ ] CI/CD error pattern database

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feat/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feat/amazing-feature`)
5. Open Pull Request

---


> **Note**: This project is not affiliated with any API or model providers.  
> Local models require adequate system resources.
> Internet required for initial setup and API mode.  
> Use at your own risk with critical operations.
> Always verify commands before execution
