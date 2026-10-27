WITH base AS (
    SELECT customer_id,cast(julianday(:asof)-julianday(max(invoice_date)) AS INT) AS recency_days,
           count(*) AS frequency,sum(revenue) AS monetary_gbp
    FROM orders WHERE customer_id IS NOT NULL GROUP BY customer_id
)
SELECT *,
    CASE WHEN recency_days<=30 THEN 5 WHEN recency_days<=60 THEN 4 WHEN recency_days<=90 THEN 3
         WHEN recency_days<=180 THEN 2 ELSE 1 END AS recency_score,
    CASE WHEN frequency>=10 THEN 5 WHEN frequency>=5 THEN 4 WHEN frequency>=3 THEN 3
         WHEN frequency>=2 THEN 2 ELSE 1 END AS frequency_score,
    CASE WHEN monetary_gbp>=1000 THEN 5 WHEN monetary_gbp>=500 THEN 4 WHEN monetary_gbp>=250 THEN 3
         WHEN monetary_gbp>=100 THEN 2 ELSE 1 END AS monetary_score
FROM base ORDER BY customer_id;
