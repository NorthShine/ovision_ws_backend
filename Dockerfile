FROM python:3.8
WORKDIR /ovision_ws_backend
COPY requirements.txt /ovision_ws_backend/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /ovision_ws_backend/requirements.txt
COPY src /ovision_ws_backend/app
RUN ls -a app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]