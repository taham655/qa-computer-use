# 🧪 RoverQA

**AI-Powered Web Application Testing with Anthropic Computer Use**

RoverQA is an intelligent QA automation platform that crawls websites, generates comprehensive test cases using AI, and executes them through Anthropic's computer-use agent on a virtual desktop.

![RoverQA](https://img.shields.io/badge/RoverQA-AI%20Testing-00d4ff?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-3776ab?style=for-the-badge&logo=python)
![React](https://img.shields.io/badge/React-18-61dafb?style=for-the-badge&logo=react)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ed?style=for-the-badge&logo=docker)

## ✨ Features

- **🔍 Website Crawling** - Automatically discover and map website structure using Firecrawl
- **🔀 Flow Graph Generation** - Visualize navigation paths and user flows with interactive Mermaid diagrams
- **🤖 AI Test Generation** - Generate comprehensive test cases using OpenAI or Anthropic
- **🖥️ Computer-Use Execution** - Execute tests on a real browser using Claude's computer-use capabilities
- **📊 Real-time Feedback** - Watch test execution live via WebSocket with screenshots
- **📥 Export Options** - Download tests as Playwright scripts, JSON, or test plans


## 🚀 Getting Started

### Prerequisites

- Docker installed on your machine
- API Keys:
  - **Firecrawl API Key** - For website crawling ([Get one here](https://firecrawl.dev))
  - **OpenAI API Key** - For test case generation ([Get one here](https://platform.openai.com))
  - **Anthropic API Key** - For computer-use test execution ([Get one here](https://console.anthropic.com))

### Quick Start with Docker

1. **Clone the repository**

```bash
git clone https://github.com/taham655/qa-computer-use.git
cd qa-computer-use/computer-use-demo
```

2. **Build the Docker image**

```bash
docker build -t ai-qa-demo .
```

3. **Run the container**

```bash
docker run -it --rm -p 5900:5900 -p 8501:8501 -p 6080:6080 -p 8080:8080 -e APP_MODE=qa
  -e FIRECRAWL_API_KEY=your_firecrawl_key \
  -e OPENAI_API_KEY=your_openai_key \
  -e ANTHROPIC_API_KEY=your_anthropic_key \
  -e WIDTH=1280 -e HEIGHT=800 ai-qa-demo
```

4. **Access the application**

- **RoverQA Web App**: [http://localhost:8501](http://localhost:8501)
- **Virtual Desktop (VNC)**: [http://localhost:6080/vnc.html](http://localhost:6080/vnc.html)

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FIRECRAWL_API_KEY` | Firecrawl API key for web crawling | ✅ |
| `OPENAI_API_KEY` | OpenAI API key for test generation | ✅ (or Anthropic) |
| `ANTHROPIC_API_KEY` | Anthropic API key for computer-use execution | ✅ |
| `APP_MODE` | Application mode (`qa` for RoverQA) | ✅ |
| `WIDTH` | Virtual desktop width (default: 1024) | ❌ |
| `HEIGHT` | Virtual desktop height (default: 768) | ❌ |

## 🎯 How to Use

### 1. Crawl a Website

Enter a URL and click **Start Crawl**. RoverQA will:
- Discover all pages on the site
- Extract navigation structure
- Build a flow graph of user journeys

### 2. Generate Test Cases

Click **Generate Tests** to create AI-powered test cases:
- Happy path scenarios
- Edge cases
- Error handling tests
- Security tests
- Accessibility tests

### 3. Execute Tests

Click **Execute Tests** to run them with the computer-use agent:
- Watch Claude interact with the browser in real-time
- View screenshots of each step
- Get pass/fail results with explanations

### 4. Export Results

Download your test cases as:
- **Playwright** - Ready-to-run TypeScript tests
- **JSON** - Structured test data
- **Test Plan** - Human-readable documentation

### Project Structure

```
roverqa/
├── computer_use_demo/
│   ├── api.py              # FastAPI backend
│   ├── loop.py             # Anthropic sampling loop
│   ├── qa/
│   │   ├── crawler.py      # Firecrawl integration
│   │   ├── flow_graph.py   # Flow graph generation
│   │   ├── test_generator.py  # AI test generation
│   │   └── test_executor.py   # Test execution logic
│   └── tools/              # Computer-use tools
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   └── lib/            # API client
│   └── ...
├── image/                  # Docker image scripts
├── Dockerfile
└── README.md
```
