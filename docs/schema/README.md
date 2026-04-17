# National Research Graph Database Schema

This directory contains the database schema and related documentation for the National Research Graph application.

## Schema Files

1. `researcher_db.sql` - Main database schema definition
2. `knowledge_graph_design.md` - Knowledge graph design documentation
3. `vector_metadata_taxonomy.md` - Vector metadata taxonomy documentation
4. `neon_integration.md` - Neon Postgres integration documentation

## Migrations

The `migrations` directory contains SQL migration scripts:

1. `001_init_schema.sql` - Initial schema setup
2. `002_neon_branching_strategy.sql` - Neon branching strategy setup
3. `003_neon_connection_pooling.sql` - Connection pooling optimization
4. `004_dpdp_compliance.sql` - Data Privacy and DPDP compliance
5. `005_kong_integration.sql` - Kong API Gateway integration

## Indexes

The `indexes` directory contains index optimization scripts:

1. `researcher_db_indexes.sql` - Index optimization script
2. `README.md` - Indexing strategy documentation

## Implementation Notes

The schema is designed with the following considerations:

1. **Neon Postgres Integration**: Optimized for Neon's serverless Postgres platform
2. **Data Privacy Compliance**: Includes features for DPDP compliance
3. **Kong API Gateway Integration**: Supports API key management and rate limiting
4. **Performance Optimization**: Includes indexing strategies for query performance
5. **Branching Strategy**: Supports Neon's branching features for development and testing