-- Esquema de Farmaticas. Se recrea completo en cada carga.
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS drugs;

CREATE TABLE drugs (
    drug_id        INTEGER PRIMARY KEY,
    name           VARCHAR(100) NOT NULL UNIQUE,
    unit_price     INTEGER NOT NULL CHECK (unit_price > 0),
    initial_stock  INTEGER NOT NULL CHECK (initial_stock >= 0)
);

CREATE TABLE customers (
    customer_id  INTEGER PRIMARY KEY,
    full_name    VARCHAR(150) NOT NULL,
    city         VARCHAR(80) NOT NULL
);

CREATE TABLE sales (
    sale_id      INTEGER PRIMARY KEY,
    date         DATE NOT NULL,
    customer_id  INTEGER NOT NULL REFERENCES customers (customer_id),
    drug_id      INTEGER NOT NULL REFERENCES drugs (drug_id),
    quantity     INTEGER NOT NULL CHECK (quantity > 0),
    total        INTEGER NOT NULL CHECK (total > 0)
);

-- Acelera el cálculo del inventario por medicamento
CREATE INDEX idx_sales_drug_id ON sales (drug_id);