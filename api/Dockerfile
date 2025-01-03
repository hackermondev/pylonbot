FROM python:3.8-slim-buster

ADD api/ api/
ADD rpc/ rpc/
COPY requirements.txt /

RUN apt-get update -yy && apt-get install -y git
RUN python -m pip install wheel
RUN python -m pip install -r requirements.txt

RUN cd rpc/python && python setup.py build_proto && python setup.py install
RUN cd api/ && python setup.py install
RUN python -m pip install rpc-1.0-py3-none-any.whl hypercorn[uvloop]==0.9.5

RUN apt-get purge -y git

EXPOSE 80
ENTRYPOINT ["hypercorn", "pylon.server:app", "--worker-class=uvloop", "--bind=127.0.0.1:80", "--access-logfile=-", "--error-logfile=-"]
