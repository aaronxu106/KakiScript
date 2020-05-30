python -m venv %~dp0\venv
call %~dp0\venv\scripts\activate
pip install -r %~dp0\requirements.txt
pause