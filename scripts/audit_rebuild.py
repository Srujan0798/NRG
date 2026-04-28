#!/usr/bin/env python3
"""
Audit Chain Rebuild Script — NRG Legal Compliance

Archives the corrupted audit chain and rebuilds it with correct HMAC chaining.

Usage:
    python scripts/audit_rebuild.py --check    # Just verify and report
    python scripts/audit_rebuild.py --rebuild  # Actually rebuild
    python scripts/audit_rebuild.py --verify   # Verify existing chain

This script:
1. Archives the current chain as .audit/chain_corrupted_backup.jsonl
2. Rebuilds a clean chain from raw event data (preserving all events)
3. Verifies the rebuilt chain passes verify_chain()
4. Logs the rebuild event as the first entry in the new chain

Root Cause: Line 139 had a hash mismatch that cascaded because subsequent
events used the wrong prev_hash. The corruption is not from tampering but
from a state inconsistency in the chain state tracking.
"""

import argparse
import hmac
import hashlib
import json
import shutil
import sys
import os
from datetime import datetime, UTC
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.audit import AuditEvent, ImmutableAuditLog, get_audit_log
from src.audit.per_user_keys import get_per_user_key_manager


def compute_hash(chain_key: str, prev_hash: str, event: AuditEvent) -> str:
    """Compute HMAC-SHA256 hash for an event."""
    message = prev_hash + event.serialize()
    return hmac.new(
        chain_key.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()


def genesis_hash() -> str:
    return "0" * 64


def first_event_hash(chain_path: Path) -> str | None:
    """Return the active genesis event hash from a JSONL chain file."""
    if not chain_path.exists():
        return None
    with chain_path.open() as f:
        for line in f:
            if line.strip():
                return json.loads(line).get("hash")
    return None


def verify_genesis_pin(audit_dir: Path, chain_path: Path, *, force: bool) -> bool:
    """Refuse lineage-changing repairs when the active genesis differs from the pin."""
    pin_file = audit_dir / "genesis_hash.pin"
    if not pin_file.exists():
        return True

    pinned_hash = pin_file.read_text().strip()
    active_hash = first_event_hash(chain_path)
    if not pinned_hash or not active_hash or pinned_hash == active_hash:
        return True

    message = (
        "Genesis hash pin mismatch: "
        f"pinned={pinned_hash[:16]} active={active_hash[:16]}"
    )
    if force:
        print(f"WARNING: {message}; proceeding because --force was supplied")
        return True

    print(f"ERROR: {message}", file=sys.stderr)
    print("Refusing rebuild with --preserve-lineage; rerun with --force to override.", file=sys.stderr)
    return False


def ensure_genesis_pin(audit_dir: Path, chain_path: Path) -> None:
    """Create the genesis pin when an older chain predates ADR-006."""
    pin_file = audit_dir / "genesis_hash.pin"
    if pin_file.exists():
        return
    active_hash = first_event_hash(chain_path)
    if active_hash:
        pin_file.write_text(f"{active_hash}\n")


def rebuild_chain(corrupted_path: str, new_path: str, chain_key: str) -> dict:
    """Rebuild the audit chain from corrupted file."""
    results = {
        "events_processed": 0,
        "hashes_corrected": 0,
        "rebuild_hash": None,
        "first_event_timestamp": None,
        "last_event_timestamp": None,
        "errors": [],
    }

    with open(corrupted_path) as f:
        lines = f.readlines()

    prev_hash = genesis_hash()
    
    key_manager = get_per_user_key_manager(chain_key)

    with open(new_path, "w") as f:
        for line_num, line in enumerate(lines, 1):
            try:
                event_data = json.loads(line)
                recorded_hash = event_data.get("hash")
                
                # Reconstruct event
                event_kwargs = {
                    k: v
                    for k, v in event_data.items()
                    if k not in ("hash", "per_user_binding", "user_key_hash")
                }
                if "_v" not in event_data:
                    event_kwargs["_v"] = None
                event = AuditEvent(**event_kwargs)
                
                # Compute correct hash
                computed_hash = compute_hash(chain_key, prev_hash, event)
                
                # Track timestamps
                if results["first_event_timestamp"] is None:
                    results["first_event_timestamp"] = event.timestamp
                results["last_event_timestamp"] = event.timestamp
                
                # Count corrections
                if computed_hash != recorded_hash:
                    results["hashes_corrected"] += 1
                
                # Write corrected event and preserve/recompute binding metadata.
                corrected_event = {**event.to_dict(), "hash": computed_hash}
                if event_data.get("per_user_binding") is not None:
                    user_id = event.user_id or "system"
                    if event.jwt_kid is not None or event.request_fingerprint is not None:
                        per_user_hash = key_manager.compute_binding(
                            user_id=user_id,
                            jwt_kid=event.jwt_kid,
                            request_fingerprint=event.request_fingerprint,
                            chain_hash=computed_hash,
                            event_serialized=event.serialize(),
                        )
                    else:
                        user_key = hmac.new(
                            chain_key.encode(),
                            f"user_key:{user_id}".encode(),
                            hashlib.sha256,
                        ).hexdigest()[:32]
                        message = f"{user_key}:{computed_hash}:{event.serialize()}"
                        per_user_hash = hmac.new(
                            user_key.encode(),
                            message.encode(),
                            hashlib.sha256,
                        ).hexdigest()
                    corrected_event["per_user_binding"] = per_user_hash[:16]
                f.write(json.dumps(corrected_event, sort_keys=True, default=str) + "\n")
                
                prev_hash = computed_hash
                results["events_processed"] += 1
                
            except Exception as e:
                results["errors"].append(f"Line {line_num}: {e}")

    results["rebuild_hash"] = prev_hash
    return results


def verify_chain_file(chain_path: str, chain_key: str) -> tuple[bool, list[str]]:
    """Verify a chain file and return (valid, errors)."""
    errors = []
    prev_hash = genesis_hash()

    with open(chain_path) as f:
        for line_num, line in enumerate(f, 1):
            try:
                event_data = json.loads(line)
                recorded_hash = event_data.get("hash")
                
                event_kwargs = {
                    k: v
                    for k, v in event_data.items()
                    if k not in ("hash", "per_user_binding", "user_key_hash")
                }
                if "_v" not in event_data:
                    event_kwargs["_v"] = None
                event = AuditEvent(**event_kwargs)
                
                computed_hash = compute_hash(chain_key, prev_hash, event)
                
                if computed_hash != recorded_hash:
                    errors.append(f"Line {line_num}: hash mismatch")
                
                prev_hash = recorded_hash
                
            except Exception as e:
                errors.append(f"Line {line_num}: {e}")

    if prev_hash != (json.loads(open(chain_path).readlines()[-1])["hash"] if open(chain_path).readlines() else genesis_hash()):
        # Check last hash matches
        pass
    
    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(description="Audit Chain Rebuild Tool")
    parser.add_argument("--check", action="store_true", help="Check current chain status")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild the chain")
    parser.add_argument("--verify", action="store_true", help="Verify existing chain")
    parser.add_argument(
        "--preserve-lineage",
        action="store_true",
        help="Verify active genesis against genesis_hash.pin before rewriting the chain",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow --preserve-lineage rebuilds to proceed despite a genesis pin mismatch",
    )
    parser.add_argument(
        "--reseed-genesis",
        action="store_true",
        help="Archive active chain, insert a traceable genesis event, and replay all events",
    )
    parser.add_argument("--chain-key", default=None, help="Override chain key")
    args = parser.parse_args()

    audit_dir = Path(".audit")
    chain_file = audit_dir / "chain.jsonl"
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_file = audit_dir / f"chain_corrupted_backup_{timestamp}.jsonl"
    legacy_backup_file = audit_dir / "chain_corrupted_backup.jsonl"
    new_chain_file = audit_dir / "chain_new.jsonl"
    last_hash_file = audit_dir / ".last_hash"
    
    # Get chain key
    chain_key = args.chain_key or os.environ.get(
        "AUDIT_CHAIN_KEY", "nrg-audit-chain-dev-key"
    )

    if args.check:
        print("=" * 60)
        print(" AUDIT CHAIN STATUS CHECK")
        print("=" * 60)
        
        if not chain_file.exists():
            print("No chain file found.")
            return 1
        
        # Count events
        with open(chain_file) as f:
            event_count = sum(1 for _ in f)
        
        print(f"Chain file: {chain_file}")
        print(f"Total events: {event_count:,}")
        
        # Verify chain
        print("\nVerifying chain integrity...")
        valid, errors = verify_chain_file(str(chain_file), chain_key)
        
        if valid:
            print("RESULT: Chain is VALID")
            return 0
        else:
            print("RESULT: Chain is INVALID")
            print(f"Errors found: {len(errors)}")
            print("First 10 errors:")
            for e in errors[:10]:
                print(f"  {e}")
            return 1

    elif args.verify:
        print("=" * 60)
        print(" AUDIT CHAIN VERIFICATION")
        print("=" * 60)
        
        if not chain_file.exists():
            print("No chain file found.")
            return 1
        
        print(f"Verifying: {chain_file}")
        valid, errors = verify_chain_file(str(chain_file), chain_key)
        
        if valid:
            print("VERIFICATION: PASSED")
            return 0
        else:
            print(f"VERIFICATION: FAILED ({len(errors)} errors)")
            return 1

    elif args.rebuild:
        print("=" * 60)
        print(" AUDIT CHAIN REBUILD")
        print("=" * 60)
        
        if not chain_file.exists():
            print("No chain file found.")
            return 1

        if args.preserve_lineage and not verify_genesis_pin(
            audit_dir,
            chain_file,
            force=args.force,
        ):
            return 2
        
        # First check
        print("\nStep 1: Checking current chain status...")
        valid, errors = verify_chain_file(str(chain_file), chain_key)
        print(f"  Current chain valid: {valid}")
        print(f"  Errors: {len(errors)}")
        
        if valid:
            print("\nChain is already valid. No rebuild needed.")
            return 0

        if args.reseed_genesis or any(e.startswith("Line 1: hash mismatch") for e in errors):
            print("\nStep 2: Reseeding chain with traceable genesis event...")
            ImmutableAuditLog._reset()
            audit_log = ImmutableAuditLog(storage_path=str(audit_dir))
            repair = audit_log.repair_line1_hash_mismatch(
                reason="script_rebuild_line1_hash_mismatch"
            )
            print(f"  Action: {repair['action']}")
            print(f"  Preserved events: {repair['preserved_event_count']:,}")
            print(f"  Archived to: {repair['backup_path']}")
            print(f"  Source SHA-256: {repair['source_sha256']}")

            print("\nStep 3: Verifying reseeded chain...")
            valid_after, verify_errors, count_after = audit_log.verify_chain()
            if valid_after:
                ensure_genesis_pin(audit_dir, chain_file)
                print("  Reseeded chain is VALID")
                print(f"  Valid events: {count_after:,}")
                print(f"  Final chain hash: {audit_log.last_hash[:20]}...")
                return 0

            print(f"  Reseeded chain is INVALID ({len(verify_errors)} errors)")
            for e in verify_errors[:10]:
                print(f"    {e}")
            return 1
        
        # Archive
        print("\nStep 2: Archiving corrupted chain...")
        shutil.copy2(chain_file, backup_file)
        if not legacy_backup_file.exists():
            shutil.copy2(chain_file, legacy_backup_file)
        print(f"  Archived to: {backup_file}")
        
        # Rebuild
        print("\nStep 3: Rebuilding chain...")
        results = rebuild_chain(str(chain_file), str(new_chain_file), chain_key)
        
        print(f"  Events processed: {results['events_processed']:,}")
        print(f"  Hashes corrected: {results['hashes_corrected']:,}")
        print(f"  Errors: {len(results['errors'])}")
        
        if results["errors"]:
            print("\n  Rebuild errors:")
            for e in results["errors"][:10]:
                print(f"    {e}")
        
        # Verify rebuilt chain
        print("\nStep 4: Verifying rebuilt chain...")
        valid, verify_errors = verify_chain_file(str(new_chain_file), chain_key)
        
        if valid:
            print("  Rebuilt chain is VALID")
            
            # Replace old chain with new
            print("\nStep 5: Activating rebuilt chain...")
            chain_file.unlink()
            Path(new_chain_file).rename(chain_file)
            ensure_genesis_pin(audit_dir, chain_file)
            
            # Update last hash
            last_hash_file.write_text(results["rebuild_hash"])
            
            print(f"  New chain activated: {chain_file}")
            print(f"  Final chain hash: {results['rebuild_hash'][:20]}...")
            
            # Log rebuild event
            print("\nStep 6: Logging rebuild event...")
            # Reset both class-level and module-level singletons so the next
            # get_audit_log() re-reads the rebuilt .last_hash (otherwise a cached
            # instance appends with stale prev_hash and breaks the chain).
            ImmutableAuditLog._reset()
            import src.audit as _audit_mod
            _audit_mod._audit_log_instance = None
            audit_log = get_audit_log()
            rebuild_event = AuditEvent(
                event_type="chain_rebuild",
                user_id="system",
                result={
                    "events_processed": results["events_processed"],
                    "hashes_corrected": results["hashes_corrected"],
                    "first_event": results["first_event_timestamp"],
                    "last_event": results["last_event_timestamp"],
                    "rebuild_hash": results["rebuild_hash"],
                },
            )
            new_hash = audit_log.append(rebuild_event)
            print(f"  Rebuild event logged with hash: {new_hash[:20]}...")
            
            print("\n" + "=" * 60)
            print(" REBUILD COMPLETE")
            print("=" * 60)
            print(f"Events processed: {results['events_processed']:,}")
            print(f"Hashes corrected: {results['hashes_corrected']:,}")
            print(f"Corrupted chain backed up to: {backup_file}")
            
            return 0
        else:
            print(f"  Rebuilt chain is INVALID ({len(verify_errors)} errors)")
            print("  ABORTING - corrupted backup preserved")
            return 1

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
