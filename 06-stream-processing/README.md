# Module 6: Stream Processing with Kafka

## Overview

All previous modules processed data in **batches** — files that already exist.
But what if you need to process data **as it arrives**, in real time?

Examples:
- A taxi trip completes → immediately update driver earnings dashboard
- A credit card transaction → instantly check for fraud
- A sensor reading → immediately trigger an alert if threshold exceeded

That's **stream processing**, and **Apache Kafka** is the backbone of most real-time
data pipelines at scale.

---

## What I Learned

### Batch vs Stream Processing

| | Batch | Stream |
|--|-------|--------|
| **When processed** | Data is collected, then processed | Processed as it arrives |
| **Latency** | Minutes to hours | Milliseconds to seconds |
| **Tools** | Spark, dbt, SQL | Kafka, Spark Streaming, Flink |
| **Use case** | Nightly reports, monthly analytics | Fraud detection, live dashboards |
| **Data size** | Large historical dataset | Continuous, potentially infinite |

### What is Kafka?

Kafka is a distributed **event streaming platform**. Think of it as a
high-throughput, fault-tolerant message queue built for real-time data.

Core model: **Producers** write events → **Topics** store events → **Consumers** read events

```
   Producer A ──┐
   Producer B ──┤──► Topic: "taxi-trips" ──► Consumer: Fraud Detector
   Producer C ──┘                        └──► Consumer: Dashboard Updater
                                          └──► Consumer: Data Lake Writer
```

### Core Concepts

**Topic** — a named stream of events (like a table in a DB, or a queue)

**Partition** — topics are split into partitions for parallelism:
```
Topic: "taxi-trips"
├── Partition 0: [msg1, msg4, msg7, ...]
├── Partition 1: [msg2, msg5, msg8, ...]
└── Partition 2: [msg3, msg6, msg9, ...]
```

**Offset** — each message has a sequential ID within its partition.
Consumers track their offset to know where they left off (allows replay).

**Consumer Group** — multiple consumers sharing the work of reading a topic.
Each partition is assigned to exactly one consumer in the group:

```
Consumer Group "analytics"
├── Consumer 1 reads Partition 0
├── Consumer 2 reads Partition 1
└── Consumer 3 reads Partition 2
```

**Retention** — Kafka keeps messages for a configurable period (default 7 days).
This allows consumers to replay historical events.

### Why Kafka is Reliable

- **Replication** — each partition is replicated across multiple brokers
- **Persistence** — messages are written to disk (not lost on crash)
- **At-least-once delivery** — consumer commits offset only after processing
- **Horizontal scaling** — add more brokers/partitions as load grows

### Schema Registry & Avro

Raw JSON messages waste bandwidth and have no schema enforcement. In production,
we use **Avro** (binary format) + **Schema Registry** (central schema store):

```python
# Avro schema definition
taxi_trip_schema = {
    "type": "record",
    "name": "TaxiTrip",
    "fields": [
        {"name": "vendor_id",        "type": "int"},
        {"name": "pickup_datetime",  "type": "string"},
        {"name": "dropoff_datetime", "type": "string"},
        {"name": "passenger_count",  "type": "int"},
        {"name": "trip_distance",    "type": "float"},
        {"name": "total_amount",     "type": "float"},
    ]
}
```

Benefits: ~10x smaller messages, schema validation on write, backward compatibility.

---

## Tools Used

| Tool | Purpose |
|------|---------|
| Apache Kafka | Message broker / event stream |
| Confluent Schema Registry | Central Avro schema store |
| kafka-python | Python Kafka client |
| Docker Compose | Run Kafka locally |

---

## Folder Structure

```
06-stream-processing/
├── README.md
├── 1_intro/
│   └── kafka_concepts.md          # Deep-dive notes on Kafka internals
└── 2_kafka_python/
    ├── docker-compose.yml          # Kafka + Zookeeper + Schema Registry
    ├── producer.py                 # Simulates taxi trips arriving in real time
    ├── consumer.py                 # Reads and processes the trip stream
    └── requirements.txt
```

---

## How to Run

### Start Kafka with Docker

```bash
cd 2_kafka_python
docker-compose up -d

# Wait for Kafka to be ready (about 30 seconds)
docker-compose logs -f kafka | grep "started"
```

### Run the Producer (simulates live taxi trips)

```bash
pip install kafka-python confluent-kafka

python producer.py
# Sends one taxi trip event per second to the "taxi-trips" topic
```

### Run the Consumer (processes the stream)

```bash
# In a second terminal
python consumer.py
# Reads events and prints aggregated stats every 10 seconds
```

### Inspect Topics

```bash
# List topics
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# Describe topic
docker exec -it kafka kafka-topics \
  --describe --topic taxi-trips --bootstrap-server localhost:9092

# Read messages from the beginning
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic taxi-trips \
  --from-beginning
```

---

## Key Kafka Concepts Summary

```
Topic         = Named stream (like a log file that grows forever)
Partition     = Ordered sub-stream within a topic (enables parallelism)
Offset        = Position of a message within a partition
Producer      = Writes events to a topic
Consumer      = Reads events from a topic
Consumer Group = Team of consumers sharing topic partitions
Broker        = A Kafka server node
Cluster       = Multiple brokers working together
Retention     = How long Kafka keeps messages (default: 7 days)
Replication   = How many copies of each partition (default: 1, production: 3)
```
