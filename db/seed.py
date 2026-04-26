"""
Seed script — creates db/sample.db with realistic e-commerce data.
Run: python db/seed.py
"""
import os
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "sample.db")

CATEGORIES = ["Electronics", "Clothing", "Books", "Home & Garden", "Sports", "Toys"]
REGIONS = ["North", "South", "East", "West", "Central"]
FIRST_NAMES = ["Alice", "Bob", "Carol", "David", "Eva", "Frank", "Grace", "Henry",
               "Iris", "Jack", "Karen", "Leo", "Mia", "Noah", "Olivia", "Paul"]
LAST_NAMES  = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
               "Miller", "Davis", "Wilson", "Moore", "Taylor", "Anderson"]


def random_date(start: datetime, end: datetime) -> str:
    delta = end - start
    return (start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))).strftime("%Y-%m-%d")


def seed():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed old DB at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # ── Tables ────────────────────────────────────────────────────────────────
    cur.executescript("""
    CREATE TABLE customers (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name  TEXT NOT NULL,
        last_name   TEXT NOT NULL,
        email       TEXT UNIQUE NOT NULL,
        age         INTEGER,
        region      TEXT,
        signup_date TEXT
    );

    CREATE TABLE products (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        category    TEXT NOT NULL,
        price       REAL NOT NULL,
        cost        REAL NOT NULL,
        stock       INTEGER DEFAULT 0
    );

    CREATE TABLE orders (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id  INTEGER NOT NULL REFERENCES customers(id),
        order_date   TEXT NOT NULL,
        status       TEXT NOT NULL DEFAULT 'completed',
        total_amount REAL NOT NULL
    );

    CREATE TABLE order_items (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id   INTEGER NOT NULL REFERENCES orders(id),
        product_id INTEGER NOT NULL REFERENCES products(id),
        quantity   INTEGER NOT NULL,
        unit_price REAL NOT NULL
    );
    """)

    # ── Customers (200) ───────────────────────────────────────────────────────
    customers = []
    for i in range(1, 201):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        email = f"{fn.lower()}.{ln.lower()}{i}@example.com"
        age = random.randint(18, 70)
        region = random.choice(REGIONS)
        signup = random_date(datetime(2020, 1, 1), datetime(2023, 12, 31))
        customers.append((fn, ln, email, age, region, signup))

    cur.executemany(
        "INSERT INTO customers (first_name, last_name, email, age, region, signup_date) VALUES (?,?,?,?,?,?)",
        customers,
    )

    # ── Products (50) ─────────────────────────────────────────────────────────
    product_templates = [
        ("Laptop Pro 15",        "Electronics", 1299.99, 750.00),
        ("Wireless Headphones",  "Electronics",  149.99,  55.00),
        ("Smartwatch X2",        "Electronics",  299.99, 110.00),
        ("USB-C Hub",            "Electronics",   49.99,  15.00),
        ("Mechanical Keyboard",  "Electronics",   89.99,  30.00),
        ("Running Shoes",        "Sports",        119.99,  45.00),
        ("Yoga Mat",             "Sports",         34.99,  10.00),
        ("Dumbbell Set",         "Sports",         79.99,  30.00),
        ("Water Bottle",         "Sports",         24.99,   6.00),
        ("Protein Powder",       "Sports",         49.99,  18.00),
        ("Python Cookbook",      "Books",          39.99,   8.00),
        ("Deep Learning",        "Books",          59.99,  12.00),
        ("The Pragmatic Prog.",  "Books",          44.99,   9.00),
        ("Clean Code",           "Books",          34.99,   7.00),
        ("Design Patterns",      "Books",          49.99,  10.00),
        ("Linen Shirt",          "Clothing",       59.99,  18.00),
        ("Slim Jeans",           "Clothing",       79.99,  22.00),
        ("Wool Sweater",         "Clothing",       99.99,  32.00),
        ("Summer Dress",         "Clothing",       69.99,  20.00),
        ("Puffer Jacket",        "Clothing",      139.99,  50.00),
        ("Coffee Maker",         "Home & Garden", 129.99,  45.00),
        ("Air Purifier",         "Home & Garden", 199.99,  75.00),
        ("Desk Lamp",            "Home & Garden",  39.99,  12.00),
        ("Indoor Plant Kit",     "Home & Garden",  29.99,   8.00),
        ("Throw Blanket",        "Home & Garden",  49.99,  15.00),
        ("LEGO Classic Set",     "Toys",           59.99,  22.00),
        ("RC Car",               "Toys",           89.99,  35.00),
        ("Board Game",           "Toys",           44.99,  14.00),
        ("Puzzle 1000pc",        "Toys",           24.99,   7.00),
        ("Stuffed Animal",       "Toys",           19.99,   5.00),
    ]
    # Pad to 50 products with slight variations
    products = list(product_templates)
    for name, cat, price, cost in product_templates:
        variation = (f"{name} v2", cat, round(price * 0.9, 2), round(cost * 0.9, 2))
        products.append(variation)
        if len(products) >= 50:
            break

    for p in products[:50]:
        stock = random.randint(0, 500)
        cur.execute(
            "INSERT INTO products (name, category, price, cost, stock) VALUES (?,?,?,?,?)",
            (*p, stock),
        )

    # ── Orders + items (1 500) ────────────────────────────────────────────────
    statuses = ["completed", "completed", "completed", "refunded", "cancelled"]
    order_id = 0
    for _ in range(1500):
        cid = random.randint(1, 200)
        order_date = random_date(datetime(2022, 1, 1), datetime(2024, 6, 30))
        status = random.choice(statuses)
        n_items = random.randint(1, 5)
        total = 0.0
        items = []
        for _ in range(n_items):
            pid = random.randint(1, 50)
            qty = random.randint(1, 4)
            cur.execute("SELECT price FROM products WHERE id=?", (pid,))
            row = cur.fetchone()
            unit_price = row[0] if row else 9.99
            total += unit_price * qty
            items.append((pid, qty, unit_price))

        cur.execute(
            "INSERT INTO orders (customer_id, order_date, status, total_amount) VALUES (?,?,?,?)",
            (cid, order_date, status, round(total, 2)),
        )
        order_id = cur.lastrowid
        for pid, qty, up in items:
            cur.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?,?,?,?)",
                (order_id, pid, qty, up),
            )

    conn.commit()
    conn.close()
    print(f"✅  Sample DB created at {DB_PATH}")
    print("    Tables: customers (200), products (50), orders (1500), order_items")


if __name__ == "__main__":
    seed()
