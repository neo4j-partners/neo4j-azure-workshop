# Neo4j Backup and Restore Guide

This guide covers the backup and restore scripts for managing Neo4j database snapshots.

## Overview

The backup/restore system exports and imports:
- **Nodes** with all labels and properties
- **Relationships** with types and properties
- **Schema** (indexes and constraints)

Data is stored in newline-delimited JSON format compatible with APOC export.

## Quick Start

### Backup
```bash
uv run python scripts/backup_neo4j.py /path/to/backup/directory
```

### Restore (Full)
```bash
uv run python scripts/restore_neo4j.py --file /path/to/backup/financial_backup.json -f
```

### Restore (Sample - Fast Testing)
```bash
uv run python scripts/restore_neo4j.py --file /path/to/backup/financial_backup.json --sample -f
```

## Backup Script

### Usage
```bash
uv run python scripts/backup_neo4j.py <directory>
```

### What It Does
1. Connects to Neo4j using credentials from `.env`
2. Exports database statistics (node/relationship counts)
3. Exports schema (indexes and constraints)
4. Exports all data using APOC (or Cypher fallback if APOC unavailable)
5. Writes two files:
   - `financial_backup.json` - The data export
   - `financial_backup.checksum.json` - Statistics and schema

### Output Files

**financial_backup.json** - Newline-delimited JSON:
```json
{"type":"node","id":"4:xxx:0","labels":["Person"],"properties":{"name":"Alice"}}
{"type":"node","id":"4:xxx:1","labels":["Company"],"properties":{"name":"Acme"}}
{"type":"relationship","id":"5:xxx:0","label":"WORKS_FOR","start":{"id":"4:xxx:0"},"end":{"id":"4:xxx:1"},"properties":{}}
```

**financial_backup.checksum.json** - Metadata and schema:
```json
{
  "timestamp": "2025-11-26T14:17:09.858803+00:00",
  "nodes": 2145,
  "relationships": 5071,
  "embeddings": 390,
  "vector_index_name": "chunkEmbeddings",
  "schema": {
    "indexes": [...],
    "constraints": [...]
  }
}
```

### Environment Variables
Required in `.env`:
- `NEO4J_URI` - Database connection URI
- `NEO4J_USERNAME` - Database username
- `NEO4J_PASSWORD` - Database password

Optional:
- `NEO4J_VECTOR_INDEX_NAME` - Name of vector index to count embeddings

## Restore Script

### Usage
```bash
uv run python scripts/restore_neo4j.py [options]
```

### Options
| Option | Short | Description |
|--------|-------|-------------|
| `--file PATH` | | Use local backup file instead of GitHub |
| `--sample` | `-s` | Sample mode: 100 nodes, 100 relationships, all schema |
| `--force` | `-f` | Skip confirmation prompt |

### What It Does
1. Loads schema from checksum file (or GitHub)
2. Parses backup data (applies limits in sample mode)
3. Clears existing database data and schema
4. Restores schema (constraints first, then indexes)
5. Creates temporary index for fast relationship lookups
6. Batch-inserts nodes using `UNWIND`
7. Batch-inserts relationships using `UNWIND` with index
8. Cleans up temporary restore artifacts

### Data Sources

**Local file:**
```bash
uv run python scripts/restore_neo4j.py --file /path/to/financial_backup.json
```
Schema is loaded from `financial_backup.checksum.json` in the same directory.

**GitHub (default):**
```bash
uv run python scripts/restore_neo4j.py
```
Streams from the workshop repository's snapshot.

### Sample Mode

Sample mode (`--sample` or `-s`) is designed for fast testing:
- Restores only **100 nodes** and **100 relationships**
- Restores **all indexes and constraints**
- Only includes relationships between the sampled nodes
- Completes in seconds instead of minutes

```bash
# Fast test restore
uv run python scripts/restore_neo4j.py --file /path/to/backup/financial_backup.json -s -f
```

## Schema Support

### Constraints
| Type | Supported |
|------|-----------|
| UNIQUENESS | ✅ |
| NODE_KEY | ✅ |
| NODE_PROPERTY_EXISTENCE | ✅ |

### Indexes
| Type | Supported |
|------|-----------|
| RANGE | ✅ |
| VECTOR | ✅ |
| TEXT | ✅ |
| FULLTEXT | ✅ |
| LOOKUP | ⏭️ Skipped (system-managed) |

## Performance Characteristics

### Backup
- Uses APOC streaming export when available
- Falls back to batched Cypher queries (1000 records/batch)
- Single database connection for all operations

### Restore
- Batched inserts using `UNWIND` (500 records/batch)
- Temporary index on `_backup_id` for O(1) relationship lookups
- Batched cleanup operations (10000 records/batch)

### Typical Times (2000 nodes, 5000 relationships)
| Operation | Full | Sample |
|-----------|------|--------|
| Backup | ~30s | N/A |
| Restore | ~2-3min | ~5-10s |

## Troubleshooting

### "APOC not available"
The backup script falls back to Cypher-based export automatically. No action needed.

### "Checksum file not found"
Ensure `financial_backup.checksum.json` exists in the same directory as the backup file. This file contains the schema needed for restore.

### Restore is slow
- Use `--sample` for testing
- Full restore creates indexes before data import, which is optimal
- Relationship creation is O(1) due to temporary index

### "Vector index creation failed"
Vector indexes require specific Neo4j versions (5.x+). The restore continues with a warning.

## Example Workflow

### Development Testing
```bash
# Quick schema + sample data restore
uv run python scripts/restore_neo4j.py \
  --file /path/to/workshop-financial-data/snapshot/financial_backup.json \
  --sample --force

# Verify schema
# In Neo4j Browser: SHOW INDEXES; SHOW CONSTRAINTS;
```

### Full Database Restore
```bash
# Backup current state first
uv run python scripts/backup_neo4j.py ./backup-$(date +%Y%m%d)

# Restore from snapshot
uv run python scripts/restore_neo4j.py \
  --file /path/to/snapshot/financial_backup.json \
  --force
```

### CI/CD Integration
```bash
# Non-interactive restore for automation
uv run python scripts/restore_neo4j.py --sample --force
echo $?  # 0 = success, 1 = failure
```
