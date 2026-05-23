#!/usr/bin/env bash

set -euo pipefail

CUSTOMER_COUNT="${1:-100}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
ENV_EXAMPLE_FILE="$ROOT_DIR/.env.example"

if ! [[ "$CUSTOMER_COUNT" =~ ^[0-9]+$ ]] || [ "$CUSTOMER_COUNT" -lt 1 ] || [ "$CUSTOMER_COUNT" -gt 1000 ]; then
  echo "Usage: $0 [customer_count]"
  echo "customer_count must be a number between 1 and 1000"
  exit 1
fi

if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  set -a && . "$ENV_FILE" && set +a
elif [ -f "$ENV_EXAMPLE_FILE" ]; then
  # shellcheck disable=SC1090
  set -a && . "$ENV_EXAMPLE_FILE" && set +a
else
  echo "No .env or .env.example file found in $ROOT_DIR"
  exit 1
fi

PGUSER="${POSTGRES_USER:-postgres}"
PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"
PGDATABASE="${POSTGRES_DB:-invoice_db}"
PGHOST="${POSTGRES_HOST:-localhost}"
PGPORT="${POSTGRES_PORT:-5432}"

if [ "$PGHOST" = "db" ]; then
  PGHOST="localhost"
fi

export PGUSER PGPASSWORD PGDATABASE PGHOST PGPORT

if ! command -v psql >/dev/null 2>&1; then
  echo "psql is not installed or not available in PATH"
  exit 1
fi

if ! psql -Atqc "select 1" >/dev/null 2>&1; then
  echo "Could not connect to PostgreSQL at ${PGHOST}:${PGPORT}/${PGDATABASE}"
  echo "Make sure PostgreSQL is running, or start the Docker stack with: docker compose up -d"
  exit 1
fi

psql -v ON_ERROR_STOP=1 <<SQL
BEGIN;

-- Remove only records managed by this demo seeder so reruns stay clean.
DELETE FROM payments
WHERE "Id"::text LIKE '50000000-0000-0000-0000-%';

DELETE FROM invoice_items
WHERE "Id"::text LIKE '40000000-0000-0000-0000-%';

DELETE FROM invoices
WHERE "Id"::text LIKE '30000000-0000-0000-0000-%'
   OR "InvoiceNumber" LIKE 'DEMO-2026-%';

DELETE FROM user_businesses
WHERE "Id"::text LIKE '60000000-0000-0000-0000-%';

DELETE FROM customers
WHERE "Id"::text LIKE '20000000-0000-0000-0000-%'
   OR "Email" LIKE '%@demo.local'
   OR "Email" LIKE '%@seeded-demo.com';

DELETE FROM users
WHERE "Id"::text LIKE '10000000-0000-0000-0000-%'
   OR "Email" LIKE '%@demo.local'
   OR "Email" LIKE '%@seeded-demo.com';

DELETE FROM businesses
WHERE "Id" IN (
  '70000000-0000-0000-0000-000000000001',
  '70000000-0000-0000-0000-000000000002',
  '70000000-0000-0000-0000-000000000003'
);

INSERT INTO businesses (
  "Id", "Name", "VatNumber", "PanNumber", "Address", "Phone", "LogoUrl"
)
VALUES
  (
    '70000000-0000-0000-0000-000000000001',
    'Northwind Traders',
    'VAT-NT-2026',
    'PAN-NT-2026',
    '101 Market Street, Kathmandu',
    '9801000001',
    'https://example.com/logos/northwind.png'
  ),
  (
    '70000000-0000-0000-0000-000000000002',
    'BluePeak Consulting',
    'VAT-BP-2026',
    'PAN-BP-2026',
    '22 Riverside Avenue, Pokhara',
    '9801000002',
    'https://example.com/logos/bluepeak.png'
  ),
  (
    '70000000-0000-0000-0000-000000000003',
    'Evergreen Retail',
    'VAT-EG-2026',
    'PAN-EG-2026',
    '9 Lakeside Road, Lalitpur',
    '9801000003',
    'https://example.com/logos/evergreen.png'
  );

