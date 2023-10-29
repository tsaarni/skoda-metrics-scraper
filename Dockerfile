FROM python:3-alpine
ADD main.py requirements.txt /
RUN pip3 install -r requirements.txt
CMD ["python3", "./main.py"]
