
# Automação Local de XLSX para Documentos com n8n conteinerizado e GUI Python

English version: [docs/readme_en.md](docs/readme_en.md)

## Visão Geral do Projeto
Este é um projeto de prova de conceito que automatiza o processamento de planilhas XLSX e geração de documentos usando workflows do n8n, tudo executando localmente. Ele fornece uma GUI Python amigável para gerenciar o contêiner Docker do n8n, fazer upload de arquivos e recuperar resultados. O projeto visa simplificar a automação de workflows para não-desenvolvedores, tornando a configuração e uso o mais fácil possível.

**Autores:**
- Luan Daniel (desenvolvedor principal, design de workflow, implementação da GUI)

---

## Introdução
Este projeto foi motivado pela necessidade de uma solução simples e local para automatizar a geração de documentos a partir de dados de planilhas, sem depender de serviços em nuvem. O projeto também visa servir como base para desenvolvimento futuro, incluindo workflows mais complexos e experiência de usuário aprimorada.

---

## Requisitos do Sistema
Veja [`docs/dependencies.md`](docs/dependencies_pt.md) para detalhes completos e instruções de instalação.

- **Linux:** Qualquer distribuição recente
- **macOS:** Versão recente (não testado)
- **Windows:** WSL2 instalado e configurado como padrão
- **Software necessário:**
  - Docker
  - Python 3
  - pip3
  - python3-tk (para GUI)
  - curl, sqlite3, jq (usados nos scripts de configuração)

Outras dependências são instaladas automaticamente durante a primeira execução. Acesso à internet é necessário para a configuração.

---

## Guia de Instalação e Uso

### Passos Gerais
1. **Clone o repositório**
   - No Windows, clone dentro do WSL2 ou fora de C:/Users para evitar problemas de permissão.
2. **Execute o script de entrada**
   - No Linux/macOS: `./run.sh`
   - No Windows: `./run.ps1`
   - Isso configura o ambiente virtual Python e instala as dependências.
3. **Aguarde a janela da GUI aparecer**
   - Use o botão "Importar Dados do n8n" para extrair um workflow de exemplo e configurações de `n8n-files/user-data/default.zip`.
   - AVISO: Você pode usar as credenciais fornecidas por conveniência, mas para produção, crie as suas próprias:
     ```sh
     N8N_USER_EMAIL=luandanielmelo@gmail.com
     N8N_USER_PASSWORD=59fyXaSx4SqUPE9UdMDyhd1jYXSARuL7v2FDNqDI95RZrdtO
     ```
4. **Inicie o contêiner n8n** usando o botão da GUI.
5. **Abra a interface web do n8n** e teste o workflow fazendo upload de um arquivo XLSX de exemplo pela GUI.

