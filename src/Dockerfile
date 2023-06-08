# pull official base image
FROM python:3.9.4

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/usr/src/app:$PYTHONPATH

# install dependencies
RUN pip install --upgrade pip

# copy requirements file
COPY src/requirements.txt .

# install project dependencies
RUN pip install -r requirements.txt

# copy the entire project
COPY . .

# command to run on container start
CMD ["python", "./src/app/main.py"]
