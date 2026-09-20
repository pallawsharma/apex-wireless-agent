"""In-memory database for Apex Wireless customer accounts, catalog, and inventory.

Shared across the GEAP backend tools for the Hybrid Architecture.
"""

CUSTOMERS = {
    "+14155550199": {
        "account_id": "ACC-1001",
        "customer_name": "Alex Rivera",
        "phone_number": "+14155550199",
        "user_zip_code": "94105",
        "current_plan": "Unlimited Plus",
        "active_lines_count": 2,
        "primary_device": "iPhone 15 Pro",
        "upgrade_eligible": True,
        "billing_balance": 85.50,
        "due_date": "October 1st",
        "pin": "1234",
        "recent_purchases": [
            {
                "order_id": "ORD-9821",
                "device": "Google Pixel 9 Pro (128GB, Obsidian)",
                "purchase_date": "2026-09-14",
                "price": 999.00,
                "status": "delivered",
            }
        ],
    },
    "+14155550123": {
        "account_id": "ACC-2002",
        "customer_name": "Taylor Morgan",
        "phone_number": "+14155550123",
        "user_zip_code": "94102",
        "current_plan": "Unlimited Starter",
        "active_lines_count": 4,
        "primary_device": "Samsung Galaxy S23",
        "upgrade_eligible": False,
        "billing_balance": 140.00,
        "due_date": "October 15th",
        "pin": "5678",
        "recent_purchases": [],
    },
}

DEVICES = [
    {
        "id": "pixel-9-pro-fold",
        "name": "Google Pixel 9 Pro Fold",
        "category": "foldable",
        "retail_price": 1799.00,
        "monthly_finance": 49.97,
        "in_stock": True,
        "features": ["8-inch Super Actua Flex inner display", "Tensor G4", "Pro triple camera system"],
    },
    {
        "id": "pixel-9-pro",
        "name": "Google Pixel 9 Pro",
        "category": "flagship",
        "retail_price": 999.00,
        "monthly_finance": 27.75,
        "in_stock": True,
        "features": ["6.3-inch Super Actua display", "Gemini on-device AI", "48MP 5x telephoto"],
    },
    {
        "id": "pixel-8a",
        "name": "Google Pixel 8a",
        "category": "budget",
        "retail_price": 499.00,
        "monthly_finance": 13.86,
        "in_stock": True,
        "features": ["All-day battery", "Tensor G3", "Titan M2 security"],
    },
    {
        "id": "iphone-16-pro",
        "name": "Apple iPhone 16 Pro",
        "category": "flagship",
        "retail_price": 999.00,
        "monthly_finance": 27.75,
        "in_stock": True,
        "features": ["A18 Pro chip", "Grade 5 Titanium", "Camera Control button"],
    },
    {
        "id": "galaxy-s25-ultra",
        "name": "Samsung Galaxy S25 Ultra",
        "category": "flagship",
        "retail_price": 1299.00,
        "monthly_finance": 36.08,
        "in_stock": True,
        "features": ["Galaxy AI suite", "Snapdragon 8 Elite", "Embedded S-Pen"],
    },
    {
        "id": "galaxy-a35",
        "name": "Samsung Galaxy A35 5G",
        "category": "budget",
        "retail_price": 399.99,
        "monthly_finance": 11.11,
        "in_stock": True,
        "features": ["6.6-inch 120Hz Super AMOLED", "5000mAh battery", "Knox security"],
    },
]

PLANS = [
    {
        "id": "unlimited-starter",
        "name": "Unlimited Starter",
        "single_line_price": 65.00,
        "multi_line_rates": {
            "1": 65.00,
            "2": 55.00,
            "3": 40.00,
            "4+": 35.00,
        },
        "features": ["Unlimited 5G Data", "SD Video Streaming", "3GB High-Speed Mobile Hotspot"],
    },
    {
        "id": "unlimited-plus",
        "name": "Unlimited Plus",
        "single_line_price": 80.00,
        "multi_line_rates": {
            "1": 80.00,
            "2": 70.00,
            "3": 50.00,
            "4+": 45.00,
        },
        "features": ["Unlimited Premium Ultra-Wideband 5G", "50GB Mobile Hotspot", "4K UHD Streaming", "Apex Care Basic"],
    },
    {
        "id": "prepaid-15gb",
        "name": "15GB Prepaid No-Credit-Check",
        "single_line_price": 35.00,
        "multi_line_rates": {"1+": 35.00},
        "features": ["15GB 5G High-Speed Data", "No credit check required", "Instant activation via eSIM"],
    },
    {
        "id": "prepaid-unlimited",
        "name": "Prepaid Unlimited",
        "single_line_price": 50.00,
        "multi_line_rates": {"1+": 50.00},
        "features": ["Unlimited 5G Data", "No credit check required", "Includes 5GB Hotspot"],
    },
]

STORES = [
    {
        "store_id": "STORE-SF-01",
        "store_name": "Apex Wireless - Downtown San Francisco",
        "address": "750 Market Street, San Francisco, CA 94102",
        "zip_code": "94102",
        "distance_miles": 0.8,
        "phone_number": "(415) 555-8800",
        "hours": "Monday to Saturday 10:00 AM to 8:00 PM, Sunday 11:00 AM to 6:00 PM",
        "in_stock_devices": ["Google Pixel 9 Pro", "Apple iPhone 16 Pro", "Samsung Galaxy S25 Ultra"],
    },
    {
        "store_id": "STORE-SF-02",
        "store_name": "Apex Wireless - Mission District",
        "address": "2240 Mission Street, San Francisco, CA 94110",
        "zip_code": "94110",
        "distance_miles": 2.1,
        "phone_number": "(415) 555-4422",
        "hours": "Monday to Saturday 10:00 AM to 7:00 PM, Sunday 11:00 AM to 5:00 PM",
        "in_stock_devices": ["Google Pixel 9 Pro", "Apple iPhone 16 Pro"],
    },
]

RESERVATIONS = {}
RMAS = {}
