{{
    config(
        materialized='table',
        partition_by={
            "field": "pickup_datetime",
            "data_type": "timestamp",
            "granularity": "day"
        },
        cluster_by=["service_type", "vendor_id"]
    )
}}

/*
    fact_trips: Combined Yellow + Green taxi trips
    
    This is the main analytical fact table. It:
    - Unions Yellow and Green taxi data into one table
    - Joins with the zones dimension for human-readable location names
    - Adds derived metrics (trip duration, speed)
    - Is partitioned by day and clustered by service_type for query performance
*/

WITH yellow AS (
    SELECT * FROM {{ ref('stg_yellow_taxi') }}
),

green AS (
    SELECT * FROM {{ ref('stg_green_taxi') }}
),

-- Combine both taxi types
all_trips AS (
    SELECT * FROM yellow
    UNION ALL
    SELECT * FROM green
),

-- Join with zones dimension
trips_with_zones AS (
    SELECT
        t.trip_id,
        t.vendor_id,
        t.service_type,
        t.pickup_datetime,
        t.dropoff_datetime,

        -- Derived metrics
        TIMESTAMP_DIFF(t.dropoff_datetime, t.pickup_datetime, MINUTE) AS trip_duration_min,
        SAFE_DIVIDE(
            t.trip_distance,
            TIMESTAMP_DIFF(t.dropoff_datetime, t.pickup_datetime, MINUTE) / 60.0
        ) AS speed_mph,

        -- Trip details
        t.passenger_count,
        t.trip_distance,
        t.ratecode_id,
        t.payment_type,
        t.payment_type_description,

        -- Location info
        t.pickup_location_id,
        pu.borough    AS pickup_borough,
        pu.zone       AS pickup_zone,
        t.dropoff_location_id,
        do_.borough   AS dropoff_borough,
        do_.zone      AS dropoff_zone,

        -- Amounts
        t.fare_amount,
        t.extra,
        t.mta_tax,
        t.tip_amount,
        t.tolls_amount,
        t.improvement_surcharge,
        t.congestion_surcharge,
        t.total_amount,

        -- Date parts for easy filtering
        DATE(t.pickup_datetime) AS pickup_date,
        EXTRACT(YEAR  FROM t.pickup_datetime) AS pickup_year,
        EXTRACT(MONTH FROM t.pickup_datetime) AS pickup_month,
        EXTRACT(HOUR  FROM t.pickup_datetime) AS pickup_hour,
        EXTRACT(DAYOFWEEK FROM t.pickup_datetime) AS pickup_day_of_week

    FROM all_trips t
    LEFT JOIN {{ ref('dim_zones') }} pu  ON t.pickup_location_id  = pu.location_id
    LEFT JOIN {{ ref('dim_zones') }} do_ ON t.dropoff_location_id = do_.location_id
)

SELECT * FROM trips_with_zones
WHERE trip_duration_min > 0
  AND trip_duration_min < 180    -- filter extreme outliers
  AND speed_mph < 120            -- filter impossible speeds
