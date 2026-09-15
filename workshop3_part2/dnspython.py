import dns.resolver
import dns.reversename
import dns.message
import dns.query

# ---------- A1: lookup básico (A) ----------
def a1_basico():
    resp = dns.resolver.resolve("yachaytech.edu.ec", "A")
    for r in resp:
        print("IP:", r.address)

# ---------- A2: reverse lookup (PTR) ----------
def a2_reverso():
    rev_name = dns.reversename.from_address("8.8.8.8")
    resp = dns.resolver.resolve(rev_name, "PTR")
    for r in resp:
        print("Dominio:", r.target)

# ---------- A3: servidor DNS específico ----------
def a3_servidor_custom():
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ["1.1.1.1"]  # Cloudflare
    resp = resolver.resolve("hpc.cedia.edu.ec", "A")
    for r in resp:
        print("IP (via 1.1.1.1):", r.address)

# ---------- A4: MX ----------
def a4_mx():
    resp = dns.resolver.resolve("yachaytech.edu.ec", "MX")
    for r in resp:
        print("MX:", r.preference, r.exchange)

# ---------- A5: NS ----------
def a5_ns():
    resp = dns.resolver.resolve("yachaytech.edu.ec", "NS")
    for r in resp:
        print("NS:", r.target)

# ---------- A6: SOA ----------
def a6_soa():
    resp = dns.resolver.resolve("yachaytech.edu.ec", "SOA")
    for r in resp:
        print("Primary NS:", r.mname)
        print("Responsible:", r.rname)
        print("Serial:", r.serial, "Refresh:", r.refresh, "Retry:", r.retry,
              "Expire:", r.expire, "Minimum:", r.minimum)

# ---------- A7: CNAME ----------
def a7_cname():
    try:
        resp = dns.resolver.resolve("www.microsoft.com", "CNAME")
        for r in resp:
            print("CNAME:", r.target)
    except dns.resolver.NoAnswer:
        print("No tiene registro CNAME")

# ---------- A8: modo debug (query/response crudo) ----------
def a8_debug():
    q = dns.message.make_query("yachaytech.edu.ec", "A")
    print("Query enviada:\n", q)
    resp = dns.query.udp(q, "8.8.8.8")  # o el resolver que quieras usar
    print("Respuesta cruda:\n", resp)

# ---------- A9: dominio inexistente ----------
def a9_inexistente():
    try:
        dns.resolver.resolve("nonexistdomain12345.com", "A")
    except dns.resolver.NXDOMAIN:
        print("NXDOMAIN: el dominio no existe")
    except dns.resolver.NoNameservers:
        print("No hay servidores que respondan")


if __name__ == "__main__":
    for nombre, fn in [
        ("A1", a1_basico), ("A2", a2_reverso), ("A3", a3_servidor_custom),
        ("A4", a4_mx), ("A5", a5_ns), ("A6", a6_soa),
        ("A7", a7_cname), ("A8", a8_debug), ("A9", a9_inexistente),
    ]:
        print(f"\n--- {nombre} ---")
        try:
            fn()
        except Exception as e:
            print("Error:", e)
