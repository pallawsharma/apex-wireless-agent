"""Typed Python functions representing enterprise tools for Apex Wireless.

ADK 2.0 inspects these signatures and docstrings to generate Gemini tool schemas.
"""

from typing import Any, Dict, List, Optional
from tools.database import CUSTOMERS, DEVICES, PLANS, RESERVATIONS, RMAS, STORES


def lookup_caller_id(phone_number: str) -> Dict[str, Any]:
    """Looks up customer account details by inbound telephone number (ANI).

    Args:
        phone_number: The incoming caller phone number (e.g. 4155550199).
    """
    clean_number = "".join(filter(str.isdigit, phone_number))
    for num, data in CUSTOMERS.items():
        if "".join(filter(str.isdigit, num)) == clean_number or num.endswith(clean_number):
            return {
                "status": "success",
                "match_found": True,
                "account_id": data["account_id"],
                "customer_name": data["customer_name"],
                "customer_type": "EXISTING_CUSTOMER",
                "caller_phone_number": data["phone_number"],
                "current_plan": data["current_plan"],
                "active_lines_count": data["active_lines_count"],
                "primary_device": data["primary_device"],
                "user_zip_code": data["user_zip_code"],
                "billing_balance": data["billing_balance"],
                "due_date": data["due_date"],
                "upgrade_eligible": data["upgrade_eligible"],
            }

    return {
        "status": "success",
        "match_found": False,
        "customer_name": "New Caller",
        "customer_type": "PROSPECT",
        "caller_phone_number": phone_number or "UNKNOWN_NUMBER",
        "prospect_lead_id": "LEAD-780000",
        "message": "No existing account on file. Created CRM sales lead for future follow-up.",
    }


def verify_customer(account_id: str, pin: str) -> Dict[str, Any]:
    """Authenticates the customer account using their 4-digit security PIN.

    Args:
        account_id: The customer account identifier (e.g. ACC-1001).
        pin: The 4-digit secret security PIN.
    """
    for _, data in CUSTOMERS.items():
        if data["account_id"] == account_id:
            if data["pin"] == pin:
                return {
                    "status": "success",
                    "authenticated": True,
                    "customer_name": data["customer_name"],
                    "account_id": account_id,
                    "message": "Authentication successful. Access granted to account billing and modifications.",
                }
            return {
                "status": "failure",
                "authenticated": False,
                "message": "Incorrect 4-digit PIN. Please re-enter or request one-time SMS code.",
            }
    return {"status": "failure", "authenticated": False, "message": "Account ID not found."}


def catalog_search(query: str = "", category: str = "all") -> Dict[str, Any]:
    """Searches Apex Wireless devices, smartphones, and rate plans.

    Args:
        query: Specific device model or keyword (e.g. 'Pixel 9 Pro Fold', 'Unlimited Starter').
        category: Filter by 'devices', 'plans', 'budget', 'flagship', or 'all'.
    """
    q = query.lower()
    cat = category.lower()

    matched_devices = []
    if cat in ["all", "devices", "flagship", "budget"]:
        for d in DEVICES:
            if cat in ["devices", "all"] or d["category"] == cat:
                if not q or q in d["name"].lower() or q in d["category"]:
                    matched_devices.append(d)

    matched_plans = []
    if cat in ["all", "plans"]:
        for p in PLANS:
            if not q or q in p["name"].lower():
                matched_plans.append(p)

    return {
        "status": "success",
        "devices": matched_devices,
        "device_count": len(matched_devices),
        "plans": matched_plans,
        "plan_count": len(matched_plans),
    }


def find_nearby_stores(zip_code: str) -> Dict[str, Any]:
    """Finds nearby retail store locations by customer ZIP code.

    Args:
        zip_code: 5-digit US Postal ZIP code (e.g. 94105).
    """
    return {
        "status": "success",
        "searched_zip_code": zip_code,
        "store_count": len(STORES),
        "stores": STORES,
    }


def reserve_store_pickup(
    store_id: str,
    device_name: str,
    customer_name: str,
    phone_number: str,
) -> Dict[str, Any]:
    """Reserves a device for in-store express pickup with a 48-hour hold.

    Args:
        store_id: Store identifier (e.g. STORE-SF-01).
        device_name: Full model name (e.g. 'Google Pixel 9 Pro').
        customer_name: Full legal name on government ID.
        phone_number: SMS callback number.
    """
    res_id = f"RES-{len(RESERVATIONS) + 49211}"
    store = next((s for s in STORES if s["store_id"] == store_id), STORES[0])

    reservation = {
        "reservation_id": res_id,
        "status": "success",
        "device_reserved": device_name,
        "customer_name": customer_name,
        "contact_phone": phone_number,
        "store_id": store["store_id"],
        "store_name": store["store_name"],
        "store_address": store["address"],
        "store_phone": store["phone_number"],
        "hold_duration": "Held for 48 hours",
        "pickup_instructions": f"Your {device_name} is reserved under reservation number {res_id}. Please bring a valid government photo ID to the express pickup counter.",
    }
    RESERVATIONS[res_id] = reservation
    return reservation


