# Activity 3 — Coordinator for the horizontally sharded "users" table.
# The two shards live on different MySQL servers, so no single UNION can span them.
# This script plays the coordinator: it routes queries by the shard key (id) and
# merges the partial results into the logical "users" table.
#
#   .\coordinator.ps1            -> query both shards, merge, sort by id
#   .\coordinator.ps1 -Id 5      -> route a point lookup to the one shard that owns id 5
param([int]$Id = -1)

$shards = @(
    @{ Name = 'shard1'; Container = 'mysql-primary'; Db = 'users_shard1' },  # even ids
    @{ Name = 'shard2'; Container = 'mysql-shard2';  Db = 'users_shard2' }   # odd ids
)

# Routing rule: even id -> Shard 1, odd id -> Shard 2
function Get-ShardFor([int]$key) { if ($key % 2 -eq 0) { $shards[0] } else { $shards[1] } }

function Invoke-ShardQuery($shard, [string]$sql) {
    # -N: no header, -B: tab-separated. MYSQL_PWD avoids the password warning on stderr.
    $lines = docker exec -e MYSQL_PWD=root $shard.Container mysql -uroot -N -B $shard.Db -e $sql
    foreach ($line in $lines) {
        $f = $line -split "`t"
        [pscustomobject]@{ id = [int]$f[0]; name = $f[1]; email = $f[2]; city = $f[3]; shard = $shard.Name }
    }
}

$sql = 'SELECT id, name, email, city FROM users'
if ($Id -ge 0) {
    $target = Get-ShardFor $Id
    Write-Host "Routing id=$Id to $($target.Name) ($($target.Container))"
    Invoke-ShardQuery $target "$sql WHERE id = $Id" | Format-Table -AutoSize
    return
}

$all = foreach ($s in $shards) {
    $part = @(Invoke-ShardQuery $s $sql)
    Write-Host "$($s.Name) ($($s.Container)): $($part.Count) rows"
    $part
}
Write-Host "`nReconstructed logical table users (shard1 UNION ALL shard2, ordered by id):"
$all | Sort-Object id | Format-Table -AutoSize
