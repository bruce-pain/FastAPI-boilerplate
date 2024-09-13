# Setting Up Celery and RabbitMQ on a Linux Environment

This guide will walk you through setting up Celery and RabbitMQ on a Linux environment. Celery is a powerful, flexible distributed task queue system, and RabbitMQ is a widely used message broker that Celery can use to send and receive messages.

## Prerequisites

- A Linux-based operating system (Ubuntu/Debian, CentOS, etc.)
- Python 3.6+ installed
- Pip (Python package manager) installed
- Git installed

## Step 1: Install RabbitMQ

RabbitMQ is the message broker that Celery will use to communicate between your application and workers.

### 1.1 Update the System

Before installing any packages, it's a good idea to update your package list:

```bash
sudo apt-get update
```

### 1.2 Install RabbitMQ
```bash
sudo apt-get install rabbitmq-server -y
```

### 1.3 Enable and start RabbitMQ server
```bash
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server
```

### 1.4 Verify RabbitMQ status
```bash
sudo systemctl status rabbitmq-server
```

## Install Celery
Celery can be installed using pip, which is the Python package manager.

### 2.1 Install Celery and Required Dependencies
Create a virtual environment and activate it (recommended):

```bash
python3 -m venv celery-env
source celery-env/bin/activate
```

Install Celery and any additional required dependencies:

```bash
pip install celery
If you're using Django, install Celery with Django support:
```

```bash
pip install celery[django]
```

## Celery commands for this app
Run the following commands in two separate terminsla:
```bash
celery -A api.core.dependencies.celery.celery_app worker --loglevel=info
celery -A api.core.dependencies.celery.celery_app flower --loglevel=info
```

## Access RabbitMQ Management Syatem
You can access the RabbitMQ Management System at :
[http://localhost:15672](http://localhost:15672)


## Access Flower Management Syatem for mMonitoring Background Tasks
You can access the RabbitMQ Management System at :
[http://localhost:5555](http://localhost:5555)