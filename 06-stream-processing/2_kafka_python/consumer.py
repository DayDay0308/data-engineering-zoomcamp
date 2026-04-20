"""
Kafka Consumer — Real-Time Taxi Trip Processor
================================================
Reads taxi trip events from the "taxi-trips" topic and computes
running aggregates: total trips, revenue, avg fare per vendor.

Prints a live dashboard every N messages.

Run: python consumer.py
"""

import json
import signal
import sys
from collections import defaultdict
from datetime import datetime

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable


TOPIC_NAME       = "taxi-trips"
BOOTSTRAP_SERVER = "localhost:9092"
GROUP_ID         = "taxi-analytics-group"
REPORT_EVERY     = 10   # print stats every N messages


def create_consumer() -> KafkaConsumer:
    """Create and return a Kafka consumer."""
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=[BOOTSTRAP_SERVER],
        group_id=GROUP_ID,
        # Deserialize JSON messages
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: int(k.decode("utf-8")) if k else None,
        # Start from the beginning if no committed offset exists
        auto_offset_reset="earliest",
        # Commit offsets manually for reliability
        enable_auto_commit=False,
    )
    print(f"Consumer connected | Topic: {TOPIC_NAME} | Group: {GROUP_ID}")
    return consumer


class StreamAggregator:
    """Maintains running aggregates over the trip stream."""

    def __init__(self):
        self.total_trips    = 0
        self.total_revenue  = 0.0
        self.vendor_stats   = defaultdict(lambda: {"trips": 0, "revenue": 0.0})
        self.zone_trips     = defaultdict(int)
        self.start_time     = datetime.utcnow()

    def update(self, trip: dict) -> None:
        self.total_trips   += 1
        self.total_revenue += trip["total_amount"]

        vendor = trip["vendor_id"]
        self.vendor_stats[vendor]["trips"]   += 1
        self.vendor_stats[vendor]["revenue"] += trip["total_amount"]

        self.zone_trips[trip["pu_location_id"]] += 1

    def print_dashboard(self) -> None:
        elapsed = (datetime.utcnow() - self.start_time).seconds
        rate = self.total_trips / max(elapsed, 1)

        print("\n" + "=" * 55)
        print(f"  LIVE DASHBOARD  |  {datetime.utcnow().strftime('%H:%M:%S')}")
        print("=" * 55)
        print(f"  Total trips    : {self.total_trips:,}")
        print(f"  Total revenue  : ${self.total_revenue:,.2f}")
        print(f"  Avg fare       : ${self.total_revenue / max(self.total_trips, 1):.2f}")
        print(f"  Throughput     : {rate:.1f} trips/sec")
        print()
        print("  By Vendor:")
        for vendor_id, stats in sorted(self.vendor_stats.items()):
            avg = stats["revenue"] / max(stats["trips"], 1)
            print(f"    Vendor {vendor_id}: "
                  f"{stats['trips']:,} trips | "
                  f"${stats['revenue']:,.2f} revenue | "
                  f"${avg:.2f} avg")
        print()
        top_zones = sorted(self.zone_trips.items(), key=lambda x: x[1], reverse=True)[:5]
        print("  Top 5 Pickup Zones:")
        for zone_id, count in top_zones:
            print(f"    Zone {zone_id:3d}: {count:,} trips")
        print("=" * 55)


def main():
    consumer = create_consumer()
    aggregator = StreamAggregator()

    # Graceful shutdown on Ctrl+C
    def shutdown(sig, frame):
        print("\n\nShutting down consumer...")
        aggregator.print_dashboard()
        consumer.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    print(f"\nListening for trips... (reporting every {REPORT_EVERY} messages)")
    print("Press Ctrl+C to stop\n")

    for message in consumer:
        trip = message.value
        aggregator.update(trip)

        # Log each message
        print(
            f"  Received trip {trip['trip_id']:5d} | "
            f"Vendor {trip['vendor_id']} | "
            f"${trip['total_amount']:6.2f} | "
            f"Partition {message.partition}, Offset {message.offset}"
        )

        # Print dashboard every N messages
        if aggregator.total_trips % REPORT_EVERY == 0:
            aggregator.print_dashboard()

        # Manually commit the offset after successful processing
        # This ensures we don't skip messages on restart
        consumer.commit()


if __name__ == "__main__":
    main()
