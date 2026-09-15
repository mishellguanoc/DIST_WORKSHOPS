import ldap

ldap_server = "ldap://localhost"
ldap_username = "uid=ismael,ou=People,dc=maki,dc=com"
ldap_password = "password"  # password introduced in ismael in user.ldif
# ldap_password = "password123"  # This is the incorrect password

try:
    conn = ldap.initialize(ldap_server)
    conn.simple_bind_s(ldap_username, ldap_password)
    print("Authentication successful!")
except ldap.INVALID_CREDENTIALS:
    print("Authentication failed!")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.unbind_s()
