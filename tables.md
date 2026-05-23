# **AI Accounting Platform — Database Design (Multi-Tenant SaaS)**

---

# **1\. USERS TABLE**

| Column | Type | Constraints | Description |
| ----- | ----- | ----- | ----- |
| Id | UUID | PK | Unique user ID |
| FullName | VARCHAR | NOT NULL | User full name |
| Email | VARCHAR | UNIQUE | Login email |
| Phone | VARCHAR | NULL | Phone number |
| PasswordHash | TEXT | NOT NULL | Encrypted password |
| IsActive | BOOLEAN | DEFAULT true | Account status |
| CreatedAt | TIMESTAMP | DEFAULT now() | Account creation time |

---

# **2\. BUSINESSES TABLE (TENANT)**

| Column | Type | Constraints | Description |
| ----- | ----- | ----- | ----- |
| Id | UUID | PK | Business ID |
| Name | VARCHAR | NOT NULL | Business name |
| VatNumber | VARCHAR | NULL | VAT registration number |
| PanNumber | VARCHAR | NULL | PAN number |
| Address | TEXT | NULL | Business address |
| Phone | VARCHAR | NULL | Contact number |
| LogoUrl | TEXT | NULL | Business logo |
| CreatedAt | TIMESTAMP | DEFAULT now() | Created time |

---

# **3\. USER\_BUSINESSES (MULTI-TENANCY MAPPING)**

| Column | Type | Constraints | Description |
| ----- | ----- | ----- | ----- |
| Id | UUID | PK | Mapping ID |
| UserId | UUID | FK → Users.Id | User reference |
| BusinessId | UUID | FK → Businesses.Id | Business reference |
| Role | ENUM | Owner/Admin/Staff/Accountant | User role in business |
| CreatedAt | TIMESTAMP | DEFAULT now() | Joined time |

---

# **4\. CUSTOMERS TABLE**

| Column | Type | Constraints | Description |
| ----- | ----- | ----- | ----- |
| Id | UUID | PK | Customer ID |
| BusinessId | UUID | FK → Businesses.Id | Tenant reference |
| Name | VARCHAR | NOT NULL | Customer name |
| Phone | VARCHAR | NULL | Contact |
| Email | VARCHAR | NULL | Email |
| Address | TEXT | NULL | Address |
| VatNumber | VARCHAR | NULL | VAT number |
| CreatedAt | TIMESTAMP | DEFAULT now() | Created time |

---

# **5\. INVOICES TABLE**

| Column | Type | Constraints | Description |
| ----- | ----- | ----- | ----- |
| Id | UUID | PK | Invoice ID |
| BusinessId | UUID | FK → Businesses.Id | Tenant reference |
| CustomerId | UUID | FK → Customers.Id | Customer reference |
| InvoiceNumber | VARCHAR | UNIQUE | Invoice number |
| Status | ENUM | Draft/Sent/Paid/Partial/Overdue/Cancelled | Invoice state |
| Subtotal | DECIMAL | NOT NULL | Before tax |
| VatAmount | DECIMAL | NOT NULL | VAT value |
| DiscountAmount | DECIMAL | NULL | Discount applied |
| TotalAmount | DECIMAL | NOT NULL | Final amount |
| DueDate | DATE | NULL | Payment due date |
| Notes | TEXT | NULL | Extra notes |
| CreatedBy | UUID | FK → Users.Id | Creator |
| CreatedAt | TIMESTAMP | DEFAULT now() | Created time |

---

# 

# **6\. INVOICE\_ITEMS TABLE**

| Column | Type | Constraints | Description |
| ----- | ----- | ----- | ----- |
| Id | UUID | PK | Item ID |
| InvoiceId | UUID | FK → Invoices.Id | Invoice reference |
| ProductName | VARCHAR | NOT NULL | Item name |
| Quantity | DECIMAL | NOT NULL | Quantity |
| UnitPrice | DECIMAL | NOT NULL | Price per unit |
| VatRate | DECIMAL | NULL | VAT % |
| Discount | DECIMAL | NULL | Discount |
| LineTotal | DECIMAL | NOT NULL | Total per item |

---

# **7\. PAYMENTS TABLE**

| Column | Type | Constraints | Description |
| ----- | ----- | ----- | ----- |
| Id | UUID | PK | Payment ID |
| InvoiceId | UUID | FK → Invoices.Id | Invoice reference |
| BusinessId | UUID | FK → Businesses.Id | Tenant reference |
| Amount | DECIMAL | NOT NULL | Paid amount |
| PaymentDate | DATE | NOT NULL | Payment date |
| PaymentMethod | ENUM | Cash/Bank/Mobile/Cheque | Payment type |
| Status | ENUM | Pending/Settled/Failed/Refunded | Payment state |
| Reference | VARCHAR | NULL | Transaction reference |
| CreatedAt | TIMESTAMP | DEFAULT now() | Record time |

---

