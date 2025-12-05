Finish the python entrypoint (src/entrypoint.py):
- Create window popup for updating dependencies before gui starts.
- Should set up venv and install requirements.txt
- Should check system requirements and prompt if missing (eg.: linux/wsl, docker installed)
- Should run the main python script
- Also should write ./run.ps1 and ./run.sh for easier launching on windows/linux. They should check for python and call the entrypoint.py.
- Now also need to ensure wsl2 is used on windows, and also tkinter `python3-tk` is installed.
Fishish the service manager (src/service-manager/main.py):
- Is a GUI Application, Its main purposes are:
  - To keep the docker n8n container running properly while the user uses the app (option to start/stop). Button behavior:
    - Container not running or doesnt exist: Offer to start it, using the "./src/docker-n8n/start-n8n.sh" script. And wait for the script to finish to change the button state.
    - Container running: Offer to stop it, using the "./src/docker-n8n/stop-n8n.sh" script. And wait for the script to finish with 0 to change the button state (the script may fail with 1).
  - To provide a simple GUI for the user to input a xlsx file (that triggers the n8n workflow run with a request).
  - Copy the resulting files to a user specified output directory automatically.
- Provide a button to open the n8n web interface in the default browser.
- Dont forget the sheet_downloader functionality.
- The n8n will send back error codes or the resulting files list (inside n8n-data/app/*/ subdirectories) when they are done, using HTTP POST requests, so we need to handle those requests and display the progress to the user (and eventual success), and point the resulting files locations and names.
Finish setting the n8n workflow:
- Should receive a HTTP request with the xlsx file location
- Should process the xlsx file and generate the charts
- Should save the resulting files to a specified output directory
Work on the auto-setup and setup documentation:
- The project should be easy to set up for end users (non-developers)
- Thinking of packing the n8n-data and .env for easier distribution. User will be advised to create their own credentials, but for convenience some defaults might be provided.
- Work on common setup variables like webhook url, input/output directories, etc.
Work on the repository documentation:
- User guide
- Developer guide
- Setup guide
---

Update: I think the libraries are not installed correctly. See Dockerfile. Maybe its the directory where they are installed.
I think trying to switch the code nodes to python might be easier. Needs investigation.

# n8n local runner

This folder contains a small helper to build and run a local n8n Docker container with persistent data.

Files:
- `Dockerfile` - image additions for charting libs
- `run.sh` - enhanced runner (builds image if missing, loads .env, sets up persistent storage)
- `.env` (optional) - place next to `run.sh` to configure runtime options

Recommended `.env` example:

```
# Use a named volume for persistence (optional). If unset, runner will create ./n8n-data
N8N_VOLUME_NAME=n8n-data

# Host port for n8n
PORT=5678

# Database settings (sqlite by default)
DB_TYPE=sqlite
DB_SQLITE_FILE=/home/node/.n8n/database.sqlite
```

Usage:

From this directory run:

```bash
./run.sh
```

What the script does:
- Builds the Docker image `n8n-custom:local` from `Dockerfile` if it doesn't exist
- Loads environment variables from `.env` (if present) and passes them to the container
- Creates/uses a named Docker volume `N8N_VOLUME_NAME` or falls back to `./n8n-data`
- Starts the container `n8n-custom` and maps the configured port

Notes:
- For production use prefer a named Docker volume and a proper DB (MySQL/Postgres).
- The Dockerfile runs `npm install chartjs-node-canvas` to enable server-side chart rendering.
