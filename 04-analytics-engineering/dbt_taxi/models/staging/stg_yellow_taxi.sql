{{
    config(materialized='view')
}}

WITH source AS (
    SELECT * FROM {{ source('staging', 'yellow_trips') }}
),

renamed AS (
    SELECT
        -- Trip identifiers
        {{ dbt_utils.generate_surrogate_key(['VendorID', 'tpep_pickup_datetime']) }} AS trip_id,
        CAST(VendorID AS INTEGER)       AS vendor_id,

        -- Timestamps
        tpep_pickup_datetime            AS pickup_datetime,
        tpep_dropoff_datetime           AS dropoff_datetime,

        -- Trip details
        CAST(passenger_count AS INTEGER) AS passenger_count,
        CAST(trip_distance AS NUMERIC)   AS trip_distance,
        CAST(RatecodeID AS INTEGER)      AS ratecode_id,
        store_and_fwd_flag,

        -- Location IDs
        CAST(PULocationID AS INTEGER)    AS pickup_location_id,
        CAST(DOLocationID AS INTEGER)    AS dropoff_location_id,

        -- Payment
        CAST(payment_type AS INTEGER)    AS payment_type,
        {{ get_payment_type_description('payment_type') }} AS payment_type_description,

        -- Amounts
        CAST(fare_amount AS NUMERIC)            AS fare_amount,
        CAST(extra AS NUMERIC)                  AS extra,
        CAST(mta_tax AS NUMERIC)                AS mta_tax,
        CAST(tip_amount AS NUMERIC)             AS tip_amount,
        CAST(tolls_amount AS NUMERIC)           AS tolls_amount,
        CAST(improvement_surcharge AS NUMERIC)  AS improvement_surcharge,
        CAST(total_amount AS NUMERIC)           AS total_amount,
        CAST(congestion_surcharge AS NUMERIC)   AS congestion_surcharge,

        -- Taxi type flag (for combined fact table)
        'Yellow' AS service_type

    FROM source
    WHERE passenger_count > 0
      AND trip_distance > 0
      AND total_amount > 0
)

SELECT * FROM renamed
