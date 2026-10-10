# Activity 5 — Read-after-write check, automated end to end.
#
#   .\raw_check.ps1             -> normal run: write on primary, immediate replica read, GTID wait, read again
#   .\raw_check.ps1 -ForceLag   -> same, but the replica's SQL (applier) thread is paused first so the
#                                  stale read and the WAIT timeout (1) are guaranteed; it is restarted at the end.
param([switch]$ForceLag)

function Sql([string]$container, [string]$sql) {
    # MYSQL_PWD avoids the password warning on stderr; -t prints a table.
    docker exec -e MYSQL_PWD=root $container mysql -uroot -t lab -e $sql
}
$read = 'SELECT id, balance, updated_at FROM accounts WHERE id=1'

if ($ForceLag) {
    Write-Host '== Simulating replication lag: STOP REPLICA SQL_THREAD (IO thread keeps downloading events)'
    Sql mysql-replica 'STOP REPLICA SQL_THREAD;'
}

Write-Host '== 1. Write on the PRIMARY, then read it on the primary and IMMEDIATELY on the replica'
# Both statements run inside the primary container, back to back, to keep the gap as small as possible.
docker exec -e MYSQL_PWD=root mysql-primary sh -c "echo '-- primary (after write):'; mysql -uroot -t lab -e 'UPDATE accounts SET balance=balance+1 WHERE id=1; $read;' && echo '-- replica (immediately after):' && mysql -uroot -h mysql-replica -t lab -e '$read;'"

Write-Host '== 2. GTID set executed on the primary (includes the write above)'
$gtid = (docker exec -e MYSQL_PWD=root mysql-primary mysql -uroot -N -B -e 'SELECT @@GLOBAL.gtid_executed') -join ''
$gtid = $gtid -replace '\n', ''
Write-Host "   $gtid"

Write-Host '== 3. On the replica: WAIT_FOR_EXECUTED_GTID_SET(<set>, 5), then read'
Sql mysql-replica "SELECT WAIT_FOR_EXECUTED_GTID_SET('$gtid', 5) AS wait_result; $read;"

if ($ForceLag) {
    Write-Host '== Restarting the applier: START REPLICA SQL_THREAD, then wait again'
    Sql mysql-replica 'START REPLICA SQL_THREAD;'
    Sql mysql-replica "SELECT WAIT_FOR_EXECUTED_GTID_SET('$gtid', 5) AS wait_result; $read;"
}
Write-Host 'wait_result: 0 = replica has applied the write (safe to read), 1 = timeout (replica still behind)'
