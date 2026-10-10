# Activity 3 Challenge — Coordinator for the vertically sharded user data.
# Node 1 (mysql-primary) holds identity(id, name); Node 2 (mysql-shard2) holds contact(id, email, city).
# The full user row only exists logically: the coordinator joins both fragments on id.
#
#   .\vertical_coordinator.ps1                -> rebuild every user (identity JOIN contact)
#   .\vertical_coordinator.ps1 -City Quito    -> filter on Node 2 first, then fetch only matching names from Node 1
param([string]$City = '')

function Invoke-Node([string]$container, [string]$db, [string]$sql) {
    # -N: no header, -B: tab-separated. MYSQL_PWD avoids the password warning on stderr.
    docker exec -e MYSQL_PWD=root $container mysql -uroot -N -B $db -e $sql | ForEach-Object { , ($_ -split "`t") }
}

# 1. Contact fragment from Node 2 (optionally filtered by city, so only matching ids travel)
$contactSql = 'SELECT id, email, city FROM contact'
if ($City) { $contactSql += " WHERE city = '$($City -replace "'", "''")'" }
$contact = @{}
foreach ($f in Invoke-Node 'mysql-shard2' 'users_contact' $contactSql) { $contact[[int]$f[0]] = $f }
Write-Host "Node 2 (mysql-shard2)  contact : $($contact.Count) rows"
if ($contact.Count -eq 0) { return }

# 2. Identity fragment from Node 1, only for the ids we need
$ids = ($contact.Keys | Sort-Object) -join ','
$identity = @{}
foreach ($f in Invoke-Node 'mysql-primary' 'users_identity' "SELECT id, name FROM identity WHERE id IN ($ids)") { $identity[[int]$f[0]] = $f }
Write-Host "Node 1 (mysql-primary) identity: $($identity.Count) rows"

# 3. Join on id at the coordinator
Write-Host "`nReconstructed users (identity JOIN contact ON id):"
$contact.Keys | Sort-Object | ForEach-Object {
    [pscustomobject]@{
        id    = $_
        name  = if ($identity.ContainsKey($_)) { $identity[$_][1] } else { '<missing on node 1>' }
        email = $contact[$_][1]
        city  = $contact[$_][2]
    }
} | Format-Table -AutoSize
