# Contributing to TaskPilot

Thank you for your interest in **TaskPilot**.

## Development setup

```bash
git clone https://github.com/MHussain414/Taskpilot.git
cd TaskPilot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
python run.py
```

## Running tests

```bash
pytest tests/ -v
make test   # if Make is installed
```

## Code style

- Match existing Flask patterns in `app/routes.py` and `app/tasks.py`
- Keep frontend changes in `app/static/` with cache-bust query on `app.js`
- Log user-visible actions via `app/activity.py`

## Pull requests

1. Fork the repository  
2. Create a feature branch (`git checkout -b feature/my-feature`)  
3. Commit with clear messages  
4. Ensure `pytest tests/ -v` passes  
5. Open a PR against `main`

## Reporting issues

Include: OS, Python version, steps to reproduce, and screenshots if UI-related.
