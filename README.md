# Automação Local de XLSX para Documentos com n8n conteinerizado e GUI Python

English Version: [docs/readme_en.md](docs/readme_en.md)

## Visão Geral
Este projeto é uma prova de conceito que automatiza o processamento de planilhas XLSX e a geração de documentos utilizando workflows do n8n, tudo executado localmente. Ele inclui uma interface gráfica amigável desenvolvida em Python para gerenciar o contêiner Docker do n8n, realizar upload de arquivos e recuperar resultados. O objetivo principal é simplificar a automação de workflows para usuários não técnicos, tornando a configuração e o uso acessíveis.

A motivação para este projeto surgiu da necessidade de uma solução local e simples para gerar documentos a partir de dados de planilhas, sem depender de serviços em nuvem. Além disso, o projeto serve como base para futuras melhorias, como workflows mais complexos e uma experiência de usuário aprimorada.

## Requisitos de Hardware
Não há requisitos específicos de hardware para este projeto, além de um computador capaz de executar Docker e Python 3. Recomenda-se:
- Processador com suporte a virtualização (para Docker)
- 4 GB de RAM ou mais
- 5 GB de espaço em disco disponível

## Requisitos de Software
- **Sistema Operacional:**
  - Linux (qualquer distribuição recente)
  - macOS (não testado)
  - Windows (com WSL2 configurado como padrão)
- **Software Necessário:**
  - Docker
  - Python 3
  - pip3
  - python3-tk (para GUI)
  - curl, sqlite3, jq (usados nos scripts de configuração)
- **Dependências Python:**
  - Listadas no arquivo `src/requirements.txt`, automaticamente instaladas pelo script de entrada.

Para detalhes de intalação de dependencias, consulte [`docs/dependencies_pt.md`](docs/dependencies_pt.md).

## Configuração do Ambiente
### Passo a Passo de Configuração
1. **Clone o repositório:**
   ```bash
   git clone https://github.com/Luan-Daniel/n8n-xlsx-to-docx.git
   cd n8n-xlsx-to-docx
   ```
2. **Execute o script de entrada:**
   - No Linux/macOS: `./run.sh`
   - No Windows: `./run.ps1`
3. **Aguarde a instalação das dependências:**
   - O script configura o ambiente virtual Python e instala as dependências automaticamente.
4. **Inicie a GUI:**
   - A janela da GUI será exibida automaticamente após a configuração inicial.
5. **Importe os dados do n8n:**
   - Use o botão "Importar Dados do n8n" para carregar um workflow de exemplo e configurações de `n8n-files/user-data/default.zip`.
   - Aviso: Utilize as credenciais fornecidas apenas para conveniência. Para uso em produção, crie suas próprias. Veja N8N_USER_EMAIL e N8N_USER_PASSWORD no `src/docker-n8n/.env` descompactado de `n8n-files/user-data/default.zip`.
6. **Inicie o contêiner n8n:**
   - Utilize o botão correspondente na GUI.
7. **Teste o workflow:**
   - Faça upload de um arquivo XLSX de exemplo pela GUI e recupere o documento gerado.

## Como Usar
### Uso Diário
1. **Inicie o contêiner Docker do n8n:**
   - Use a GUI para iniciar/parar o contêiner conforme necessário.
2. **Envie arquivos XLSX:**
   - Faça upload de arquivos XLSX pela GUI para acionar o workflow.
3. **Recupere os documentos gerados:**
   - Os arquivos gerados estarão disponíveis no diretório `n8n-files/documents/`.
4. **Gerencie workflows:**
   - Acesse a interface web do n8n pela GUI para criar ou modificar workflows.

## Estrutura do Projeto e Visão Geral de Implementação
### Organização dos Arquivos
- `src/entrypoint.py`: Configura o ambiente, verifica dependências e inicia a GUI.
- `src/service-manager/main.py`: Aplicação GUI principal, gerencia o contêiner n8n e interações do usuário.
- `src/docker-n8n/`: Scripts para construir e gerenciar o contêiner Docker do n8n.
- `n8n-files/`: Diretório compartilhado com o contêiner n8n, contendo dados de exemplo e arquivos de workflow.
- `docs/`: Documentação do projeto, incluindo dependências e ideias futuras.

### Principais Interações HTTP do Workflow:
- GUI envia HTTP POST para webhook do n8n com informações do arquivo
- n8n processa arquivos e envia resultado de volta para GUI via HTTP POST

### Passos do Workflow de Exemplo:
- Acionado por requisição HTTP da GUI (nome do arquivo xlsx e nome do arquivo de template)
- Lê arquivo XLSX e template de pastas compartilhadas em `n8n-files/sheets/` e `n8n-files/templates/`, respectivamente.
- Extrai os dados do XLSX e os mescla com o binario do template.
- [Docxtemplater](https://github.com/jreyesr/n8n-nodes-docxtemplater) é usado para processar dados e gerar um documento DOCX.
- Salva resultado em `n8n-files/documents/`
- Envia HTTP POST para webhook da GUI com resultado ou código de erro.

### Limitações Conhecidas e Trabalho Futuro
Devido a restrições de tempo, alguns recursos foram deixados incompletos:
- Instalação automática de dependências do sistema está incompleta.
- Processo de configuração pode ser melhorado (substituído por exportar/importar dados).
- Componentes JavaScript para visualização de dados estão presentes mas não totalmente integrados.
- Tratamento de erros precisa de melhorias.
- Template docx está hardcoded; versões futuras devem permitir seleção pelo usuário.

## Troubleshooting
### Problemas Comuns e Soluções
1. **Erro ao iniciar o contêiner Docker:**
   - Verifique se o Docker está instalado e em execução.
   - Certifique-se de que o usuário atual tem permissão para executar comandos Docker.
2. **A GUI não aparece após executar o script:**
   - Verifique se todas as dependências Python estão instaladas corretamente.
   - Consulte o arquivo `src/requirements.txt` para instalar dependências manualmente.
3. **Workflow do n8n não processa arquivos:**
   - Certifique-se de que os arquivos XLSX e templates estão nos diretórios corretos (`n8n-files/sheets/` e `n8n-files/templates/`).
   - Verifique os logs do contêiner n8n para identificar erros.

## Imagens
![](docs/img/GUI.png)
*Figura 1: Interface Gráfica do Gerenciador de Serviço*
![](docs/img/workflow.png)
*Figura 2: Exemplo de Workflow do n8n*

## Contribuidores
- **Luan Daniel (20102096):** Desenvolvedor principal, design de workflow, implementação da GUI.