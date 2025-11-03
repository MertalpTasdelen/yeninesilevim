import pandas as pd

# Load the Excel file
file_path = "C:/Users/Taşdelen/Downloads/guncel_urunler.xlsx"  # Change this to your file's path
df = pd.read_excel(file_path)

# Ensure your column names match
df.columns = ["name", "barcode", "purchase_barcode","purchase_price", "selling_price", "commution","stock", "image_url"]

# Table name in the database
table_name = "inventory_product"

# Create SQL insert statements
insert_statements = []
for _, row in df.iterrows():
    values = (
        row["name"], 
        row["barcode"],
        row["purchase_barcode"], 
        row["purchase_price"],
        row["selling_price"], 
        row["commution"],
        row["stock"],
        row["image_url"]
    )
    statement = f"INSERT INTO {table_name} (name, barcode, purchase_barcode, purchase_price, selling_price, commution, stock, image_url) VALUES {values};"
    insert_statements.append(statement)

# Save to a .sql file
sql_file_path = "insert_products.sql"
with open(sql_file_path, "w", encoding="utf-8") as file:
    file.write("\n".join(insert_statements))

print(f"SQL file generated at: {sql_file_path}")