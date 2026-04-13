import psycopg2
from config import get_default_connection

conn_kwargs = get_default_connection()
print("Connecting to DB to cleanup...")
conn = psycopg2.connect(**conn_kwargs)
conn.autocommit = True

with conn.cursor() as cur:
    print("Deleting benchmark data (log_id LIKE 'blog_%', etc)...")
    cur.execute("""
        DELETE FROM manage_audit_logs WHERE log_id LIKE 'blog_%';
        DELETE FROM manage_change_sets WHERE change_id LIKE 'bcs_%';
        DELETE FROM manage_branches WHERE branch_id LIKE 'bbranch_%';
        DELETE FROM manage_milestone_nodes WHERE snapshot_id LIKE 'bsnap_%';
        DELETE FROM manage_milestones WHERE milestone_id LIKE 'bms_%';
        DELETE FROM manage_defects WHERE defect_id LIKE 'bdef_%';
        DELETE FROM manage_requirement_test_links WHERE requirement_id LIKE 'breq_%' OR test_case_id LIKE 'btc_%';
        DELETE FROM manage_test_cases WHERE test_case_id LIKE 'btc_%';
        DELETE FROM manage_requirements WHERE req_id LIKE 'breq_%';
        DELETE FROM manage_projects WHERE project_id LIKE 'bproj_%';
        DELETE FROM manage_product_members WHERE product_id LIKE 'bprod_%' OR user_id LIKE 'bench_user_%';
        DELETE FROM manage_products WHERE product_id LIKE 'bprod_%';
    """)
    
    print("Executing VACUUM FULL to reclaim disk space...")
    cur.execute("VACUUM FULL")
    
    print("Executing ANALYZE to refresh statistics and query optimizer...")
    cur.execute("ANALYZE")

print("Cleanup completed successfully.")
