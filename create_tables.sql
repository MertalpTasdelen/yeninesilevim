-- Create the table
CREATE TABLE inventory_product (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    barcode VARCHAR(255) UNIQUE NOT NULL,
    purchase_barcode VARCHAR
    purchase_price DECIMAL(10, 2) NOT NULL,
    selling_price DECIMAL(10, 2) NOT NULL,
    commution DECIMAL(10, 2) NOT NULL,
    stock INTEGER NOT NULL,
    image_url VARCHAR(1024),  -- Increased length for image URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
CREATE TRIGGER update_inventory_product_updated_at
BEFORE UPDATE ON inventory_product
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Create the profit_calculator table
CREATE TABLE profits (
    id SERIAL PRIMARY KEY,
    barcode VARCHAR(50) REFERENCES inventory_product(barcode) ON DELETE CASCADE,
    selling_price DECIMAL(10, 2) NOT NULL,
    commution DECIMAL(10, 2) NOT NULL,
    purchase_cost DECIMAL(10, 2) NOT NULL,
    shipping_cost DECIMAL(10, 2) NOT NULL,
    packaging_cost DECIMAL(10, 2) NOT NULL,
    other_costs DECIMAL(10, 2) NOT NULL,
    vat_rate DECIMAL(5, 2) NOT NULL,
    paid_commission DECIMAL(10, 2),
    paid_vat DECIMAL(10, 2),
    total_cost DECIMAL(10, 2),
    net_profit DECIMAL(10, 2),
    profit_margin DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the trigger function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger to update the updated_at column on update
CREATE TRIGGER update_profit_calculator_updated_at
BEFORE UPDATE ON profits
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();