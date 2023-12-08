FROM python:3.11
EXPOSE 8080
WORKDIR .
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
