FROM python:3.12-alpine

WORKDIR /shirino

COPY ./requirements.txt .

RUN pip3 install --no-cache-dir --upgrade -r ./requirements.txt

COPY ./ /shirino/

CMD ["python", "main.py"]