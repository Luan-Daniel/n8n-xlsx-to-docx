
# Local XLSX-to-Document Automation with conteinerized n8n & Python GUI

Versão em Português: [/readme.md](../readme.md)

## Project Overview
This is a proof-of-concept project that automates the processing of XLSX spreadsheets and document generation using n8n workflows, all running locally. It provides a user-friendly Python GUI to manage the n8n Docker container, upload files, and retrieve results. The project aims to simplify workflow automation for non-developers, making setup and usage as easy as possible.

**Authors:**
- Luan Daniel (lead developer, workflow design, GUI implementation)

---

## Introduction
This project was motivated by the need for a simple, local solution to automate document generation from spreadsheet data, without relying on cloud services. The project also aims to serve as a basis for further development, including more complex workflows and improved user experience.

---

## System Requirements
See [`dependencies_en.md`](dependencies_en.md) for full details and installation instructions.

- **Linux:** Any recent distribution
- **macOS:** Recent version (untested)
- **Windows:** WSL2 installed and set as default
- **Required software:**
  - Docker
  - Python 3
  - pip3
  - python3-tk (for GUI)
  - curl, sqlite3, jq (used in setup scripts)

Other dependencies are installed automatically during first execution. Internet access is required for setup.

---

## Installation & Usage Guide

### General Steps
1. **Clone the repository**
   - On Windows, clone inside WSL2 or outside C:/Users to avoid permission issues.
2. **Run the entrypoint script**
   - On Linux/macOS: `./run.sh`
   - On Windows: `./run.ps1`
   - This sets up the Python virtual environment and installs dependencies.
3. **Wait for the GUI window to appear**
   - Use the "Import n8n Data" button to extract a sample workflow and settings from `n8n-files/user-data/default.zip`.
   - WARNING: You may use provided credentials for convenience, but for production, create your own:
     ```sh
     N8N_USER_EMAIL=luandanielmelo@gmail.com
     N8N_USER_PASSWORD=59fyXaSx4SqUPE9UdMDyhd1jYXSARuL7v2FDNqDI95RZrdtO
     ```
4. **Start the n8n container** using the GUI button.
5. **Open the n8n web interface** and test the workflow by uploading a sample XLSX file via the GUI.

### Following usage:
1. Start/stop the n8n Docker container using the GUI.
2. Use the GUI to download or submit an XLSX file to trigger the workflow. Sample sheet [here](https://docs.google.com/spreadsheets/d/1ozqeJ4xOjd_rN_tQ1jfRHwIGtqdUUawjQhnJll25PGw/edit?usp=sharing).
3. Retrieve the generated document from the output directory specified in the GUI.
4. Use the GUI to open the n8n web interface for workflow management.
5. N8N data can be exported/imported via zip files for easy setup on new machines.

---

## Functionality Overview

- **Main Goal:** Implement an n8n workflow that processes an XLSX file and generates a document from the data, all locally.
- **Python GUI:** Manages the n8n container, handles file download and submission, and displays results.
![](docs/img/GUI.png)
- **Sample Workflow:**
  - Triggered by HTTP request from the GUI (xlsx file name & template file name)
  - Reads XLSX file and template from shared folders on `n8n-files/sheets/` and `n8n-files/templates/`, respectively.
  - Processes data and generates a .docx file using [Docxtemplater](https://github.com/jreyesr/n8n-nodes-docxtemplater).
  - Saves result to `n8n-files/documents/`
  - Sends HTTP POST to GUI webhook with result or error code.
![](docs/img/workflow.png)
---

## Implementation Overview

**Main files and directories:**
- `src/entrypoint.py`: Sets up environment, checks dependencies, launches GUI
- `src/service-manager/main.py`: Main GUI application, manages n8n container and user interactions
- `src/docker-n8n/`: Scripts for building and managing the n8n Docker container
- `n8n-files/`: Shared with n8n container, contains sample data and workflow files

**Workflow HTTP Interactions:**
- GUI sends HTTP POST to n8n webhook with file info
- n8n processes files and sends result back to GUI via HTTP POST

**Sample Workflow Steps:**
1. Webhook receives XLSX and template file names
2. Reads XLSX file using "Read Binary File" node
3. Processes with "XLSX" node to extract data
4. Reads template file
5. Merges data and generates .docx with Docxtemplater
6. Saves .docx to `n8n-files/documents/`
7. Sends result to GUI webhook

---

## Known Limitations & Future Work
Due to time constraints, some features were left incomplete:
- Automatic system dependencies installation is incomplete.
- Setup process can be improved (replaced by export/import data).
- JavaScript components for data visualization are present but not fully integrated.
- Error handling needs improvement.
- Docx template is hardcoded; future versions should allow user selection.

---

## License
This project is distributed for educational purposes.

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