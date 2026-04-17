# Database Indexing Strategy

This directory contains the indexing strategy for the National Research Graph database.

## Indexing Principles

1. **Performance First**: All indexes are designed to optimize query performance for the most common access patterns
2. **Resource Efficiency**: Indexes are carefully planned to minimize disk space and memory usage
3. **Maintenance**: Indexes are designed to be low-maintenance with minimal impact on write performance

## Index Implementation

The indexes are implemented using PostgreSQL's concurrent creation to avoid table locking.

## Index Monitoring

Regular monitoring of index usage is performed to identify and remove unused indexes.