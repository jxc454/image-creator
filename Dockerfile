FROM python

RUN #pip3 install pipenv

ADD dist dist

WORKDIR dist

#RUN tar -xf image-creator-0.1.0.tar.gz

USER root

#RUN pipenv install --deploy --ignore-pipfile
RUN pip3 install image-creator-0.1.0.tar.gz

#CMD ["image-creator", "hello", "world"]
