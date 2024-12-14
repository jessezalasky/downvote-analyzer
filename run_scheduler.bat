@echo off
call venv\Scripts\activate
python scheduler.py >> scheduler_output.log 2>&1