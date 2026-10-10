# Workshop 5 — Distributed Databases

All commands are for **PowerShell** and are run from this `workshop5/` folder.
PowerShell 5.1 has no `<` redirection, so SQL files are piped in with
`Get-Content <file> -Raw | docker exec -i <container> mysql -uroot -proot`.

## Activity 1 — Docker topology

| Container       | Host port | Role                                              |
|-----------------|-----------|---------------------------------------------------|
| `mysql-primary` | 3306      | Writable source (binlog + GTID), also Shard 1     |
| `mysql-replica` | 3307      | Read-only replica of `mysql-primary`              |
| `mysql-shard2`  | 3308      | Independent node, Shard 2 (no replication)        |

```powershell
docker compose up -d
docker ps
# wait ~15-30 s for first-time initialization, then:
docker exec mysql-primary mysqladmin ping -uroot -proot
docker exec mysql-replica mysqladmin ping -uroot -proot
docker exec mysql-shard2 mysqladmin ping -uroot -proot
```

Expected: three containers `Up` and three `mysqld is alive` lines.

## Activity 2 — Primary–replica replication (`activity2-replication/`)

```powershell
# 1. Replication account on the primary
Get-Content activity2-replication\01_primary_repl_user.sql -Raw | docker exec -i mysql-primary mysql -uroot -proot
# 2. Point the replica at the primary (GTID auto-position) and start it
Get-Content activity2-replication\02_replica_setup.sql -Raw | docker exec -i mysql-replica mysql -uroot -proot
# 3. Check status: Replica_IO_Running = Yes and Replica_SQL_Running = Yes
docker exec mysql-replica mysql -uroot -proot -e "SHOW REPLICA STATUS\G"
# 4. Write on the primary, read on the replica
Get-Content activity2-replication\03_test_data.sql -Raw | docker exec -i mysql-primary mysql -uroot -proot lab
docker exec mysql-replica mysql -uroot -proot lab -e "SELECT * FROM replication_test;"
```

Note: `read_only=ON` does not stop accounts with SUPER (like `root`); `super_read_only=ON` would.
Never write on the replica directly, or it diverges from the primary.

## Activity 3 — Horizontal sharding (`activity3-sharding/`)

Rule (shard key = `id`): **even → Shard 1 (`mysql-primary`, `users_shard1`)**, **odd → Shard 2 (`mysql-shard2`, `users_shard2`)**.

```powershell
Get-Content activity3-sharding\01_schema_shard1.sql -Raw | docker exec -i mysql-primary mysql -uroot -proot
Get-Content activity3-sharding\02_schema_shard2.sql -Raw | docker exec -i mysql-shard2 mysql -uroot -proot
Get-Content activity3-sharding\03_data_shard1.sql -Raw | docker exec -i mysql-primary mysql -uroot -proot
Get-Content activity3-sharding\04_data_shard2.sql -Raw | docker exec -i mysql-shard2 mysql -uroot -proot
# Query each fragment separately
docker exec mysql-primary mysql -uroot -proot -t -e "SELECT * FROM users_shard1.users;"
docker exec mysql-shard2 mysql -uroot -proot -t -e "SELECT * FROM users_shard2.users;"
# Coordinator: merge both fragments into the logical table, or route one id
.\activity3-sharding\coordinator.ps1
.\activity3-sharding\coordinator.ps1 -Id 5
```

### Challenge — Vertical sharding (`activity3-sharding/vertical/`)

Node 1 (`mysql-primary`) → `users_identity.identity(id, name)`;
Node 2 (`mysql-shard2`) → `users_contact.contact(id, email, city)`. Rebuilt by joining on `id`.

```powershell
Get-Content activity3-sharding\vertical\01_identity_node1.sql -Raw | docker exec -i mysql-primary mysql -uroot -proot
Get-Content activity3-sharding\vertical\02_contact_node2.sql -Raw | docker exec -i mysql-shard2 mysql -uroot -proot
docker exec mysql-primary mysql -uroot -proot -t -e "SELECT * FROM users_identity.identity;"
docker exec mysql-shard2 mysql -uroot -proot -t -e "SELECT * FROM users_contact.contact;"
.\activity3-sharding\vertical\vertical_coordinator.ps1
.\activity3-sharding\vertical\vertical_coordinator.ps1 -City Quito
```

The data scripts use plain `INSERT`; running them twice gives a duplicate-key error (data is already there).

## Activity 4 — Lost update and locking (`activity4-locking/`)

```powershell
# Create/reset the accounts table (Alice=1000, Bob=1000)
Get-Content activity4-locking\00_setup_accounts.sql -Raw | docker exec -i mysql-primary mysql -uroot -proot lab
# Open TWO terminals, both connected to the primary:
docker exec -it mysql-primary mysql -uroot -proot lab
```

Then paste the steps of `4.1_sessionA.sql` / `4.1_sessionB.sql` **one step at a time** in the global
step order (1 → A, 2 → B, 3 → A, ...). Expected final balance: **950** (lost update).

```powershell
Get-Content activity4-locking\4.2_reset.sql -Raw | docker exec -i mysql-primary mysql -uroot -proot lab
```

Then follow `4.2_sessionA.sql` / `4.2_sessionB.sql`. Session B hangs at `SELECT ... FOR UPDATE` until A
commits. Expected final balance: **1050**.

Optional third terminal while B is waiting:

```powershell
Get-Content activity4-locking\show_lock_waits.sql -Raw | docker exec -i mysql-primary mysql -uroot -proot -t
```

A blocked statement gives up after 50 s (`innodb_lock_wait_timeout`) with `ERROR 1205`; just `ROLLBACK` and repeat.

## Activity 5 — Read-after-write consistency (`activity5-raw/`)

Manual version (as in the workshop):

```powershell
Get-Content activity5-raw\01_write_primary.sql -Raw | docker exec -i mysql-primary mysql -uroot -proot lab
Get-Content activity5-raw\02_read_replica.sql -Raw | docker exec -i mysql-replica mysql -uroot -proot lab
Get-Content activity5-raw\03_capture_gtid.sql -Raw | docker exec -i mysql-primary mysql -uroot -proot
docker exec -it mysql-replica mysql -uroot -proot
# inside mysql: paste 04_wait_and_read_replica.sql with the copied GTID set
```

Automated version:

```powershell
.\activity5-raw\raw_check.ps1            # usually: replica already up to date, WAIT returns 0
.\activity5-raw\raw_check.ps1 -ForceLag  # pauses the replica applier: stale read + WAIT returns 1, then 0
```

## Activity 6 — Deadlock and prevention (`activity6-deadlock/`)

```powershell
Get-Content activity6-deadlock\00_reset.sql -Raw | docker exec -i mysql-primary mysql -uroot -proot lab
# TWO terminals:
docker exec -it mysql-primary mysql -uroot -proot lab
```

- **6.1** — follow `6.1_sessionA.sql` / `6.1_sessionB.sql` step by step. The second session to request
  the other's row gets `ERROR 1213 (40001): Deadlock found...`; the survivor commits (1010 / 990).
- **6.2** — reset again, then follow `6.2_sessionA.sql` / `6.2_sessionB.sql`. Both lock rows 1 and 2
  in the same order (`ORDER BY id FOR UPDATE`): B only waits, no deadlock (final 1020 / 980).

Optional: InnoDB's report of the last deadlock (who held / waited for which row, who was rolled back):

```powershell
.\activity6-deadlock\show_last_deadlock.ps1
```
