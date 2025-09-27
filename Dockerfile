FROM python:3.9

RUN apt-get update

COPY . .

RUN python -m venv /opt/venv
RUN /bin/bash -c "source /opt/venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

ENV PATH="/opt/venv/bin:$PATH"
CMD ["python", "main.py"]