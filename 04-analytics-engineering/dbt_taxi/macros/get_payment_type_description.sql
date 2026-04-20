{#
    Macro: get_payment_type_description
    =====================================
    Converts numeric payment_type codes to human-readable descriptions.
    Used in staging models so analysts never have to remember code meanings.

    Usage:
        {{ get_payment_type_description('payment_type') }}
    
    Returns a SQL CASE expression as a string.
#}

{% macro get_payment_type_description(payment_type_field) %}

    CASE {{ payment_type_field }}
        WHEN 1 THEN 'Credit Card'
        WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No Charge'
        WHEN 4 THEN 'Dispute'
        WHEN 5 THEN 'Unknown'
        WHEN 6 THEN 'Voided Trip'
        ELSE 'Unknown'
    END

{% endmacro %}
