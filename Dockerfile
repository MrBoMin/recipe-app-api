FROM python:3.9-alpine3.13
LABEL maintainer="technortal.com"

# Set environment variable to ensure Python output is sent straight to terminal
ENV PYTHONUNBUFFERED=1

# Copy requirements and application code
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app

# Set the working directory
WORKDIR /app

# Expose the application port
EXPOSE 8000
ARG DEV=false
# Create a virtual environment and install dependencies
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \ 
    apk add --update --no-cache postgresql-client && \
    apk add --update --no-cache --virtual .tmp-build-deps\
        build-base postgresql-dev musl-dev &&\
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ]; then \
        /py/bin/pip install -r /tmp/requirements.dev.txt; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps &&\
    adduser --disabled-password --no-create-home django-user

# Update the PATH environment variable
ENV PATH="/py/bin:$PATH"

# Switch to the non-root user
USER django-user
