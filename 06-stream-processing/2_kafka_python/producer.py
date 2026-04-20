"""
Kafka Producer — Simulates Real-Time Taxi Trips
================================================
Reads from the NYC taxi Parquet file and sends each trip
as a JSON event to the "taxi-trips" Kafka topic.

Simulates a live system where taxis complete trips and send
data to a central stream in real time.

Run: python producer.py
"""

import json
import time
import random
import argparse
from datetime import datetime

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable


TOPIC_NAME      = "taxi-trips"
BOOTSTRAP_SERVER = "localhost:9092"


def create_producer() -> KafkaProducer:
    """Create and return a Kafka producer with JSON serialization."""
    retries = 5
    for attempt in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=[BOOTSTRAP_SERVER],
                # Serialize messages as JSON bytes
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: str(k).encode("utf-8"),
                # Reliability settings
                acks="all",              # Wait for all replicas to confirm
                retries=3,
                linger_ms=10,           # Batch messages for 10ms before sending
            )
            print(f"Connected to Kafka at {BOOTSTRAP_SERVER}")
            return producer
        except NoBrokersAvailable:
            wait = 2 ** attempt
            print(f"Kafka not ready, retrying in {wait}s... (attempt {attempt+1}/{retries})")
            time.sleep(wait)
    raise RuntimeError("Could not connect to Kafka after multiple retries")


def generate_taxi_trip(trip_id: int) -> dict:
    """
    Generate a realistic synthetic taxi trip event.
    In a real system, this would come from taxi meters / GPS devices.
    """
    vendors = [1, 2]
    zones   = list(range(1, 266))  # NYC has 265 taxi zones
    payment_types = [1, 2, 1, 1]  # Weight toward credit card

    distance  = round(random.uniform(0.5, 25.0), 2)
    fare      = round(2.5 + distance * 2.5, 2)
    tip       = round(fare * random.uniform(0, 0.3), 2)
    total     = round(fare + tip + 0.5, 2)  # + MTA tax

    now = datetime.utcnow()

    return {
        "trip_id":           trip_id,
        "vendor_id":         random.choice(vendors),
        "pickup_datetime":   now.isoformat(),
        "dropoff_datetime":  now.isoformat(),  # simplified
        "passenger_count":   random.randint(1, 4),
        "trip_distance":     distance,
        "pu_location_id":    random.choice(zones),
        "do_location_id":    random.choice(zones),
        "payment_type":      random.choice(payment_types),
        "fare_amount":       fare,
        "tip_amount":        tip,
        "total_amount":      total,
        "timestamp":         now.isoformat(),
    }


def send_trip(producer: KafkaProducer, trip: dict) -> None:
    """Send a single trip event to Kafka."""
    # Use vendor_id as partition key — all trips from same vendor
    # go to the same partition (ordering guaranteed per vendor)
    future = producer.send(
        topic=TOPIC_NAME,
        key=trip["vendor_id"],
        value=trip,
    )
    record_metadata = future.get(timeout=10)
    print(
        f"  Sent trip {trip['trip_id']:5d} | "
        f"Vendor {trip['vendor_id']} | "
        f"${trip['total_amount']:6.2f} | "
        f"Partition {record_metadata.partition}, Offset {record_metadata.offset}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count",    type=int,   default=0,   help="0 = run forever")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between messages")
    args = parser.parse_args()

    producer = create_producer()
    print(f"\nProducing to topic '{TOPIC_NAME}' (interval: {args.interval}s)")
    print("Press Ctrl+C to stop\n")

    trip_id = 1
    try:
        while True:
            trip = generate_taxi_trip(trip_id)
            send_trip(producer, trip)
            trip_id += 1

            if args.count and trip_id > args.count:
                break

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\nStopped after sending {trip_id - 1} trips")
    finally:
        producer.flush()
        producer.close()
        print("Producer closed.")


if __name__ == "__main__":
    main()
