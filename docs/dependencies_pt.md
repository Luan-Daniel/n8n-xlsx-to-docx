# Guia de Configuração do Sistema

Este guia explica como instalar todas as dependências necessárias no **Linux** e **Windows (WSL2)**.  
Uma vez dentro de um ambiente Unix-like (Linux ou WSL2), as etapas de instalação são unificadas.

---

## Requisitos do Sistema
- **Linux**: Qualquer distribuição recente (Ubuntu, Debian, Fedora, Arch, etc.)
- **macOS**: Versão recente deve funcionar (não testado)
- **Windows**: Requer **WSL2** instalado e configurado como padrão
- **Dependências**:
  - Docker
  - Python3
  - pip3
  - python3-tk
  - curl
  - sqlite3
  - jq
- Outras dependências são instaladas automaticamente durante a primeira execução (requer acesso à internet).

---

## Configuração no Windows (WSL2)

### 1. Habilitar WSL
Abra o **PowerShell como Administrador** e execute:
```powershell
wsl --install
```

Isso instala o WSL com a distribuição Linux padrão (geralmente Ubuntu).  
Se você já tem o WSL instalado, atualize para WSL2:

```powershell
wsl --set-default-version 2
```

### 2. Iniciar WSL2
Abra o Ubuntu (ou sua distribuição escolhida) no Menu Iniciar, ou execute:
```powershell
wsl
```

Agora você está dentro de um shell Linux. Continue com as **etapas de configuração do Linux** abaixo.

---

## Configuração no Linux e WSL2

Execute os seguintes comandos dentro do seu terminal Linux (exemplos para Ubuntu/Debian):

### 1. Atualizar Gerenciador de Pacotes
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar Python3, pip3 e python3-tk
```bash
sudo apt install -y python3 python3-pip python3-tk
```

### 3. Instalar Docker
```bash
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
```

Adicione seu usuário ao grupo Docker para evitar usar `sudo`:
```bash
sudo usermod -aG docker $USER
```

Faça logout e login novamente para que as alterações tenham efeito.
```bash
# no wsl, você pode usar 'exit' ou fechar a janela do terminal
exit
# então reabra o wsl a partir da linha de comando
wsl
```

### 4. Instalar curl, sqlite3 e jq
```bash
sudo apt install -y curl sqlite3 jq
```