ws backend deployemnt as follows

```bash
python3.8 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8080 --ws websockets --ws-ping-interval 5 --ws-ping-timeout 10
```