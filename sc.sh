#!/bin/bash

# Create the root directory and navigate into it
mkdir -p mysql-sharding-lab
cd mysql-sharding-lab || exit

# Create the subdirectories
mkdir -p shard0 shard1 proxysql

# Create the configuration and compose files
touch docker-compose.yml
touch shard0/primary.cnf
touch shard0/replica.cnf
touch shard1/primary.cnf
touch shard1/replica.cnf
touch proxysql/proxysql.cnf

echo "✅ Successfully created the mysql-sharding-lab folder structure!"
