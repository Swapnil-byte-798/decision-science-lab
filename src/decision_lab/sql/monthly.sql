WITH totals AS (
    SELECT substr(invoice_date,1,7) AS month,count(*) AS orders,
           count(DISTINCT customer_id) AS identified_customers,sum(revenue) AS gross_sales_gbp
    FROM orders GROUP BY substr(invoice_date,1,7)
), lagged AS (
    SELECT *,lag(gross_sales_gbp) OVER (ORDER BY month) AS prior_gross_sales_gbp FROM totals
)
SELECT *,gross_sales_gbp/nullif(orders,0) AS average_order_value_gbp,
       gross_sales_gbp/nullif(prior_gross_sales_gbp,0)-1 AS mom_growth
FROM lagged ORDER BY month;
