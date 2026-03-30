import re

# Rule-based compliance validation (no ML).
# Rules example:
# {
#   "required_fields": ["Invoice No", "Date", "Amount"],
#   "patterns": {"Date": "^\\d{2}/\\d{2}/\\d{4}$"},
#   "value_constraints": {"Amount": {"min": 1, "max": 100000}}
# }


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").strip().lower())


def _get_aliases(normalized_name: str):
    alias_map = {
        "invoiceno": {"invoiceno", "invoicenumber", "invoiceid", "invoice"},
        "date": {"date", "invoicedate", "issuedate", "billingdate"},
        "amount": {"amount", "totalamount", "amountdue", "total", "grandtotal"},
    }
    return alias_map.get(normalized_name, {normalized_name})


def _find_field_value(extracted: dict, field_name: str) -> str:
    # Exact key first.
    if field_name in extracted:
        exact = str(extracted.get(field_name) or "").strip()
        if exact:
            return exact

    target = _normalize_key(field_name)
    aliases = _get_aliases(target)

    for key, value in (extracted or {}).items():
        key_norm = _normalize_key(str(key))
        text = str(value or "").strip()
        if not text:
            continue
        if key_norm == target or key_norm in aliases:
            return text

    return ""


def evaluate_compliance(extracted: dict, rules: dict):
    extracted = extracted or {}
    remarks = []
    status = "PASS"

    for field in rules.get("required_fields", []):
        if not _find_field_value(extracted, field):
            status = "FAIL"
            remarks.append(f"Missing required field: {field}")

    patterns = rules.get("patterns", {})
    for field, pattern in patterns.items():
        value = _find_field_value(extracted, field)
        if value and not re.match(pattern, value):
            status = "WARNING" if status != "FAIL" else status
            remarks.append(f"Invalid format for {field}: {value}")

    constraints = rules.get("value_constraints", {})
    for field, constraint in constraints.items():
        value = _find_field_value(extracted, field)
        if value:
            try:
                numeric_text = re.sub(r"[^0-9.\-]", "", value.replace(",", ""))
                numeric = float(numeric_text)
                if "min" in constraint and numeric < constraint["min"]:
                    status = "WARNING" if status != "FAIL" else status
                    remarks.append(f"{field} below minimum: {numeric}")
                if "max" in constraint and numeric > constraint["max"]:
                    status = "WARNING" if status != "FAIL" else status
                    remarks.append(f"{field} above maximum: {numeric}")
            except ValueError:
                status = "WARNING" if status != "FAIL" else status
                remarks.append(f"{field} is not numeric: {value}")

    return {"status": status, "remarks": "; ".join(remarks) or "All checks passed"}
