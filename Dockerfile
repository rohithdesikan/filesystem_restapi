FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

# Set workdir
WORKDIR /app

# Add necessary folders
COPY . /app

# Install pip requirements
RUN pip install --upgrade pip
RUN pip --no-cache-dir install -r requirements.txt

# Expose the 8000 port
EXPOSE 8000

CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0"]