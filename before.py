# order_stuff.py
def proc(uid, c, f, st, addr, cc):
    # calc total
    t = 0.0
    itms = c.get("items", [])
    for it in itms:
        t += float(it.get("p", 0.0)) * int(it.get("q", 0))

    # apply discount if any
    if "disc" in c:
        d = float(c["disc"])  # e.g., 0.1
        t = t - t * d

    # fast shipping surcharge
    if f:
        t += 9.99

    # tax? (magic number; NY?)
    t = t * 1.08875

    # validate address (super naive)
    if not addr or len(addr.get("zip", "")) < 5:
        raise Exception("bad addr")

    # choose shipper
    sp = 0
    if st == "std":
        sp = 1
    elif st == "xp":
        sp = 2

    # process payment
    if not cc or len(cc) < 12:
        return -1  # error
    ok = cc.startswith("4") or cc.startswith("5")  # visa/master only
    if not ok:
        return -2  # another error

    # ship
    if sp == 1:
        label = "STD-" + addr["zip"]
    elif sp == 2:
        label = "EXP-" + addr["zip"]
    else:
        label = "UNK-" + addr["zip"]

    print("UID=", uid, "TOTAL=", t, "LABEL=", label)
    return t



# Sample Call
cart = {
    "items": [
        {"p": 19.99, "q": 2},  # price and quantity
        {"p": 5.49, "q": 4}
    ],
    "disc": 0.1  # 10% discount
}

address = {
    "zip": "12345"
}

credit_card = "4111111111111111"  # Example Visa card number

proc(uid=1, c=cart, f=True, st="xp", addr=address, cc=credit_card)