# Setup Instructions

## Step-by-step setup guide

### 1. Install Python 3.10+

Visit https://www.python.org/downloads/ and install Python 3.10 or later.

Verify:
```bash
python --version
```

### 2. Install Azure CLI

Visit https://learn.microsoft.com/cli/azure/install-azure-cli and follow instructions for your OS.

Verify:
```bash
az version
```

### 3. Log in to Azure

```bash
az login
```

### 4. Create an Azure AI Foundry project

1. Go to [Azure AI Foundry](https://ai.azure.com)
2. Create a new project (or use an existing one)
3. Deploy a model — select **gpt-4o** or **gpt-4o-mini**
4. Copy the **Project endpoint** URL — you will need it for `.env`

Format: `https://<resource>.services.ai.azure.com/api/projects/<project>`

### 5. Create and activate a virtual environment

```bash
cd maf_workshop
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 6. Install packages

```bash
pip install -r requirements.txt
```

### 7. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder values with your real endpoint and model name.

### 8. Run the setup verification

```bash
python exercises/ex00-setup/verify_setup.py
```

All checks should pass before proceeding to Exercise 01.
