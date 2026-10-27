WITH customer_month AS (
    SELECT DISTINCT customer_id,substr(invoice_date,1,7) AS month
    FROM orders WHERE customer_id IS NOT NULL
), assigned AS (
    SELECT *,min(month) OVER (PARTITION BY customer_id) AS cohort FROM customer_month
), sizes AS (
    SELECT cohort,count(DISTINCT customer_id) AS cohort_customers FROM assigned GROUP BY cohort
), active AS (
    SELECT cohort,month,count(*) AS active_customers FROM assigned GROUP BY cohort,month
)
SELECT s.cohort,m.month,
       (cast(substr(m.month,1,4) AS INT)-cast(substr(s.cohort,1,4) AS INT))*12
       +cast(substr(m.month,6,2) AS INT)-cast(substr(s.cohort,6,2) AS INT) AS month_age,
       s.cohort_customers,coalesce(a.active_customers,0) AS active_customers,
       1.0*coalesce(a.active_customers,0)/s.cohort_customers AS repeat_purchase_rate
FROM sizes s CROSS JOIN months m
LEFT JOIN active a ON a.cohort=s.cohort AND a.month=m.month
WHERE m.month>=s.cohort ORDER BY s.cohort,m.month;