### Uso subsequente:
1. Inicie/pare o contêiner Docker do n8n usando a GUI.
2. Use a GUI para baixar ou enviar um arquivo XLSX para acionar o workflow. Planilha de exemplo [aqui](https://docs.google.com/spreadsheets/d/1ozqeJ4xOjd_rN_tQ1jfRHwIGtqdUUawjQhnJll25PGw/edit?usp=sharing).
3. Recupere o documento gerado do diretório de saída especificado na GUI.
4. Use a GUI para abrir a interface web do n8n para gerenciamento de workflows.
5. Os dados do n8n podem ser exportados/importados via arquivos zip para facilitar a configuração em novas máquinas.

---

## Visão Geral da Funcionalidade

- **Objetivo Principal:** Implementar um workflow n8n que processa um arquivo XLSX e gera um documento a partir dos dados, tudo localmente.
- **GUI Python:** Gerencia o contêiner n8n, lida com download e envio de arquivos, e exibe resultados.
![](docs/img/GUI.png)
- **Workflow de Exemplo:**
  - Acionado por requisição HTTP da GUI (nome do arquivo xlsx e nome do arquivo de template)
  - Lê arquivo XLSX e template de pastas compartilhadas em `n8n-files/sheets/` e `n8n-files/templates/`, respectivamente.
  - Processa dados e gera um arquivo .docx usando [Docxtemplater](https://github.com/jreyesr/n8n-nodes-docxtemplater).
  - Salva resultado em `n8n-files/documents/`
  - Envia HTTP POST para webhook da GUI com resultado ou código de erro.
![](docs/img/workflow.png)
---

## Visão Geral da Implementação

**Principais arquivos e diretórios:**
- `src/entrypoint.py`: Configura ambiente, verifica dependências, inicia a GUI
- `src/service-manager/main.py`: Aplicação GUI principal, gerencia contêiner n8n e interações do usuário
- `src/docker-n8n/`: Scripts para construir e gerenciar o contêiner Docker do n8n
- `n8n-files/`: Compartilhado com o contêiner n8n, contém dados de exemplo e arquivos de workflow

**Interações HTTP do Workflow:**
- GUI envia HTTP POST para webhook do n8n com informações do arquivo
- n8n processa arquivos e envia resultado de volta para GUI via HTTP POST

**Passos do Workflow de Exemplo:**
1. Webhook recebe nomes de arquivos XLSX e template
2. Lê arquivo XLSX usando o nó "Read Binary File"
3. Processa com o nó "XLSX" para extrair dados
4. Lê arquivo de template
5. Mescla dados e gera .docx com Docxtemplater
6. Salva .docx em `n8n-files/documents/`
7. Envia resultado para webhook da GUI

---

## Limitações Conhecidas e Trabalho Futuro
Devido a restrições de tempo, alguns recursos foram deixados incompletos:
- Instalação automática de dependências do sistema está incompleta.
- Processo de configuração pode ser melhorado (substituído por exportar/importar dados).
- Componentes JavaScript para visualização de dados estão presentes mas não totalmente integrados.
- Tratamento de erros precisa de melhorias.
- Template docx está hardcoded; versões futuras devem permitir seleção pelo usuário.

---

## Licença
Este projeto é distribuído para fins educacionais.

<!-- Authors notes: -->
<!--title and paragraph summarizing project-->

<!--Setup Guide-->
<!-- System Dependencies instalation guide: points to dependencies.md -->
<!-- Project installation guide:
- Clone the repository (in windows, we recommend using cloning inside wsl2 or out of C:/Users subdirectories to avoid permission issues)
- First execution will set up the virtual environment and install dependencies. See the guide for first execution below.
-->
<!-- First execution guide:
  - Run the entrypoint script according to your OS (./run.sh or ./run.ps1) and wait for python venv dependencies to be installed.
  - When the GUI window appears, we recommend using the "Import n8n Data" button to extract a zip file containg a sample workflow. It also contains n8n settings, credentials, and environment variables, all setup.
  - n8n-files/user-data/default.zip is provided for convenience, but you can setup your own n8n credentials and workflow on the fly if you prefer.
```sh
N8N_USER_EMAIL=luandanielmelo@gmail.com
N8N_USER_PASSWORD=59fyXaSx4SqUPE9UdMDyhd1jYXSARuL7v2FDNqDI95RZrdtO
```
(WARNING: this file is public to speed setup and make testing on new machines easier, you should eventually create your own credentials for production use)
  - After importing the n8n data, you can start the n8n container using the button on the GUI.
  - You can then open the n8n web interface using the provided button, and test the workflow by uploading a sample xlsx file using the service manager GUI.
  - For now, the workflow is very simple. But can be upgraded to do more complex tasks as needed.
 -->

<!-- Functionality overview:
The projects main goal was to implement an n8n workflow that processes an xlsx file and generates a document from the data, **all locally**. It serves as a proof of concept and basis for further development.

As the project evolved, a GUI application was created to manage the n8n container and provide a user-friendly interface for uploading files and retrieving results. This application also handles dependency management and setup, making it easier for end users to get started.

Due to time constraints, some features were left incomplete: 
- automatic system dependencies installation.
- improved setup process (replaced by export/import data).
- use of javascript components to create data visualization (components install but remain unused/untested).
- better error handling.
-->

<!-- Implementation overview:

Main files and directories:
- src/entrypoint.py: main entrypoint script, handles dependency installation and launching the service manager GUI.
- src/service-manager/main.py: main GUI application, handles n8n container management and user interactions.
- src/docker-n8n/: contains scripts for building and managing the n8n docker container.
- n8n-files/: binds to the n8n container, used to share files with the workflow. Also contains sample n8n data for easy setup.

Sample workflow HTTP interactions:
- The service manager GUI communicates with the n8n workflow using HTTP requests to webhooks:
- GUI post http request -> n8n webhook -> workflow processing -> n8n post http request -> GUI webhook.
- The n8n webhook expects to get the xlsx file name and template file name. It triggers the workflow to read the indicated files from n8n-files/sheets/ and n8n-files/templates/, respectively;
- After processing, the workflow sends a HTTP POST request to the GUI webhook with the resulting files list or error code.

Sample workflow implementation description:
- The workflow is triggered by a webhook that receives the xlsx file name and template file name.
- It reads the xlsx file using the "Read Binary File" node, and processes it using the "XLSX" node to extract data into json. (Sample xlsx sheet [here](https://docs.google.com/spreadsheets/d/1ozqeJ4xOjd_rN_tQ1jfRHwIGtqdUUawjQhnJll25PGw/edit?usp=sharing))
- The template file is read similarly, but kept in binary form.
- Their data is merged and sent to the Docxtemplater node, which generates a .docx file using the template and xlsx data.
- Finally, the resulting .docx file is saved to n8n-files/documents/ using the "Write Binary File" node.
- The workflow then sends a HTTP POST request to the GUI webhook with the resulting files list or error code.
-->