INSERT INTO users (
  "Id", "FullName", "Email", "Phone", "PasswordHash", "IsActive"
)
VALUES
  (
    '10000000-0000-0000-0000-000000000001',
    'Aarav Sharma',
    'aarav.sharma@seeded-demo.com',
    '9801100001',
    'demo_hash_1',
    TRUE
  ),
  (
    '10000000-0000-0000-0000-000000000002',
    'Sofia Gurung',
    'sofia.gurung@seeded-demo.com',
    '9801100002',
    'demo_hash_2',
    TRUE
  ),
  (
    '10000000-0000-0000-0000-000000000003',
    'Milan Rai',
    'milan.rai@seeded-demo.com',
    '9801100003',
    'demo_hash_3',
    TRUE
  ),
  (
    '10000000-0000-0000-0000-000000000004',
    'Priya Karki',
    'priya.karki@seeded-demo.com',
    '9801100004',
    'demo_hash_4',
    TRUE
  ),
  (
    '10000000-0000-0000-0000-000000000005',
    'Noah Adhikari',
    'noah.adhikari@seeded-demo.com',
    '9801100005',
    'demo_hash_5',
    TRUE
  );

INSERT INTO user_businesses (
  "Id", "UserId", "BusinessId", "Role"
)
VALUES
  ('60000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', '70000000-0000-0000-0000-000000000001', 'Owner'),
  ('60000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000002', '70000000-0000-0000-0000-000000000001', 'Accountant'),
  ('60000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000003', '70000000-0000-0000-0000-000000000002', 'Owner'),
  ('60000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000004', '70000000-0000-0000-0000-000000000002', 'Admin'),
  ('60000000-0000-0000-0000-000000000005', '10000000-0000-0000-0000-000000000005', '70000000-0000-0000-0000-000000000003', 'Owner'),
  ('60000000-0000-0000-0000-000000000006', '10000000-0000-0000-0000-000000000002', '70000000-0000-0000-0000-000000000003', 'Accountant'),
  ('60000000-0000-0000-0000-000000000007', '10000000-0000-0000-0000-000000000004', '70000000-0000-0000-0000-000000000001', 'Staff');

WITH numbered_customers AS (
  SELECT gs AS n
  FROM generate_series(1, ${CUSTOMER_COUNT}) AS gs
)
INSERT INTO customers (
  "Id", "BusinessId", "Name", "Phone", "Email", "Address", "VatNumber"
)
SELECT
  ('20000000-0000-0000-0000-' || lpad(n::text, 12, '0'))::uuid,
  CASE
    WHEN n % 3 = 1 THEN '70000000-0000-0000-0000-000000000001'::uuid
    WHEN n % 3 = 2 THEN '70000000-0000-0000-0000-000000000002'::uuid
    ELSE '70000000-0000-0000-0000-000000000003'::uuid
  END,
  (
    ARRAY['Aarush','Isha','Rohan','Maya','Kabir','Anika','Dev','Saanvi','Reyansh','Diya','Arjun','Nisha']
  )[((n - 1) % 12) + 1]
  || ' ' ||
  (
    ARRAY['Sharma','Gurung','Rai','Karki','Shrestha','Adhikari','Basnet','Bhandari','Thapa','Poudel','Lama','Maharjan']
  )[(floor((n - 1) / 12)::int % 12) + 1],
  '98' || lpad((10000000 + n)::text, 8, '0'),
  'customer' || lpad(n::text, 3, '0') || '@seeded-demo.com',
  (
    CASE
      WHEN n % 3 = 1 THEN 'Baneshwor, Kathmandu'
      WHEN n % 3 = 2 THEN 'Lakeside, Pokhara'
      ELSE 'Jawalakhel, Lalitpur'
    END
  ) || ' - Block ' || ((n % 9) + 1),
  'VAT-CUST-' || lpad(n::text, 4, '0')
FROM numbered_customers;

