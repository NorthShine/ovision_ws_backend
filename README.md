ws backend deployemnt as follows

```bash
python3.8 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
uvicorn main:app
```