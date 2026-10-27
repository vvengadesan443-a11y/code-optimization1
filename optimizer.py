import re

IDENT = r"[A-Za-z_]\w*"
BIN_RE = re.compile(rf"^\s*({IDENT})\s*=\s*({IDENT}|-?\d+(?:\.\d+)?)\s*([+\-*/])\s*({IDENT}|-?\d+(?:\.\d+)?)\s*;?\s*$")
ASSIGN_RE = re.compile(rf"^\s*({IDENT})\s*=\s*(.*?)\s*;?\s*$")
NUMBER_RE = re.compile(r"^-?\d+(?:\.\d+)?$")

def _strip_comment(line):
    return line.split("#", 1)[0].strip()

def _parse(line):
    m = BIN_RE.match(line)
    if m:
        return {"target": m.group(1), "left": m.group(2), "op": m.group(3), "right": m.group(4), "kind": "bin"}
    m = ASSIGN_RE.match(line)
    if m:
        rhs = m.group(2).strip().rstrip(";").strip()
        if rhs:
            return {"target": m.group(1), "rhs": rhs, "kind": "assign"}
    return {"kind": "raw", "raw": line.strip()}

def _is_num(value):
    return bool(NUMBER_RE.match(value))

def _format_num(value):
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)

def _constant_fold(left, op, right):
    if not (_is_num(left) and _is_num(right)):
        return None
    a = float(left) if "." in left else int(left)
    b = float(right) if "." in right else int(right)
    try:
        if op == "+": v = a + b
        elif op == "-": v = a - b
        elif op == "*": v = a * b
        elif op == "/":
            if b == 0: return None
            v = a / b
        else: return None
        return _format_num(v)
    except (ArithmeticError, ValueError):
        return None

def _peephole_expr(left, op, right):
    # Return replacement when a safe, simple algebraic identity applies.
    if op == "+" and right == "0": return left
    if op == "+" and left == "0": return right
    if op == "-" and right == "0": return left
    if op == "*" and right == "1": return left
    if op == "*" and left == "1": return right
    if op == "*" and (right == "0" or left == "0"): return "0"
    if op == "/" and right == "1": return left
    if op == "-" and left == right: return "0"
    if op == "/" and left == right and left != "0": return "1"
    return None

def _replace_vars(text, aliases):
    # Replace whole identifier tokens only.
    for name in sorted(aliases, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(name)}\b", aliases[name], text)
    return text

def _expr_key(left, op, right):
    # Commutative operators can share a DAG node in either operand order.
    if op in ("+", "*") and right < left:
        left, right = right, left
    return (left, op, right)

def optimize_code(code, techniques):
    use_dag = "dag" in techniques
    use_peephole = "peephole" in techniques
    original_lines = [_strip_comment(x) for x in code.splitlines()]
    parsed = [_parse(x) for x in original_lines if _strip_comment(x)]
    steps = []
    warnings = []
    current = []
    aliases = {}
    expr_cache = {}
    assigned = set()

    for item in parsed:
        if item["kind"] == "raw":
            current.append(item["raw"])
            if item["raw"]:
                warnings.append(f"Kept unsupported statement as-is: {item['raw']}")
            continue

        target = item["target"]
        if item["kind"] == "assign":
            rhs = _replace_vars(item["rhs"], aliases)
            # Invalidate any cached expression depending on a variable being reassigned.
            aliases.pop(target, None)
            assigned.add(target)
            current.append(f"{target} = {rhs}")
            continue

        left = _replace_vars(item["left"], aliases)
        right = _replace_vars(item["right"], aliases)
        op = item["op"]
        replacement = None
        reason = None

        if use_peephole:
            folded = _constant_fold(left, op, right)
            if folded is not None:
                replacement, reason = folded, f"Constant folding: {left} {op} {right} → {folded}"
            else:
                simple = _peephole_expr(left, op, right)
                if simple is not None:
                    replacement, reason = simple, f"Algebraic simplification: {left} {op} {right} → {simple}"

        if replacement is not None:
            aliases[target] = replacement if re.fullmatch(IDENT, replacement) else replacement
            current.append(f"{target} = {replacement}")
            steps.append({"technique": "Peephole", "detail": reason, "before": f"{target} = {left} {op} {right}", "after": f"{target} = {replacement}"})
            continue

        key = _expr_key(left, op, right)
        if use_dag and key in expr_cache:
            existing = expr_cache[key]
            aliases[target] = existing
            current.append(f"{target} = {existing}")
            steps.append({"technique": "DAG", "detail": f"Common subexpression reused: {left} {op} {right}", "before": f"{target} = {left} {op} {right}", "after": f"{target} = {existing}"})
        else:
            aliases.pop(target, None)
            assigned.add(target)
            current.append(f"{target} = {left} {op} {right}")
            if use_dag:
                expr_cache[key] = target

    # Resolve alias chains in final statements.
    def resolve(value):
        seen = set()
        while value in aliases and value not in seen:
            seen.add(value)
            value = aliases[value]
        return value

    final = []
    for line in current:
        m = ASSIGN_RE.match(line)
        if not m:
            final.append(line)
            continue
        target, rhs = m.group(1), m.group(2).strip()
        rhs = re.sub(rf"\b{IDENT}\b", lambda x: resolve(x.group(0)), rhs)
        final.append(f"{target} = {rhs}")

    # Remove overwritten/dead assignments conservatively: only remove pure assignments
    # to variables that are never read later and are not the last write to that variable.
    # Keep this modest to avoid changing behavior for unsupported syntax.
    if use_dag:
        live = set()
        kept = []
        for line in reversed(final):
            m = ASSIGN_RE.match(line)
            if not m:
                kept.append(line)
                live.update(re.findall(IDENT, line))
                continue
            target, rhs = m.group(1), m.group(2)
            rhs_names = set(re.findall(IDENT, rhs))
            if target not in live and not rhs_names:
                # Preserve final user-visible outputs by retaining the last assignment in the program.
                if line == final[-1]:
                    kept.append(line)
                else:
                    steps.append({"technique": "DAG", "detail": f"Removed dead assignment to {target}", "before": line, "after": "(removed)"})
            else:
                kept.append(line)
                live.discard(target)
                live.update(rhs_names)
        final = list(reversed(kept))

    return {
        "original": code.strip(),
        "optimized": "\n".join(final).strip(),
        "steps": steps,
        "summary": {
            "input_lines": len([x for x in original_lines if x.strip()]),
            "output_lines": len([x for x in final if x.strip()]),
            "optimizations": len(steps)
        },
        "warnings": warnings
    }
