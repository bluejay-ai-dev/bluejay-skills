#!/usr/bin/env python3
"""Create Bluejay contracts and rate cards in Metronome the way the internal dashboard does.

Mirrors bluejay-ai-dashboard lib/metronome/{create-contract,contracts,operations,transform,
subscription-rows,deal-window}.ts. Every write is a dry run unless --apply is passed.
Needs METRONOME_API_KEY. Standard library only.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://api.metronome.com"
CONTRACT_NAME_PREFIX = "Bluejay"
TEMPLATE_RATE_CARD_NAME = "Rate Card (Template)"
SUBSCRIPTION_PRODUCT_NAME = "Subscription"
PHONE_PRODUCT_NAME = "Phone Numbers"
CREDITS_PRODUCT_NAME = "Credits"
# (catalog type, accepted names); sandbox names its credits product "Bluejay Credits" and also keeps a
# FIXED "Phone numbers" product, so the type is what tells the real one apart
CATALOG_PRODUCTS = {
    SUBSCRIPTION_PRODUCT_NAME: ("SUBSCRIPTION", {"Subscription"}),
    PHONE_PRODUCT_NAME: ("SUBSCRIPTION", {"Phone Numbers"}),
    CREDITS_PRODUCT_NAME: ("FIXED", {"Credits", "Bluejay Credits"}),
}
CREDITS_CREDIT_TYPE_NAME = "Credits"
CF_OVERAGES = "overages_allowed"
CF_K = "markup_commit_k"
CF_M = "markup_overage_m"
CF_PAYG = "pay-as-you-go"
TERMS = {"MONTHLY": 1, "QUARTERLY": 3, "ANNUAL": 12}
RECURRING_CREDIT_PRIORITY = 4
ADD_RATES_BATCH = 40
MAX_FREE_MONTHS = 60
WINDOW_END_CUSHION = timedelta(hours=1)
BILLING_LOOKUP_ATTEMPTS = 3


class MetronomeError(Exception):
    pass


def api_key() -> str:
    key = os.environ.get("METRONOME_API_KEY", "").strip()
    if not key:
        sys.exit("METRONOME_API_KEY is not set")
    return key


def call(method: str, path: str, body=None, query=None):
    url = f"{API}{path}" + (f"?{urllib.parse.urlencode(query)}" if query else "")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as res:
            raw = res.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise MetronomeError(f"{method} {path} -> {e.code}: {e.read().decode()[:500]}") from e


def post(path, body, query=None):
    return call("POST", path, body, query)


def paged(path, body=None, query=None, method="POST"):
    rows, cursor = [], None
    while True:
        q = {"limit": "100", **(query or {}), **({"next_page": cursor} if cursor else {})}
        res = call(method, path, body if method == "POST" else None, q)
        rows.extend(res.get("data", []))
        cursor = res.get("next_page")
        if not cursor:
            return rows


def floor_to_hour(iso: str) -> str:
    moment = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    return moment.replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:00:00.000Z")


def parse_iso(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def add_calendar_months(moment: datetime, months: int) -> datetime:
    index = moment.month - 1 + months
    year, month = moment.year + index // 12, index % 12 + 1
    next_month = datetime(year + month // 12, month % 12 + 1, 1, tzinfo=timezone.utc)
    last_day = (next_month - timedelta(days=1)).day
    return moment.replace(year=year, month=month, day=min(moment.day, last_day))


def free_window_end(starting_at: str, free_months: int) -> str:
    end = add_calendar_months(parse_iso(starting_at), free_months) + WINDOW_END_CUSHION
    return end.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def js_number_string(value: float) -> str:
    """String(value) as the dashboard writes it: 2 not 2.0."""
    return str(int(value)) if float(value).is_integer() else repr(value)


def dollars_to_cents(dollars: float) -> int:
    return round(dollars * 100)


def emit(label, payload):
    print(f"\n### {label}\n{json.dumps(payload, indent=2)}")


# ---------- catalog lookups (by name, so the same script works on prod and sandbox) ----------

def catalog_product_ids() -> dict:
    """The Subscription, Phone Numbers and Credits product ids in this Metronome account."""
    products = [p for p in paged("/v1/contract-pricing/products/list", {}) if not p.get("archived_at")]
    found = {}
    for role, (catalog_type, names) in CATALOG_PRODUCTS.items():
        matches = [p["id"] for p in products if p["type"].upper() == catalog_type and p.get("current", {}).get("name") in names]
        if len(matches) != 1:
            raise MetronomeError(f"Expected one {catalog_type} product named {sorted(names)}, found {len(matches)}")
        found[role] = matches[0]
    return found


def all_rate_cards():
    return paged("/v1/contract-pricing/rate-cards/list", {})


def get_rate_card(rate_card_id: str):
    return post("/v1/contract-pricing/rate-cards/get", {"id": rate_card_id})["data"]


def rates_for_card(rate_card_id: str, at: str):
    return paged("/v1/contract-pricing/rate-cards/getRates", {"rate_card_id": rate_card_id, "at": at})


def credits_credit_type_id(card) -> str:
    for conversion in card.get("credit_type_conversions") or []:
        if conversion["custom_credit_type"]["name"] == CREDITS_CREDIT_TYPE_NAME:
            return conversion["custom_credit_type"]["id"]
    raise MetronomeError("Rate card has no Credits custom credit type to grant")


def contracts_for(customer_id: str, include_archived=False):
    return post("/v2/contracts/list", {"customer_id": customer_id, "include_archived": include_archived})["data"]


def active_at(contract, moment: str) -> bool:
    start = parse_iso(contract["starting_at"])
    end = contract.get("ending_before")
    return start <= parse_iso(moment) and (end is None or parse_iso(end) > parse_iso(moment))


# ---------- read commands ----------

def cmd_customer(args):
    customers = paged("/v1/customers", method="GET")
    needle = args.query.lower()
    matches = [c for c in customers if needle in c.get("name", "").lower() or needle in (c.get("external_id") or "")
               or needle == c["id"]]
    if not matches:
        sys.exit(f"No Metronome customer matches {args.query!r}")
    for customer in matches[:5]:
        print(f"\n== {customer['name']}  customer_id={customer['id']}  external_id(org_id)={customer.get('external_id')}")
        configs = post("/v1/getCustomerBillingProviderConfigurations", {"customer_id": customer["id"]})["data"]
        for config in configs:
            print(f"   billing: {config['billing_provider']} {config.get('configuration')} archived={config.get('archived_at')}")
        if not configs:
            print("   billing: none linked")
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for contract in contracts_for(customer["id"]):
            state = "ACTIVE" if active_at(contract, now) else "not active now"
            print(f"   contract {contract['id']} {contract.get('name')!r} {contract['starting_at']} -> "
                  f"{contract.get('ending_before')} card={contract.get('rate_card_id')} [{state}] "
                  f"schedule={contract.get('usage_statement_schedule')}")
        balances = post("/v1/contracts/customerBalances/list",
                        {"customer_id": customer["id"], "include_balance": True}).get("data", [])
        for balance in balances:
            print(f"   balance {balance.get('type')} {(balance.get('product') or {}).get('name')} "
                  f"contract={(balance.get('contract') or {}).get('id')} balance={balance.get('balance')}")


def cmd_rate_cards(args):
    for card in all_rate_cards():
        fields = card.get("custom_fields") or {}
        if args.query and args.query.lower() not in card["name"].lower():
            continue
        print(f"{card['id']}  {card['name']:<40} k={fields.get(CF_K, '-'):<8} m={fields.get(CF_M, '-'):<8}"
              f"{'  PAYG' if fields.get(CF_PAYG) == 'true' else ''}")


# ---------- rate card creation (operations.ts createRateCardFromTemplate) ----------

def product_types(product_ids):
    types = {}
    for product_id in set(product_ids):
        types[product_id] = post("/v1/contract-pricing/products/get", {"id": product_id})["data"]["type"].upper()
    return types


def scale(value, mult):
    if not isinstance(value, (int, float)):
        return value
    scaled = value * mult
    return round(scaled) if float(value).is_integer() else round(scaled * 1e6) / 1e6


def scale_rate(rate, mult):
    rate = dict(rate, rate_type=rate["rate_type"].upper())
    if rate["rate_type"] in ("FLAT", "SUBSCRIPTION") and "price" in rate:
        rate["price"] = scale(rate["price"], mult)
    elif rate["rate_type"] == "TIERED" and rate.get("tiers"):
        rate["tiers"] = [dict(t, price=scale(t["price"], mult)) for t in rate["tiers"]]
    return rate


def row_to_payload(row, types, k, m, hard_stop, subscription_prices):
    rate = dict(row["rate"], rate_type=row["rate"]["rate_type"].upper())
    commit = dict(row["commit_rate"], rate_type=row["commit_rate"]["rate_type"].upper()) if row.get("commit_rate") else None
    if types[row["product_id"]] == "USAGE":
        if hard_stop:
            commit = scale_rate(commit or {"rate_type": rate["rate_type"], "price": rate.get("price"),
                                           "tiers": rate.get("tiers")}, k)
            rate = {"rate_type": "FLAT", "price": 0, "credit_type": rate.get("credit_type")}
        else:
            rate = scale_rate(rate, m)
            commit = scale_rate(commit, k) if commit else None
    payload = {
        "product_id": row["product_id"], "starting_at": row["starting_at"], "entitled": row.get("entitled"),
        "rate_type": rate["rate_type"], "pricing_group_values": row.get("pricing_group_values"),
        "ending_before": row.get("ending_before"), "billing_frequency": row.get("billing_frequency"),
        "price": rate.get("price"), "quantity": rate.get("quantity"), "is_prorated": rate.get("is_prorated"),
        "tiers": rate.get("tiers"), "custom_rate": rate.get("custom_rate"),
        "credit_type_id": (rate.get("credit_type") or {}).get("id"), "commit_rate": commit,
    }
    override = subscription_prices.get((row.get("product_name"), (row.get("billing_frequency") or "").upper()))
    if types[row["product_id"]] == "SUBSCRIPTION" and override is not None:
        payload["price"] = dollars_to_cents(override)
    return {key: value for key, value in payload.items() if value is not None}


def expand_subscription_terms(payloads, types, names, subscription_prices):
    def term_key(p):
        return (p["product_id"], (p.get("billing_frequency") or "").upper(), json.dumps(p.get("pricing_group_values") or {}, sort_keys=True))
    present = {term_key(p) for p in payloads}
    added = []
    for p in payloads:
        if types[p["product_id"]] != "SUBSCRIPTION" or (p.get("billing_frequency") or "").upper() != "MONTHLY":
            continue
        for term, months in TERMS.items():
            if months == 1:
                continue
            clone = dict(p, billing_frequency=term)
            if term_key(clone) in present:
                continue
            present.add(term_key(clone))
            override = subscription_prices.get((names[p["product_id"]], term))
            price = dollars_to_cents(override) if override is not None else (
                round(p["price"] * months) if isinstance(p.get("price"), (int, float)) else p.get("price"))
            added.append(dict(clone, price=price))
    return payloads + added


def parse_term_prices(pairs, product_name):
    prices = {}
    for pair in pairs or []:
        term, _, dollars = pair.partition("=")
        if term.upper() not in TERMS or not dollars:
            sys.exit(f"--{product_name.lower().replace(' ', '-')}-price expects TERM=DOLLARS, got {pair!r}")
        prices[(product_name, term.upper())] = float(dollars)
    return prices


def cmd_create_rate_card(args):
    if args.k < 0 or args.m < 0:
        sys.exit("k and m must be non-negative")
    templates = [c for c in all_rate_cards() if c["name"] == TEMPLATE_RATE_CARD_NAME]
    if len(templates) != 1:
        sys.exit(f"Expected exactly one {TEMPLATE_RATE_CARD_NAME!r} card, found {len(templates)}")
    template = get_rate_card(templates[0]["id"])
    rows = rates_for_card(template["id"], datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    types = product_types(r["product_id"] for r in rows)
    names = {r["product_id"]: r.get("product_name") for r in rows}
    subscription_prices = {**parse_term_prices(args.subscription_price, SUBSCRIPTION_PRODUCT_NAME),
                           **parse_term_prices(args.phone_price, PHONE_PRODUCT_NAME)}
    payloads = [row_to_payload(r, types, args.k, args.m, args.payg, subscription_prices) for r in rows]
    payloads = expand_subscription_terms(payloads, types, names, subscription_prices)
    custom_fields = {CF_K: js_number_string(args.k), CF_M: js_number_string(args.m), **({CF_PAYG: "true"} if args.payg else {})}
    create_body = {
        "name": args.name, **({"description": args.description} if args.description else {}),
        "fiat_credit_type_id": template["fiat_credit_type"]["id"],
        "credit_type_conversions": [
            {"custom_credit_type_id": c["custom_credit_type"]["id"], "fiat_per_custom_credit": float(c["fiat_per_custom_credit"])}
            for c in template.get("credit_type_conversions") or []],
        "custom_fields": custom_fields,
    }
    print(f"Template {template['id']} -> {len(rows)} rates, {len(payloads)} after adding QUARTERLY/ANNUAL subscription terms")
    for p in payloads:
        if types[p["product_id"]] == "SUBSCRIPTION":
            print(f"   list price {names[p['product_id']]:<14} {p.get('billing_frequency'):<10} ${p.get('price', 0) / 100:,.2f}")
    emit("rate-cards/create", create_body)
    if not args.apply:
        print("\nDRY RUN — nothing written. Re-run with --apply to create the card.")
        return
    card_id = post("/v1/contract-pricing/rate-cards/create", create_body)["data"]["id"]
    for i in range(0, len(payloads), ADD_RATES_BATCH):
        post("/v1/contract-pricing/rate-cards/addRates", {"rate_card_id": card_id, "rates": payloads[i:i + ADD_RATES_BATCH]})
    print(f"\nCREATED rate card {card_id} ({args.name}) with {len(payloads)} rates")


# ---------- contract creation (create-contract.ts createContractForCustomer) ----------

def subscription(product_id, quantity, is_prorated, term):
    return {"collection_schedule": "ADVANCE", "initial_quantity": quantity, "quantity_management_mode": "QUANTITY_ONLY",
            "proration": {"is_prorated": is_prorated, "invoice_behavior": "BILL_IMMEDIATELY"},
            "subscription_rate": {"billing_frequency": term, "product_id": product_id}}


def price_override(product_id, dollars, starting_at, term, ending_before=None):
    override = {"starting_at": starting_at, "type": "OVERWRITE", "entitled": True,
                "override_specifiers": [{"product_id": product_id, "billing_frequency": term}],
                "overwrite_rate": {"rate_type": "FLAT", "price": dollars_to_cents(dollars)}}
    if ending_before:
        override["ending_before"] = ending_before
    return override


def fee_overrides(product_id, fee, starting_at, term, free_months):
    if not free_months:
        return [price_override(product_id, fee, starting_at, term)]
    free_ends = free_window_end(starting_at, free_months)
    return [price_override(product_id, 0, starting_at, term, free_ends), price_override(product_id, fee, free_ends, term)]


def validate_contract_args(args):
    if args.term not in TERMS:
        sys.exit("term must be MONTHLY, QUARTERLY or ANNUAL")
    for name in ("fee", "credits", "phone_price"):
        if getattr(args, name) < 0:
            sys.exit(f"{name} must be non-negative")
    if args.phone_quantity < 0:
        sys.exit("phone-quantity must be a non-negative integer")
    if args.free_months is not None:
        if not 0 < args.free_months <= MAX_FREE_MONTHS:
            sys.exit(f"free-months must be 1-{MAX_FREE_MONTHS}")
        if args.term != "MONTHLY":
            sys.exit("A startup deal free period is only supported on a monthly term")
    if bool(args.stripe_customer) != bool(args.collection):
        sys.exit("--stripe-customer and --collection go together")
    if args.stripe_customer and not args.stripe_customer.startswith("cus_"):
        sys.exit("stripe customer must look like cus_…")
    if sum(bool(x) for x in (args.replace, args.replace_at_its_start, args.add)) > 1:
        sys.exit("choose one of --replace, --replace-at-its-start, --add")


def plan_transition(args, starting_at):
    """applyContractTransition: returns (start, action, contract) without writing."""
    active = [c for c in contracts_for(args.customer_id) if active_at(c, starting_at)]
    if args.replace_at_its_start:
        target = next((c for c in contracts_for(args.customer_id) if c["id"] == args.replace_at_its_start), None)
        if not target:
            sys.exit("The contract being replaced was not found")
        return target["starting_at"], "archive", target
    if not active:
        return starting_at, None, None
    if args.add:
        return starting_at, None, None
    if not args.replace:
        ids = ", ".join(c["id"] for c in active)
        sys.exit(f"Customer already has an active contract at the start ({ids}) — pass --replace <id> or --add")
    target = next((c for c in active if c["id"] == args.replace), None)
    if not target:
        sys.exit("Selected contract is not active at the new start date")
    if parse_iso(starting_at) <= parse_iso(target["starting_at"]):
        sys.exit("New contract must start after the existing contract started")
    return starting_at, "end", target


def cmd_create_contract(args):
    validate_contract_args(args)
    requested_start = floor_to_hour(args.start) if args.start else floor_to_hour(datetime.now(timezone.utc).isoformat())
    starting_at, transition, old = plan_transition(args, requested_start)
    starting_at = floor_to_hour(starting_at)

    card = get_rate_card(args.rate_card)
    rates = rates_for_card(card["id"], starting_at)
    ids = catalog_product_ids()
    subscription_id, phone_id, credits_id = (ids[n] for n in (SUBSCRIPTION_PRODUCT_NAME, PHONE_PRODUCT_NAME, CREDITS_PRODUCT_NAME))
    missing = [n for pid, n in ((subscription_id, SUBSCRIPTION_PRODUCT_NAME), (phone_id, PHONE_PRODUCT_NAME))
               if not any(r["product_id"] == pid and (r.get("billing_frequency") or "").upper() == args.term for r in rates)]
    if missing:
        sys.exit(f"Rate card has no {args.term} subscription rate for {', '.join(missing)} — add one or pick another term")

    body = {
        "customer_id": args.customer_id, "rate_card_id": card["id"], "starting_at": starting_at,
        "name": f"{CONTRACT_NAME_PREFIX} - {args.customer_name.strip()}",
        "usage_statement_schedule": {"frequency": args.term, "day": "CUSTOM_DATE", "billing_anchor_date": starting_at},
        "custom_fields": {CF_OVERAGES: "true" if args.overages else "false"},
        "recurring_credits": [{
            "product_id": credits_id,
            "access_amount": {"unit_price": args.credits, "quantity": 1, "credit_type_id": credits_credit_type_id(card)},
            "commit_duration": {"value": 1, "unit": "PERIODS"}, "priority": RECURRING_CREDIT_PRIORITY,
            "rate_type": "COMMIT_RATE", "proration": "FIRST_AND_LAST", "starting_at": starting_at}],
        "subscriptions": [subscription(subscription_id, 1, True, args.term),
                          subscription(phone_id, args.phone_quantity, False, args.term)],
        "overrides": [*fee_overrides(subscription_id, args.fee, starting_at, args.term, args.free_months),
                      price_override(phone_id, args.phone_price, starting_at, args.term)],
    }

    print(f"Contract '{body['name']}' on card {card['name']} ({card['id']})")
    print(f"   start/anchor {starting_at}  term {args.term}  fee ${args.fee:,.2f}  credits {args.credits:,g}"
          f"  phones {args.phone_quantity} @ ${args.phone_price:,.2f}  overages {'on' if args.overages else 'off'}"
          f"{f'  free months {args.free_months}' if args.free_months else ''}")
    if transition == "end":
        print(f"   ends existing contract {old['id']} ({old.get('name')}) at {starting_at}")
    elif transition == "archive":
        print(f"   ARCHIVES existing contract {old['id']} ({old.get('name')}) and takes over its start")
    if args.stripe_customer:
        print(f"   bills through Stripe {args.stripe_customer} ({args.collection})")
    else:
        print("   no Stripe link — invoices stay in Metronome only")
    emit("contracts/create (billing_provider_configuration added after Stripe link)", body)
    if not args.apply:
        print("\nDRY RUN — nothing written. Re-run with --apply to create the contract.")
        return

    if transition == "end":
        post("/v1/contracts/updateEndDate", {"customer_id": args.customer_id, "contract_id": old["id"], "ending_before": starting_at})
    elif transition == "archive":
        post("/v1/contracts/archive", {"customer_id": args.customer_id, "contract_id": old["id"], "void_invoices": False})
    if args.stripe_customer:
        post("/v1/setCustomerBillingProviderConfigurations", {"data": [{
            "customer_id": args.customer_id, "billing_provider": "stripe",
            "configuration": {"stripe_customer_id": args.stripe_customer, "stripe_collection_method": args.collection},
            "delivery_method": "direct_to_billing_provider"}]})
        config_id = None
        for attempt in range(1, BILLING_LOOKUP_ATTEMPTS + 1):
            configs = post("/v1/getCustomerBillingProviderConfigurations", {"customer_id": args.customer_id})["data"]
            config_id = next((c["id"] for c in configs if c["billing_provider"] == "stripe" and not c.get("archived_at")), None)
            if config_id:
                break
            time.sleep(0.3 * attempt)
        if not config_id:
            sys.exit("Stripe was saved on the customer but billing is not ready yet — confirm the cus_ id and retry")
        body["billing_provider_configuration"] = {"billing_provider_configuration_id": config_id}
    contract_id = post("/v1/contracts/create", body)["data"]["id"]
    print(f"\nCREATED contract {contract_id}")


def cmd_verify(args):
    contract = next((c for c in contracts_for(args.customer_id) if c["id"] == args.contract_id), None)
    if not contract:
        sys.exit("Contract not found")
    print(f"{contract['name']}  {contract['starting_at']} -> {contract.get('ending_before')}  card {contract.get('rate_card_id')}")
    print(f"   schedule {contract.get('usage_statement_schedule')}  custom_fields {contract.get('custom_fields')}")
    print(f"   billing {(contract.get('customer_billing_provider_configuration') or {}).get('configuration')}")
    for s in contract.get("subscriptions", []):
        print(f"   subscription {s['subscription_rate']['product']['name']} {s['subscription_rate']['billing_frequency']} "
              f"qty {s.get('quantity_schedule')}")
    for o in contract.get("overrides", []):
        print(f"   override {(o.get('product') or {}).get('name')} ${(o.get('overwrite_rate') or {}).get('price', 0) / 100:,.2f}"
              f" {o['starting_at']} -> {o.get('ending_before')}")
    balances = post("/v1/contracts/customerBalances/list", {"customer_id": args.customer_id, "include_balance": True}).get("data", [])
    for b in balances:
        if (b.get("contract") or {}).get("id") == args.contract_id:
            items = (b.get("access_schedule") or {}).get("schedule_items", [])
            granted = sum(i.get("amount", 0) for i in items)
            print(f"   credits balance {b.get('balance')} of {granted} granted {[(i['starting_at'], i['ending_before']) for i in items]}")
    for inv in paged(f"/v1/customers/{args.customer_id}/invoices", method="GET"):
        if inv.get("contract_id") == args.contract_id:
            print(f"   invoice {inv['type']} {inv['status']} {inv.get('start_timestamp')} -> {inv.get('end_timestamp')} "
                  f"total ${inv.get('total', 0) / 100:,.2f} stripe={(inv.get('external_invoice') or {}).get('external_status')}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("customer", help="find a Metronome customer and show billing, contracts, balances")
    p.add_argument("query", help="name, org id (external_id) or Metronome customer id")
    p.set_defaults(func=cmd_customer)

    p = sub.add_parser("rate-cards", help="list rate cards with their k/m")
    p.add_argument("--query")
    p.set_defaults(func=cmd_rate_cards)

    p = sub.add_parser("create-rate-card", help="clone the template card scaled by k (credits) and m (overage)")
    p.add_argument("--name", required=True)
    p.add_argument("--description")
    p.add_argument("--k", type=float, required=True)
    p.add_argument("--m", type=float, required=True)
    p.add_argument("--payg", action="store_true", help="pay-as-you-go card: $0 list rate, usage draws at k")
    p.add_argument("--subscription-price", action="append", metavar="TERM=DOLLARS")
    p.add_argument("--phone-price", action="append", metavar="TERM=DOLLARS")
    p.add_argument("--apply", action="store_true")
    p.set_defaults(func=cmd_create_rate_card)

    p = sub.add_parser("create-contract", help="start a contract directly (dashboard 'Start now')")
    p.add_argument("--customer-id", required=True)
    p.add_argument("--customer-name", required=True)
    p.add_argument("--rate-card", required=True)
    p.add_argument("--term", required=True, type=str.upper)
    p.add_argument("--fee", type=float, required=True, help="subscription price per term, dollars")
    p.add_argument("--credits", type=float, required=True, help="credits granted each term")
    p.add_argument("--phone-price", type=float, required=True, help="per number per term, dollars")
    p.add_argument("--phone-quantity", type=int, required=True)
    p.add_argument("--overages", action=argparse.BooleanOptionalAction, required=True)
    p.add_argument("--start", help="ISO time; floored to the hour (default now)")
    p.add_argument("--free-months", type=int, help="startup/YC deal: $0 fee for N months (MONTHLY only)")
    p.add_argument("--stripe-customer")
    p.add_argument("--collection", choices=["charge_automatically", "send_invoice"])
    p.add_argument("--replace", metavar="CONTRACT_ID", help="end this active contract at the new start")
    p.add_argument("--replace-at-its-start", metavar="CONTRACT_ID", help="archive it and take over its start")
    p.add_argument("--add", action="store_true", help="add alongside an active contract")
    p.add_argument("--apply", action="store_true")
    p.set_defaults(func=cmd_create_contract)

    p = sub.add_parser("verify", help="read back a contract: settings, credit balance, invoices")
    p.add_argument("--customer-id", required=True)
    p.add_argument("--contract-id", required=True)
    p.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    try:
        args.func(args)
    except MetronomeError as e:
        sys.exit(f"Metronome error: {e}")


if __name__ == "__main__":
    main()
