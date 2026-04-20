# Module 6 Homework — Stream Processing with Kafka

## Setup

Kafka running locally via Docker Compose.
Producer sending synthetic taxi trips, consumer reading and aggregating.

---

## Question 1: What is a Kafka topic?

**Answer:** A topic is a named, ordered, persistent log of events.
Producers write to it, consumers read from it. It's split into partitions for
parallelism and replicated across brokers for fault tolerance.

---

## Question 2: What happens if a consumer crashes before committing its offset?

**Answer:** With `enable_auto_commit=False` (manual commits), the consumer will
**re-read** all uncommitted messages from the last committed offset when it restarts.
This is "at-least-once" delivery — the same message might be processed twice,
so consumers should be **idempotent** (processing the same message twice produces the same result).

---

## Question 3: What is the role of the Consumer Group?

**Answer:** A consumer group allows multiple consumers to share the work of reading
a topic. Each partition is assigned to exactly one consumer in the group.

If you have 3 partitions and 3 consumers in the same group:
- Consumer 1 reads Partition 0
- Consumer 2 reads Partition 1  
- Consumer 3 reads Partition 2

If Consumer 2 crashes, Kafka **rebalances** — Partition 1 is reassigned to
Consumer 1 or Consumer 3 automatically.

---

## Question 4: What is the output of the producer after 10 messages?

Running `python producer.py --count 10 --interval 0`:

```
Sent trip     1 | Vendor 1 | $ 12.34 | Partition 0, Offset 0
Sent trip     2 | Vendor 2 | $  8.91 | Partition 1, Offset 0
Sent trip     3 | Vendor 1 | $ 22.10 | Partition 0, Offset 1
...
Sent trip    10 | Vendor 2 | $ 15.50 | Partition 1, Offset 4
```

Notice: all Vendor 1 trips go to Partition 0, Vendor 2 to Partition 1 —
because we use `vendor_id` as the partition key. This guarantees **ordering
per vendor**.

---

## Question 5: What is the difference between `auto_offset_reset="earliest"` vs `"latest"`?

| Setting | Behaviour |
|---------|-----------|
| `"earliest"` | Start from the very first message in the topic |
| `"latest"` | Start from the next new message (skip all existing) |

- Use `"earliest"` to replay all history (e.g., backfill, debugging)
- Use `"latest"` for production consumers that only care about new events

---

## Key Takeaways

1. **Kafka decouples producers and consumers** — the taxi system writes events
   without knowing which downstream systems will consume them. We can add a
   new consumer (e.g., fraud detector) without touching the producer.

2. **Partition keys control ordering** — using `vendor_id` as a key ensures all
   trips from the same vendor are ordered within their partition.

3. **Manual offset commits = reliability** — auto-commit can skip messages if the
   consumer crashes between committing and processing. Manual commit only after
   successful processing = no data loss.

4. **Retention enables replay** — Kafka kept all our messages for 7 days. If the
   consumer had a bug, we could fix it and reprocess from the beginning.

5. **Stream → Batch boundary** — in real pipelines, a Kafka consumer would write
   events to GCS (data lake). Then our batch pipeline (Spark/dbt) would pick them
   up for historical analysis. This is the **Lambda Architecture** pattern.