WITH invoice_seed AS (
  SELECT
    gs AS n,
    ('20000000-0000-0000-0000-' || lpad(gs::text, 12, '0'))::uuid AS customer_id,
    ('30000000-0000-0000-0000-' || lpad(gs::text, 12, '0'))::uuid AS invoice_id,
    CASE
      WHEN gs % 3 = 1 THEN '70000000-0000-0000-0000-000000000001'::uuid
      WHEN gs % 3 = 2 THEN '70000000-0000-0000-0000-000000000002'::uuid
      ELSE '70000000-0000-0000-0000-000000000003'::uuid
    END AS business_id,
    CASE
      WHEN gs % 5 = 1 THEN '10000000-0000-0000-0000-000000000001'::uuid
      WHEN gs % 5 = 2 THEN '10000000-0000-0000-0000-000000000002'::uuid
      WHEN gs % 5 = 3 THEN '10000000-0000-0000-0000-000000000003'::uuid
      WHEN gs % 5 = 4 THEN '10000000-0000-0000-0000-000000000004'::uuid
      ELSE '10000000-0000-0000-0000-000000000005'::uuid
    END AS created_by,
    CASE
      WHEN gs % 6 = 0 THEN 'Draft'
      WHEN gs % 6 = 1 THEN 'Sent'
      WHEN gs % 6 = 2 THEN 'Paid'
      WHEN gs % 6 = 3 THEN 'Partial'
      WHEN gs % 6 = 4 THEN 'Overdue'
      ELSE 'Cancelled'
    END AS status,
    round((((gs % 4) + 1) * (80 + gs * 3) - ((gs % 5) * 5))::numeric, 2) AS line_total_1,
    round((((gs % 3) + 1) * (25 + gs * 2) - ((gs % 4) * 2))::numeric, 2) AS line_total_2,
    round(((gs % 3) * 10)::numeric, 2) AS discount_amount
  FROM generate_series(1, ${CUSTOMER_COUNT}) AS gs
),
invoice_totals AS (
  SELECT
    n,
    customer_id,
    invoice_id,
    business_id,
    created_by,
    status,
    line_total_1,
    line_total_2,
    discount_amount,
    round((line_total_1 + line_total_2)::numeric, 2) AS subtotal,
    round(((line_total_1 + line_total_2) * 0.13)::numeric, 2) AS vat_amount,
    round(((line_total_1 + line_total_2) * 1.13 - discount_amount)::numeric, 2) AS total_amount
  FROM invoice_seed
)
INSERT INTO invoices (
  "Id", "BusinessId", "CustomerId", "InvoiceNumber", "Status",
  "Subtotal", "VatAmount", "DiscountAmount", "TotalAmount",
  "DueDate", "Notes", "CreatedBy"
)
SELECT
  invoice_id,
  business_id,
  customer_id,
  'DEMO-2026-' || lpad(n::text, 4, '0'),
  status::invoice_status_enum,
  subtotal,
  vat_amount,
  discount_amount,
  total_amount,
  CURRENT_DATE + ((n % 20) + 5),
  'Demo invoice for seeded dataset customer #' || lpad(n::text, 3, '0'),
  created_by
FROM invoice_totals;

WITH item_seed AS (
  SELECT
    gs AS n,
    ('30000000-0000-0000-0000-' || lpad(gs::text, 12, '0'))::uuid AS invoice_id,
    ('40000000-0000-0000-0000-' || lpad((gs * 2 - 1)::text, 12, '0'))::uuid AS item_id_1,
    ('40000000-0000-0000-0000-' || lpad((gs * 2)::text, 12, '0'))::uuid AS item_id_2,
    round((((gs % 4) + 1) * (80 + gs * 3) - ((gs % 5) * 5))::numeric, 2) AS line_total_1,
    round((((gs % 3) + 1) * (25 + gs * 2) - ((gs % 4) * 2))::numeric, 2) AS line_total_2
  FROM generate_series(1, ${CUSTOMER_COUNT}) AS gs
)
INSERT INTO invoice_items (
  "Id", "InvoiceId", "ProductName", "Quantity", "UnitPrice", "VatRate", "Discount", "LineTotal"
)
SELECT
  item_id,
  invoice_id,
  product_name,
  quantity,
  unit_price,
  vat_rate,
  discount,
  line_total
