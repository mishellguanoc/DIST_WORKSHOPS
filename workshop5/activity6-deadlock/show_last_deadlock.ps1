# Activity 6 — Optional evidence: InnoDB's report of the most recent deadlock
# (both transactions, the locks each held, the lock each waited for, and which one was rolled back).
$status = docker exec -e MYSQL_PWD=root mysql-primary mysql -uroot -e 'SHOW ENGINE INNODB STATUS\G'
$start = [array]::IndexOf($status, ($status | Where-Object { $_ -match 'LATEST DETECTED DEADLOCK' } | Select-Object -First 1))
if ($start -lt 0) { Write-Host 'No deadlock recorded since the server started.'; return }
$end = [array]::IndexOf($status, ($status | Where-Object { $_ -match '^TRANSACTIONS$' } | Select-Object -First 1))
$status[($start - 1)..($end - 2)]