def run_device_diagnostics(phone_number: str, issue_type: str = "slow_data") -> Dict[str, Any]:
    """Executes network ping, eSIM status check, and cell tower telemetry diagnostics.

    Args:
        phone_number: Line phone number to diagnose.
        issue_type: Symptom ('slow_data', 'dropped_calls', 'no_service').
    """
    return {
        "status": "success",
        "phone_number": "+14155550199",
        "issue_analyzed": issue_type,
        "diagnostics": {
            "device_model": "Apple iPhone 15 Pro",
            "line_number": "+14155550199",
            "sim_type": "eSIM",
            "sim_status": "Active & Provisioned",
            "network_status": "Connected (5G Ultra Wideband)",
            "signal_strength_bars": 5.0,
            "tower_id": "TWR-SFO-042",
            "tower_status": "Operational (No outages)",
            "throttled": False,
            "data_allowance": "Unlimited Premium High-Speed",
            "data_used_gb": 24.3,
            "recommended_action": "Toggle Airplane mode on for 10 seconds and off, or perform a Network Settings reset under Settings > General > Transfer or Reset iPhone.",
        },
        "summary": "Diagnostics completed for Apple iPhone 15 Pro. SIM status is Active & Provisioned, connected to Connected (5G Ultra Wideband) with 5 out of 5 bars. No network throttling or tower outages detected. Recommended step: Toggle Airplane mode on for 10 seconds and off, or perform a Network Settings reset under Settings > General > Transfer or Reset iPhone.",
    }


def check_return_eligibility(account_id: str, device_condition: str = "opened") -> Dict[str, Any]:
    """Evaluates 14-day policy return eligibility, restocking fees, and estimated refunds.

    Args:
        account_id: The customer account ID (e.g. ACC-1001).
        device_condition: Condition of returned hardware ('unopened', 'opened', 'damaged').
    """
    restocking_fee = 35.00 if device_condition == "opened" else 0.00
    original_price = 999.00
    refund = original_price - restocking_fee

    return {
        "status": "success",
        "account_id": account_id,
        "device_name": "Google Pixel 9 Pro (128GB, Obsidian)",
        "is_eligible": True,
        "days_since_purchase": 5.0,
        "return_deadline": "September 28, 2026",
        "device_condition": device_condition,
        "restocking_fee": restocking_fee,
        "original_price": original_price,
        "estimated_refund": refund,
        "policy_summary": f"Eligible for return! Your purchase is 5 days old (within our 14-day window ending September 28, 2026). Restocking fee: ${restocking_fee:.2f} (standard fee for opened devices). Estimated refund: ${refund:.2f} back to your original payment method.",
    }


def process_device_return(
    account_id: str,
    device_name: str,
    return_method: str = "store_dropoff",
    zip_code: str = "94105",
    confirmed_by_customer: bool = True,
) -> Dict[str, Any]:
    """Authorizes a device return, issues RMA number, and generates return instructions.

    Includes a Human-in-the-Loop Safeguard: High-stakes hardware return authorization and
    restocking fee deductions require verified human confirmation before executing irreversible RMA issuance.

    Args:
        account_id: Customer account ID.
        device_name: Device to return (e.g. 'Google Pixel 9 Pro').
        return_method: 'store_dropoff' or 'mail_in'.
        zip_code: Customer postal code for finding drop-off location.
        confirmed_by_customer: Human-in-the-Loop verification flag. Must be explicitly True.
    """
    # Human-in-the-Loop Guard: Stop execution if customer has not confirmed restocking fee
    if not confirmed_by_customer:
        return {
            "status": "requires_human_confirmation",
            "action_blocked": True,
            "reason": "HIGH_STAKES_ACTION",
            "message": (
                "Human-in-the-Loop Policy Check: Returning this device will incur a $35.00 restocking fee. "
                "Explicit customer authorization is required before finalizing this transaction. "
                "Please verify with the customer: 'Do you authorize the return and the $35 restocking fee?'"
            ),
        }

    rma_num = f"RMA-{len(RMAS) + 70448}"
    store = STORES[0]
    maps_url = "https://www.google.com/maps/dir/?api=1&destination=750+Market+Street%2C+San+Francisco%2C+CA+94102"

    instructions = (
        f"Your return authorization number is {rma_num}. Bring your {device_name} and accessories to "
        f"{store['store_name']} at {store['address']}. Directions: {maps_url}. "
        "A store associate at the express return counter will inspect the device and issue your instant refund."
    )

    rma_data = {
        "status": "success",
        "rma_number": rma_num,
        "account_id": account_id,
        "device_name": device_name,
        "return_method": return_method,
        "dropoff_store": store["store_name"],
        "store_address": store["address"],
        "store_hours": store["hours"],
        "maps_url": maps_url,
        "instructions": instructions,
        "human_confirmation_verified": True,
    }
    RMAS[rma_num] = rma_data
    return rma_data


def lookup_billing_details(account_id: str) -> Dict[str, Any]:
    """Retrieves itemized monthly charges, auto-pay status, taxes, and due date.

    Args:
        account_id: The customer account identifier (e.g. ACC-1001).
    """
    customer = next((c for c in CUSTOMERS.values() if c["account_id"] == account_id), list(CUSTOMERS.values())[0])

    itemized = [
        {"description": f"{customer['current_plan']} (Line 1: 415-555-0199)", "amount": 80.00},
        {"description": "Paperless & AutoPay Monthly Discount", "amount": -10.00},
        {"description": f"Apex Care Device Protection ({customer['primary_device']})", "amount": 9.00},
        {"description": "Government Taxes and Regulatory Surcharges", "amount": 6.50},
    ]

    return {
        "status": "success",
        "account_id": account_id,
        "customer_name": customer["customer_name"],
        "total_amount_due": customer["billing_balance"],
        "due_date": f"{customer['due_date']}, 2026",
        "billing_cycle": "September 1, 2026 - September 30, 2026",
        "autopay_enrolled": True,
        "payment_status": "Current (AutoPay Scheduled)",
        "itemized_charges": itemized,
        "explanation": f"Your monthly total is ${customer['billing_balance']:.2f} due on {customer['due_date']}. This consists of your {customer['current_plan']} plan for $80, minus your $10 AutoPay discount, plus $9 for Apex Care device protection, and $6.50 in taxes and fees.",
    }
