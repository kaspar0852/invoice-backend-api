#!/usr/bin/env bash

set -euo pipefail

LIMIT="${1:-10}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
ENV_EXAMPLE_FILE="$ROOT_DIR/.env.example"

if ! [[ "$LIMIT" =~ ^[0-9]+$ ]] || [ "$LIMIT" -lt 1 ] || [ "$LIMIT" -gt 15 ]; then
  echo "Usage: $0 [limit]"
  echo "limit must be a number between 1 and 15"
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

print_section() {
  local title="$1"
  local query="$2"

  printf '\n%s\n' "============================================================"
  printf '%s\n' "$title"
  printf '%s\n' "============================================================"

  psql \
    --pset=border=2 \
    --pset=null='NULL' \
    --pset=expanded=auto \
    -P pager=off \
    -c "$query"
}

print_section "USERS" \
  "SELECT
      u.\"Id\" AS user_id,
      u.\"FullName\" AS full_name,
      u.\"Email\" AS email,
      u.\"Phone\" AS phone,
      u.\"IsActive\" AS is_active,
      u.\"CreatedAt\" AS created_at
   FROM users u
   ORDER BY u.\"CreatedAt\" DESC NULLS LAST
   LIMIT $LIMIT;"

print_section "BUSINESSES" \
  "SELECT
      b.\"Id\" AS business_id,
      b.\"Name\" AS business_name,
      b.\"VatNumber\" AS vat_number,
      b.\"PanNumber\" AS pan_number,
      b.\"Phone\" AS phone,
      b.\"Address\" AS address,
      b.\"CreatedAt\" AS created_at
   FROM businesses b
   ORDER BY b.\"CreatedAt\" DESC NULLS LAST
   LIMIT $LIMIT;"

print_section "USER_BUSINESSES" \
  "SELECT
      ub.\"Id\" AS membership_id,
      u.\"FullName\" AS user_name,
      u.\"Email\" AS user_email,
      b.\"Name\" AS business_name,
      ub.\"Role\" AS role,
      ub.\"CreatedAt\" AS joined_at
   FROM user_businesses ub
   JOIN users u ON u.\"Id\" = ub.\"UserId\"
   JOIN businesses b ON b.\"Id\" = ub.\"BusinessId\"
   ORDER BY ub.\"CreatedAt\" DESC NULLS LAST
   LIMIT $LIMIT;"

print_section "CUSTOMERS" \
  "SELECT
      c.\"Id\" AS customer_id,
      c.\"Name\" AS customer_name,
      c.\"Email\" AS email,
      c.\"Phone\" AS phone,
      c.\"VatNumber\" AS vat_number,
      b.\"Name\" AS business_name,
      c.\"CreatedAt\" AS created_at
   FROM customers c
   JOIN businesses b ON b.\"Id\" = c.\"BusinessId\"
   ORDER BY c.\"CreatedAt\" DESC NULLS LAST
   LIMIT $LIMIT;"

print_section "INVOICES" \
  "SELECT
      i.\"Id\" AS invoice_id,
      i.\"InvoiceNumber\" AS invoice_number,
      b.\"Name\" AS business_name,
      c.\"Name\" AS customer_name,
      COALESCE(u.\"FullName\", 'Unknown') AS created_by,
      i.\"Status\" AS status,
      i.\"Subtotal\" AS subtotal,
      i.\"VatAmount\" AS vat_amount,
      i.\"DiscountAmount\" AS discount_amount,
      i.\"TotalAmount\" AS total_amount,
      i.\"DueDate\" AS due_date,
      i.\"CreatedAt\" AS created_at
   FROM invoices i
   JOIN businesses b ON b.\"Id\" = i.\"BusinessId\"
   JOIN customers c ON c.\"Id\" = i.\"CustomerId\"
   LEFT JOIN users u ON u.\"Id\" = i.\"CreatedBy\"
   ORDER BY i.\"CreatedAt\" DESC NULLS LAST
   LIMIT $LIMIT;"

print_section "INVOICE_ITEMS" \
  "SELECT
      ii.\"Id\" AS item_id,
      i.\"InvoiceNumber\" AS invoice_number,
      c.\"Name\" AS customer_name,
      ii.\"ProductName\" AS product_name,
      ii.\"Quantity\" AS quantity,
      ii.\"UnitPrice\" AS unit_price,
      ii.\"VatRate\" AS vat_rate,
      ii.\"Discount\" AS discount,
      ii.\"LineTotal\" AS line_total
   FROM invoice_items ii
   JOIN invoices i ON i.\"Id\" = ii.\"InvoiceId\"
   JOIN customers c ON c.\"Id\" = i.\"CustomerId\"
   ORDER BY i.\"CreatedAt\" DESC NULLS LAST, ii.\"Id\" DESC
   LIMIT $LIMIT;"

print_section "PAYMENTS" \
  "SELECT
      p.\"Id\" AS payment_id,
      b.\"Name\" AS business_name,
      c.\"Name\" AS customer_name,
      i.\"InvoiceNumber\" AS invoice_number,
      p.\"Amount\" AS amount,
      p.\"PaymentMethod\" AS payment_method,
      p.\"Status\" AS payment_status,
      p.\"Reference\" AS reference,
      p.\"PaymentDate\" AS payment_date,
      p.\"CreatedAt\" AS created_at
   FROM payments p
   JOIN invoices i ON i.\"Id\" = p.\"InvoiceId\"
   JOIN customers c ON c.\"Id\" = i.\"CustomerId\"
   JOIN businesses b ON b.\"Id\" = p.\"BusinessId\"
   ORDER BY p.\"CreatedAt\" DESC NULLS LAST
   LIMIT $LIMIT;"

print_section "BUSINESS SNAPSHOT" \
  "SELECT
      b.\"Name\" AS business_name,
      COALESCE(c.customer_count, 0) AS customers,
      COALESCE(i.invoice_count, 0) AS invoices,
      COALESCE(p.payment_count, 0) AS payments,
      COALESCE(i.total_invoiced, 0) AS total_invoiced,
      COALESCE(p.total_paid, 0) AS total_paid
   FROM businesses b
   LEFT JOIN (
      SELECT
          \"BusinessId\",
          COUNT(*) AS customer_count
      FROM customers
      GROUP BY \"BusinessId\"
   ) c ON c.\"BusinessId\" = b.\"Id\"
   LEFT JOIN (
      SELECT
          \"BusinessId\",
          COUNT(*) AS invoice_count,
          SUM(\"TotalAmount\") AS total_invoiced
      FROM invoices
      GROUP BY \"BusinessId\"
   ) i ON i.\"BusinessId\" = b.\"Id\"
   LEFT JOIN (
      SELECT
          \"BusinessId\",
          COUNT(*) AS payment_count,
          SUM(CASE WHEN \"Status\" = 'Settled' THEN \"Amount\" ELSE 0 END) AS total_paid
      FROM payments
      GROUP BY \"BusinessId\"
   ) p ON p.\"BusinessId\" = b.\"Id\"
   ORDER BY b.\"Name\"
   LIMIT $LIMIT;"
