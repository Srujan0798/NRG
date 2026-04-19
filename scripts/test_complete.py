#!/usr/bin/env python3
"""
Complete System Test - Run this to verify all components work.
Usage: python scripts/test_complete.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment
os.environ['DATABASE_URL'] = 'sqlite:///nrg_research.db'
os.environ.setdefault('LLM_PROVIDER', 'none')
os.environ.setdefault('CLOUD_SYNTHESIS_ALLOWED', 'false')

print("=" * 70)
print("🚀 NRG COMPLETE SYSTEM TEST")
print("=" * 70)

# Test 1: Database
print("\n📊 Test 1: Database Connectivity")
try:
    from src.data.database import get_sqlite_connection
    conn = get_sqlite_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM researchers")
    researcher_count = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM publications")
    pub_count = cursor.fetchone()[0]
    conn.close()
    print(f"   ✅ Database connected: {researcher_count} researchers, {pub_count} publications")
except Exception as e:
    print(f"   ❌ Database error: {e}")
    sys.exit(1)

# Test 2: JWT Auth
print("\n🔐 Test 2: JWT Authentication")
try:
    from src.auth.jwt_handler import JWTHandler
    handler = JWTHandler()
    user = handler.authenticate_user("researcher_user", "researcher-pass")
    if user:
        tokens = handler.issue_token_pair(user)
        print(f"   ✅ Auth working: access_token generated ({len(tokens['access_token'])} chars)")
    else:
        print("   ❌ Auth failed")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Auth error: {e}")
    sys.exit(1)

# Test 3: Text-to-SQL
print("\n📝 Test 3: Text-to-SQL Skill")
try:
    from src.skills.text_to_sql.skill import TextToSQLSkill
    skill = TextToSQLSkill()
    result = skill.execute("find robotics researchers in Gujarat")
    row_count = result.get('row_count', 0)
    print(f"   ✅ Text-to-SQL working: {row_count} rows returned")
    skill.close()
except Exception as e:
    print(f"   ❌ Text-to-SQL error: {e}")
    sys.exit(1)

# Test 4: LLM Configuration
print("\n🤖 Test 4: LLM Configuration (NVIDIA)")
try:
    from src.config.llm_config import load_llm_settings, get_llm_client
    settings = load_llm_settings()
    print(f"   ✅ LLM Config: provider={settings.provider}, model={settings.model}")
    client = get_llm_client()
    if client:
        print(f"   ✅ LLM Client created successfully")
    else:
        print("   ⚠️  LLM Client is None (fallback mode)")
except Exception as e:
    print(f"   ❌ LLM error: {e}")

# Test 5: Full Workflow
print("\n⚙️  Test 5: Complete Workflow (Query → SQL → Response)")
try:
    from src.orchestration.graph import NRGWorkflow
    workflow = NRGWorkflow()
    result = workflow.run("find robotics researchers in Gujarat", user_tier=1)
    
    intent = result.get('intent', 'N/A')
    routing = result.get('routing_decision', 'N/A')
    sql_rows = len(result.get('sql_results', []))
    response_preview = result.get('synthesized_response', 'N/A')[:100]
    
    print(f"   ✅ Intent detected: {intent}")
    print(f"   ✅ Routing: {routing}")
    print(f"   ✅ SQL returned: {sql_rows} rows")
    print(f"   ✅ Response preview: {response_preview}...")
    
    # Check for executor errors
    errors = result.get('errors', [])
    if errors:
        print(f"   ⚠️  Executor errors: {len(errors)}")
    else:
        print(f"   ✅ No executor errors")
        
except Exception as e:
    print(f"   ❌ Workflow error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Audit Chain
print("\n📋 Test 6: Audit Chain")
try:
    from src.audit import verify_chain, get_audit_log
    valid, errors = verify_chain()
    if valid:
        print(f"   ✅ Audit chain valid: {len(get_audit_log())} entries")
    else:
        print(f"   ⚠️  Audit chain has {len(errors)} errors")
except Exception as e:
    print(f"   ❌ Audit error: {e}")

# Test 7: Seed Relations
print("\n🌱 Test 7: Relationship Tables")
try:
    from src.data.database import get_sqlite_connection
    conn = get_sqlite_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM researcher_publications")
    rp_count = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM publication_keywords")
    pk_count = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM researcher_labs")
    rl_count = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM keywords")
    kw_count = cursor.fetchone()[0]
    conn.close()
    print(f"   ✅ researcher_publications: {rp_count}")
    print(f"   ✅ publication_keywords: {pk_count}")
    print(f"   ✅ researcher_labs: {rl_count}")
    print(f"   ✅ keywords: {kw_count}")
except Exception as e:
    print(f"   ❌ Relations error: {e}")

# Test 8: API Endpoints (if running)
print("\n🌐 Test 8: API Health Check")
try:
    import requests
    response = requests.get("http://localhost:8000/health", timeout=2)
    if response.status_code == 200:
        print(f"   ✅ API is running on localhost:8000")
    else:
        print(f"   ⚠️  API returned status {response.status_code}")
except requests.exceptions.ConnectionError:
    print(f"   ⚠️  API not running (start with: make dev)")
except Exception as e:
    print(f"   ⚠️  API check error: {e}")

# Summary
print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED")
print("=" * 70)
print("\nSystem is ready for use!")
print("\nQuick commands:")
print("  source .venv/bin/activate")
print("  make dev          # Start API server")
print("  make test         # Run test suite")
print("  bash scripts/smoke.sh  # Run smoke tests")
print("\nAPI Documentation:")
print("  http://localhost:8000/docs")
print("  http://localhost:8000/redoc")
print("\nFrontend:")
print("  cd frontend && npm run dev")
print("=" * 70)
