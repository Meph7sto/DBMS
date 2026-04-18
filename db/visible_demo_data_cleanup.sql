BEGIN;

DELETE FROM manage_audit_logs
WHERE log_id LIKE 'demo_log_%';

DELETE FROM manage_comments
WHERE comment_id LIKE 'demo_comment_%';

DELETE FROM manage_change_sets
WHERE change_id LIKE 'demo_cs_%';

DELETE FROM manage_branches
WHERE branch_id LIKE 'demo_branch_%';

DELETE FROM manage_milestone_nodes
WHERE snapshot_id LIKE 'demo_snap_%';

DELETE FROM manage_milestones
WHERE milestone_id LIKE 'demo_ms_%';

DELETE FROM manage_defects
WHERE defect_id LIKE 'demo_def_%';

DELETE FROM manage_requirement_test_links
WHERE requirement_id LIKE 'demo_req_%'
   OR test_case_id LIKE 'demo_tc_%';

DELETE FROM manage_test_cases
WHERE test_case_id LIKE 'demo_tc_%';

DELETE FROM manage_requirement_links
WHERE source_req_id LIKE 'demo_req_%'
   OR target_req_id LIKE 'demo_req_%';

DELETE FROM manage_requirements
WHERE req_id LIKE 'demo_req_%';

DELETE FROM manage_project_members
WHERE project_id LIKE 'demo_proj_%';

DELETE FROM manage_projects
WHERE project_id LIKE 'demo_proj_%';

DELETE FROM manage_product_members
WHERE product_id LIKE 'demo_prod_%';

DELETE FROM manage_products
WHERE product_id LIKE 'demo_prod_%';

COMMIT;
