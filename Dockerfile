FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

# Set workdir
WORKDIR /app

# ENV ROOT_DIR /Users/rohithdesikan/Desktop/data_analysis/wgridtest/test_folder
ENV ROOT_DIR /data

# Add necessary folders
COPY ./app /app
COPY ./requirements.txt /app

# Install pip requirements
RUN pip install --upgrade pip
RUN pip --no-cache-dir install -r requirements.txt

# Expose the 8000 port
EXPOSE 8000

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]