FROM (
  SELECT
    item_id_1 AS item_id,
    invoice_id,
    (
      ARRAY['Website Maintenance','Monthly Bookkeeping','Tax Advisory','UI Design Sprint','Cloud Hosting','Inventory Audit']
    )[((n - 1) % 6) + 1] AS product_name,
    ((n % 4) + 1)::numeric AS quantity,
    (80 + n * 3)::numeric(12,2) AS unit_price,
    13.00::numeric(5,2) AS vat_rate,
    ((n % 5) * 5)::numeric(12,2) AS discount,
    line_total_1 AS line_total
  FROM item_seed

  UNION ALL

  SELECT
    item_id_2 AS item_id,
    invoice_id,
    (
      ARRAY['Support Retainer','Analytics Setup','POS Integration','SEO Content Pack','Training Session','Mobile App QA']
    )[((n - 1) % 6) + 1] AS product_name,
    ((n % 3) + 1)::numeric AS quantity,
    (25 + n * 2)::numeric(12,2) AS unit_price,
    13.00::numeric(5,2) AS vat_rate,
    ((n % 4) * 2)::numeric(12,2) AS discount,
    line_total_2 AS line_total
  FROM item_seed
) items;

WITH payment_seed AS (
  SELECT
    gs AS n,
    ('30000000-0000-0000-0000-' || lpad(gs::text, 12, '0'))::uuid AS invoice_id,
    ('50000000-0000-0000-0000-' || lpad(gs::text, 12, '0'))::uuid AS payment_id,
    CASE
      WHEN gs % 3 = 1 THEN '70000000-0000-0000-0000-000000000001'::uuid
      WHEN gs % 3 = 2 THEN '70000000-0000-0000-0000-000000000002'::uuid
      ELSE '70000000-0000-0000-0000-000000000003'::uuid
    END AS business_id,
    CASE
      WHEN gs % 6 = 0 THEN 'Draft'
      WHEN gs % 6 = 1 THEN 'Sent'
      WHEN gs % 6 = 2 THEN 'Paid'
      WHEN gs % 6 = 3 THEN 'Partial'
      WHEN gs % 6 = 4 THEN 'Overdue'
      ELSE 'Cancelled'
    END AS invoice_status,
    round((((((gs % 4) + 1) * (80 + gs * 3) - ((gs % 5) * 5))
      + (((gs % 3) + 1) * (25 + gs * 2) - ((gs % 4) * 2))) * 1.13 - ((gs % 3) * 10))::numeric, 2) AS total_amount
  FROM generate_series(1, ${CUSTOMER_COUNT}) AS gs
)
INSERT INTO payments (
  "Id", "InvoiceId", "BusinessId", "Amount", "PaymentDate", "PaymentMethod", "Status", "Reference"
)
SELECT
  payment_id,
  invoice_id,
  business_id,
  CASE
    WHEN invoice_status = 'Paid' THEN total_amount
    WHEN invoice_status = 'Partial' THEN round((total_amount * 0.50)::numeric, 2)
    WHEN invoice_status IN ('Sent', 'Overdue') THEN round((total_amount * 0.30)::numeric, 2)
  END,
  CURRENT_DATE - ((n % 12) + 1),
  CASE
    WHEN n % 4 = 1 THEN 'Bank'
    WHEN n % 4 = 2 THEN 'Cash'
    WHEN n % 4 = 3 THEN 'Mobile'
    ELSE 'Cheque'
  END::payment_method_enum,
  CASE
    WHEN invoice_status IN ('Paid', 'Partial') THEN 'Settled'
    WHEN invoice_status IN ('Sent', 'Overdue') THEN 'Pending'
  END::payment_status_enum,
  'PAY-DEMO-' || lpad(n::text, 5, '0')
FROM payment_seed
WHERE invoice_status IN ('Sent', 'Paid', 'Partial', 'Overdue');

COMMIT;
SQL

echo "Seeded realistic demo data successfully."
echo "Customers: ${CUSTOMER_COUNT}"
echo "Invoices: ${CUSTOMER_COUNT}"
echo "Invoice items: $(( CUSTOMER_COUNT * 2 ))"
echo "Payments: roughly $(( CUSTOMER_COUNT * 4 / 6 ))"
echo
echo "Preview with:"
echo "  ./scripts/show_sample_data.sh 15"
