# Docker Introduction — Notes

## What is Docker?

Docker is a platform for developing, shipping, and running applications in isolated environments called **containers**.

Think of it this way:
- Without Docker: you install Python 3.9 on your Mac, your colleague has Python 3.11 on Ubuntu, the server runs Python 3.8 → bugs everywhere
- With Docker: everyone runs the **exact same container image** → behavior is identical

---

## Core Concepts

### Images vs Containers

| Concept | Analogy | Description |
|---------|---------|-------------|
| **Image** | Recipe / Blueprint | A read-only snapshot of a filesystem + metadata |
| **Container** | Cooked dish / Running instance | A live, running instance of an image |

You can run many containers from the same image, and each is isolated.

### Dockerfile

A `Dockerfile` is a script of instructions to build a custom image:

```dockerfile
# Start from an existing base image
FROM python:3.11

# Set working directory inside the container
WORKDIR /app

# Copy files from host into the container
COPY requirements.txt .

# Run commands during image build
RUN pip install -r requirements.txt

# Copy remaining source code
COPY . .

# Default command when container starts
ENTRYPOINT ["python", "ingest_data.py"]
```

---

## Essential Docker Commands

```bash
# Pull an image from Docker Hub
docker pull postgres:13

# Run a container interactively
docker run -it ubuntu bash

# Run in detached mode (background)
docker run -d postgres:13

# Run with environment variables + port mapping
docker run -d \
  -e POSTGRES_USER=root \
  -e POSTGRES_PASSWORD=root \
  -e POSTGRES_DB=ny_taxi \
  -p 5432:5432 \
  postgres:13

# List running containers
docker ps

# List ALL containers (including stopped)
docker ps -a

# Stop a container
docker stop <container_id>

# Remove a container
docker rm <container_id>

# List all images
docker images

# Remove an image
docker rmi <image_name>

# View container logs
docker logs <container_id>

# Execute command inside running container
docker exec -it <container_id> bash

# Build a custom image from Dockerfile
docker build -t my-image:v1 .
```

---

## Port Mapping

Containers are isolated — their ports aren't accessible from your host machine unless you map them:

```
Host Port → Container Port
  5432    →     5432        (PostgreSQL)
  8080    →     80          (pgAdmin)
```

Flag: `-p <host_port>:<container_port>`

---

## Docker Volumes

Data inside containers is **ephemeral** — it disappears when the container is removed. Volumes persist data:

```bash
# Named volume
docker run -v my_pg_data:/var/lib/postgresql/data postgres:13

# Bind mount (map a host directory)
docker run -v $(pwd)/data:/app/data my-image
```

---

## Docker Networks

Containers on the same network can talk to each other using their **service names** as hostnames. This is how pgAdmin connects to PostgreSQL — not via `localhost`, but via the container name `pgdatabase`.

```bash
# Create a network
docker network create pg-network

# Run postgres on the network
docker run --network=pg-network --name pgdatabase postgres:13

# Run pgAdmin on same network — it can reach postgres at "pgdatabase"
docker run --network=pg-network --name pgadmin dpage/pgadmin4
```

---

## docker-compose

Managing multiple containers with individual `docker run` commands gets tedious. `docker-compose` lets you define everything in a single YAML file:

```yaml
services:
  database:
    image: postgres:13
    environment:
      POSTGRES_USER: root
    ports:
      - "5432:5432"
  
  admin:
    image: dpage/pgadmin4
    ports:
      - "8080:80"
    depends_on:
      - database
```

Then just:
```bash
docker-compose up -d    # start all
docker-compose down     # stop and remove all
```

---

## Why Docker Matters for Data Engineering

1. **Reproducibility** — pipeline runs identically on dev, staging, and production
2. **Dependency isolation** — Spark 3.4 in one container, different version in another — no conflicts
3. **Easy teardown** — spin up a Postgres DB for testing, destroy it when done
4. **CI/CD integration** — containers make automation and deployment straightforward
5. **Industry standard** — orchestration tools (Airflow, Prefect, Mage) all run in containers
