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

INSERT INTO manage_products (
    product_id, name, description, status, roadmap, version, tags, created_by, created_at, updated_at
)
VALUES
    (
        'demo_prod_retail',
        '零售运营中台',
        '面向连锁零售业务的订单、会员、履约与门店协同平台。',
        'active',
        '2026 年 Q3 完成结算与履约一体化上线',
        '2026.4',
        '["零售", "订单", "履约"]'::JSONB,
        'user_lin_pm',
        NOW() - INTERVAL '45 days',
        NOW() - INTERVAL '1 day'
    ),
    (
        'demo_prod_campus',
        '校园服务平台',
        '覆盖选课、排课、教室管理与通知触达的校园数字化平台。',
        'active',
        '2026 年 Q2 完成教务链路稳定性改造',
        '3.2.1',
        '["校园", "教务", "课表"]'::JSONB,
        'user_helen',
        NOW() - INTERVAL '38 days',
        NOW() - INTERVAL '2 days'
    );

INSERT INTO manage_product_members (
    product_id, user_id, role, created_at, updated_at
)
VALUES
    ('demo_prod_retail', 'user_lin_pm', 'owner', NOW() - INTERVAL '45 days', NOW() - INTERVAL '1 day'),
    ('demo_prod_retail', 'user_qiao_arch', 'admin', NOW() - INTERVAL '40 days', NOW() - INTERVAL '3 days'),
    ('demo_prod_retail', 'user_chen_fe', 'member', NOW() - INTERVAL '34 days', NOW() - INTERVAL '5 days'),
    ('demo_prod_retail', 'user_sun_ops', 'viewer', NOW() - INTERVAL '28 days', NOW() - INTERVAL '6 days'),
    ('demo_prod_campus', 'user_helen', 'owner', NOW() - INTERVAL '38 days', NOW() - INTERVAL '2 days'),
    ('demo_prod_campus', 'user_ma_dev', 'admin', NOW() - INTERVAL '36 days', NOW() - INTERVAL '4 days'),
    ('demo_prod_campus', 'user_yu_qa', 'member', NOW() - INTERVAL '30 days', NOW() - INTERVAL '3 days');

INSERT INTO manage_projects (
    project_id, name, description, status, product_id, current_session_id, created_by, created_at, updated_at
)
VALUES
    (
        'demo_proj_checkout',
        '会员结算改造',
        '重构订单确认与支付补偿链路，支撑会员价、优惠券和门店自提预约。',
        'active',
        'demo_prod_retail',
        'checkout-session-2026w15',
        'user_lin_pm',
        NOW() - INTERVAL '32 days',
        NOW() - INTERVAL '6 hours'
    ),
    (
        'demo_proj_fulfillment',
        '仓配履约看板',
        '建立仓内异常预警与出库延迟看板，提升日常履约透明度。',
        'active',
        'demo_prod_retail',
        'fulfillment-session-2026w15',
        'user_qiao_arch',
        NOW() - INTERVAL '27 days',
        NOW() - INTERVAL '12 hours'
    ),
    (
        'demo_proj_course',
        '选课与排课协同',
        '为教务处提供实时冲突校验、教室容量分析和学生端提示能力。',
        'active',
        'demo_prod_campus',
        'course-session-2026w15',
        'user_helen',
        NOW() - INTERVAL '24 days',
        NOW() - INTERVAL '8 hours'
    );

INSERT INTO manage_project_members (
    project_id, user_id, role, created_at, updated_at
)
VALUES
    ('demo_proj_checkout', 'user_lin_pm', 'owner', NOW() - INTERVAL '32 days', NOW() - INTERVAL '6 hours'),
    ('demo_proj_checkout', 'user_qiao_arch', 'admin', NOW() - INTERVAL '31 days', NOW() - INTERVAL '1 day'),
    ('demo_proj_checkout', 'user_chen_fe', 'member', NOW() - INTERVAL '29 days', NOW() - INTERVAL '2 days'),
    ('demo_proj_checkout', 'user_yu_qa', 'member', NOW() - INTERVAL '26 days', NOW() - INTERVAL '2 days'),
    ('demo_proj_fulfillment', 'user_qiao_arch', 'owner', NOW() - INTERVAL '27 days', NOW() - INTERVAL '12 hours'),
    ('demo_proj_fulfillment', 'user_sun_ops', 'member', NOW() - INTERVAL '26 days', NOW() - INTERVAL '1 day'),
    ('demo_proj_fulfillment', 'user_chen_fe', 'member', NOW() - INTERVAL '24 days', NOW() - INTERVAL '3 days'),
    ('demo_proj_course', 'user_helen', 'owner', NOW() - INTERVAL '24 days', NOW() - INTERVAL '8 hours'),
    ('demo_proj_course', 'user_ma_dev', 'admin', NOW() - INTERVAL '23 days', NOW() - INTERVAL '1 day'),
    ('demo_proj_course', 'user_yu_qa', 'member', NOW() - INTERVAL '21 days', NOW() - INTERVAL '2 days');

INSERT INTO manage_requirements (
    req_id, project_id, requirement_type, status, title, description, priority, assignee, tags,
    due_date, parent_id, order_index, custom_fields, is_planned, created_by, created_at, updated_by, updated_at, deleted
)
VALUES
    (
        'demo_req_checkout_001',
        'demo_proj_checkout',
        'top_level',
        'confirmed',
        '会员结算链路升级',
        '打通会员价、优惠券和支付补偿的统一结算链路，降低客服人工补单量。',
        'high',
        'user_lin_pm',
        '["结算", "会员"]'::JSONB,
        '2026-05-20',
        NULL,
        0,
        '{"owner_team":"checkout","goal":"支付成功率提升到 99.5%"}'::JSONB,
        TRUE,
        'user_lin_pm',
        NOW() - INTERVAL '22 days',
        'user_lin_pm',
        NOW() - INTERVAL '3 days',
        FALSE
    ),
    (
        'demo_req_checkout_002',
        'demo_proj_checkout',
        'low_level',
        'in_progress',
        '会员价与优惠券叠加规则引擎',
        '引入可配置的规则引擎，支持按会员等级、活动、券种决定叠加与互斥关系。',
        'high',
        'user_qiao_arch',
        '["规则", "价格"]'::JSONB,
        '2026-05-10',
        'demo_req_checkout_001',
        0,
        '{"rule_sets":12,"rollback_plan":"切回旧规则中心"}'::JSONB,
        TRUE,
        'user_qiao_arch',
        NOW() - INTERVAL '20 days',
        'user_qiao_arch',
        NOW() - INTERVAL '14 hours',
        FALSE
    ),
    (
        'demo_req_checkout_003',
        'demo_proj_checkout',
        'task',
        'completed',
        '结算服务增加价格快照字段',
        '在订单确认阶段固化促销前后金额、券面值和会员折扣明细，便于追溯。',
        'medium',
        'user_chen_fe',
        '["订单", "追踪"]'::JSONB,
        '2026-04-25',
        'demo_req_checkout_002',
        0,
        '{"table":"order_price_snapshot"}'::JSONB,
        TRUE,
        'user_chen_fe',
        NOW() - INTERVAL '18 days',
        'user_chen_fe',
        NOW() - INTERVAL '5 days',
        FALSE
    ),
    (
        'demo_req_checkout_004',
        'demo_proj_checkout',
        'task',
        'in_progress',
        '订单确认页展示优惠拆分明细',
        '前端确认页展示会员折扣、优惠券让利和门店补贴的拆分结果。',
        'medium',
        'user_yu_qa',
        '["前端", "展示"]'::JSONB,
        '2026-05-06',
        'demo_req_checkout_002',
        1,
        '{"owner_team":"web-checkout"}'::JSONB,
        TRUE,
        'user_lin_pm',
        NOW() - INTERVAL '15 days',
        'user_yu_qa',
        NOW() - INTERVAL '9 hours',
        FALSE
    ),
    (
        'demo_req_checkout_005',
        'demo_proj_checkout',
        'low_level',
        'under_review',
        '支付失败自动补偿流程',
        '识别支付成功但订单落库失败的场景，自动重试并生成补偿任务。',
        'high',
        'user_chen_fe',
        '["支付", "补偿"]'::JSONB,
        '2026-05-12',
        'demo_req_checkout_001',
        1,
        '{"retry_limit":3,"alert_channel":"ops-checkout"}'::JSONB,
        TRUE,
        'user_qiao_arch',
        NOW() - INTERVAL '17 days',
        'user_qiao_arch',
        NOW() - INTERVAL '2 days',
        FALSE
    ),
    (
        'demo_req_checkout_006',
        'demo_proj_checkout',
        'top_level',
        'under_review',
        '门店自提预约窗口',
        '允许用户在确认订单时选择门店自提日期和时段，避免高峰拥堵。',
        'medium',
        'user_lin_pm',
        '["门店", "自提"]'::JSONB,
        '2026-05-24',
        NULL,
        1,
        '{"pilot_city":"上海"}'::JSONB,
        TRUE,
        'user_lin_pm',
        NOW() - INTERVAL '16 days',
        'user_lin_pm',
        NOW() - INTERVAL '1 day',
        FALSE
    ),
    (
        'demo_req_checkout_007',
        'demo_proj_checkout',
        'low_level',
        'draft',
        '门店容量与时段配置',
        '支持按门店、按日期维护最大预约单量和可选时间窗口。',
        'medium',
        'user_sun_ops',
        '["容量", "门店配置"]'::JSONB,
        '2026-05-18',
        'demo_req_checkout_006',
        0,
        '{"config_scope":["store","date","timeslot"]}'::JSONB,
        FALSE,
        'user_sun_ops',
        NOW() - INTERVAL '12 days',
        'user_sun_ops',
        NOW() - INTERVAL '12 days',
        FALSE
    ),
    (
        'demo_req_checkout_008',
        'demo_proj_checkout',
        'task',
        'draft',
        '自提码短信模板接入',
        '预约成功后给用户发送自提码与时间窗确认短信。',
        'low',
        'user_yu_qa',
        '["短信", "通知"]'::JSONB,
        '2026-05-21',
        'demo_req_checkout_007',
        0,
        '{"provider":"sms-center"}'::JSONB,
        FALSE,
        'user_yu_qa',
        NOW() - INTERVAL '10 days',
        'user_yu_qa',
        NOW() - INTERVAL '10 days',
        FALSE
    ),
    (
        'demo_req_fulfill_001',
        'demo_proj_fulfillment',
        'top_level',
        'confirmed',
        '仓配异常看板',
        '统一呈现超时拣货、延迟出库和波次积压等关键履约异常。',
        'high',
        'user_qiao_arch',
        '["仓配", "可视化"]'::JSONB,
        '2026-05-16',
        NULL,
        0,
        '{"dashboard_owner":"ops-bi"}'::JSONB,
        TRUE,
        'user_qiao_arch',
        NOW() - INTERVAL '18 days',
        'user_qiao_arch',
        NOW() - INTERVAL '2 days',
        FALSE
    ),
    (
        'demo_req_fulfill_002',
        'demo_proj_fulfillment',
        'low_level',
        'in_progress',
        '延迟出库预警规则',
        '按仓组和波次粒度计算预计出库时间，提前 30 分钟触发预警。',
        'high',
        'user_sun_ops',
        '["预警", "SLA"]'::JSONB,
        '2026-05-08',
        'demo_req_fulfill_001',
        0,
        '{"threshold_minutes":30}'::JSONB,
        TRUE,
        'user_sun_ops',
        NOW() - INTERVAL '14 days',
        'user_sun_ops',
        NOW() - INTERVAL '6 hours',
        FALSE
    ),
    (
        'demo_req_fulfill_003',
        'demo_proj_fulfillment',
        'task',
        'draft',
        '看板支持按仓组筛选',
        '增加华东、华南和华北仓组三档筛选，便于区域运营值班。',
        'medium',
        'user_chen_fe',
        '["筛选", "仓组"]'::JSONB,
        '2026-05-14',
        'demo_req_fulfill_002',
        0,
        '{"ui_filter":"warehouse_group"}'::JSONB,
        FALSE,
        'user_chen_fe',
        NOW() - INTERVAL '9 days',
        'user_chen_fe',
        NOW() - INTERVAL '9 days',
        FALSE
    ),
    (
        'demo_req_course_001',
        'demo_proj_course',
        'top_level',
        'confirmed',
        '选课冲突实时校验',
        '学生提交选课请求前即时校验时间冲突、先修条件和人数上限。',
        'high',
        'user_helen',
        '["选课", "实时校验"]'::JSONB,
        '2026-05-15',
        NULL,
        0,
        '{"semester":"2026-Spring"}'::JSONB,
        TRUE,
        'user_helen',
        NOW() - INTERVAL '19 days',
        'user_helen',
        NOW() - INTERVAL '3 days',
        FALSE
    ),
    (
        'demo_req_course_002',
        'demo_proj_course',
        'low_level',
        'in_progress',
        '课表冲突矩阵服务',
        '将课程节次、实验课和跨校区通勤时间统一纳入冲突矩阵计算。',
        'high',
        'user_ma_dev',
        '["课表", "服务"]'::JSONB,
        '2026-05-07',
        'demo_req_course_001',
        0,
        '{"matrix_version":"v2"}'::JSONB,
        TRUE,
        'user_ma_dev',
        NOW() - INTERVAL '16 days',
        'user_ma_dev',
        NOW() - INTERVAL '8 hours',
        FALSE
    ),
    (
        'demo_req_course_003',
        'demo_proj_course',
        'task',
        'draft',
        '前端冲突提示文案',
        '针对时间冲突、容量已满和先修条件未满足给出不同文案与引导。',
        'medium',
        'user_yu_qa',
        '["前端", "文案"]'::JSONB,
        '2026-05-11',
        'demo_req_course_002',
        0,
        '{"channel":"student-h5"}'::JSONB,
        FALSE,
        'user_yu_qa',
        NOW() - INTERVAL '8 days',
        'user_yu_qa',
        NOW() - INTERVAL '8 days',
        FALSE
    ),
    (
        'demo_req_course_004',
        'demo_proj_course',
        'top_level',
        'draft',
        '教室容量预测',
        '基于历史选课峰值和补退选行为，预测热门课程的教室容量压力。',
        'medium',
        'user_helen',
        '["容量", "预测"]'::JSONB,
        '2026-05-28',
        NULL,
        1,
        '{"source":"registration_history"}'::JSONB,
        FALSE,
        'user_helen',
        NOW() - INTERVAL '11 days',
        'user_helen',
        NOW() - INTERVAL '11 days',
        FALSE
    ),
    (
        'demo_req_course_005',
        'demo_proj_course',
        'low_level',
        'draft',
        '历史选课数据回灌',
        '补齐近四个学期的选课快照，为容量预测提供稳定训练样本。',
        'medium',
        'user_ma_dev',
        '["数据", "训练样本"]'::JSONB,
        '2026-05-19',
        'demo_req_course_004',
        0,
        '{"semesters":4}'::JSONB,
        FALSE,
        'user_ma_dev',
        NOW() - INTERVAL '7 days',
        'user_ma_dev',
        NOW() - INTERVAL '7 days',
        FALSE
    );

INSERT INTO manage_requirement_links (
    source_req_id, target_req_id, link_type, created_by, created_at
)
VALUES
    ('demo_req_checkout_002', 'demo_req_checkout_005', 'blocks', 'user_qiao_arch', NOW() - INTERVAL '13 days'),
    ('demo_req_checkout_007', 'demo_req_checkout_005', 'depends_on', 'user_sun_ops', NOW() - INTERVAL '10 days'),
    ('demo_req_fulfill_002', 'demo_req_fulfill_003', 'relates_to', 'user_qiao_arch', NOW() - INTERVAL '7 days'),
    ('demo_req_course_002', 'demo_req_course_003', 'blocks', 'user_ma_dev', NOW() - INTERVAL '6 days');

INSERT INTO manage_test_cases (
    test_case_id, project_id, title, description, status, source, created_by, created_at
)
VALUES
    (
        'demo_tc_checkout_001',
        'demo_proj_checkout',
        '会员价与满减券叠加回归',
        '验证黑金会员叠加店铺券与平台券后的金额拆分是否符合新规则。',
        'active',
        'demo_req_checkout_002',
        'user_yu_qa',
        NOW() - INTERVAL '13 days'
    ),
    (
        'demo_tc_checkout_002',
        'demo_proj_checkout',
        '确认页优惠拆分展示校验',
        '验证订单确认页展示会员折扣、优惠券和运费减免三类明细。',
        'active',
        'demo_req_checkout_004',
        'user_yu_qa',
        NOW() - INTERVAL '9 days'
    ),
    (
        'demo_tc_checkout_003',
        'demo_proj_checkout',
        '支付回调补偿重试',
        '模拟支付成功但订单落库超时，确认补偿任务自动创建并重试。',
        'active',
        'demo_req_checkout_005',
        'user_yu_qa',
        NOW() - INTERVAL '8 days'
    ),
    (
        'demo_tc_checkout_004',
        'demo_proj_checkout',
        '门店预约时段冲突校验',
        '同一时间窗达到上限后，前端不再展示该时段。',
        'draft',
        'demo_req_checkout_007',
        'user_sun_ops',
        NOW() - INTERVAL '6 days'
    ),
    (
        'demo_tc_fulfill_001',
        'demo_proj_fulfillment',
        '延迟出库预警阈值测试',
        '验证距离预计出库 30 分钟时生成黄色预警，超时后升级红色预警。',
        'active',
        'demo_req_fulfill_002',
        'user_sun_ops',
        NOW() - INTERVAL '7 days'
    ),
    (
        'demo_tc_fulfill_002',
        'demo_proj_fulfillment',
        '仓组筛选联动测试',
        '切换华东仓组后，只展示对应仓与波次的异常数据。',
        'draft',
        'demo_req_fulfill_003',
        'user_chen_fe',
        NOW() - INTERVAL '5 days'
    ),
    (
        'demo_tc_course_001',
        'demo_proj_course',
        '课程时间冲突即时拦截',
        '学生选择两门时间重叠的课程时，应在提交前收到冲突提示。',
        'active',
        'demo_req_course_002',
        'user_yu_qa',
        NOW() - INTERVAL '9 days'
    ),
    (
        'demo_tc_course_002',
        'demo_proj_course',
        '跨校区通勤时间校验',
        '上一节课在新校区、下一节课在老校区且间隔不足 20 分钟时，应提示不可选。',
        'active',
        'demo_req_course_002',
        'user_yu_qa',
        NOW() - INTERVAL '8 days'
    ),
    (
        'demo_tc_course_003',
        'demo_proj_course',
        '容量预测样本完整性检查',
        '检查导入的历史选课快照是否覆盖近四个学期且课程编码不缺失。',
        'draft',
        'demo_req_course_005',
        'user_ma_dev',
        NOW() - INTERVAL '4 days'
    );

INSERT INTO manage_requirement_test_links (
    requirement_id, test_case_id, link_type, created_at
)
VALUES
    ('demo_req_checkout_002', 'demo_tc_checkout_001', 'verification', NOW() - INTERVAL '13 days'),
    ('demo_req_checkout_004', 'demo_tc_checkout_002', 'verification', NOW() - INTERVAL '9 days'),
    ('demo_req_checkout_005', 'demo_tc_checkout_003', 'verification', NOW() - INTERVAL '8 days'),
    ('demo_req_checkout_007', 'demo_tc_checkout_004', 'verification', NOW() - INTERVAL '6 days'),
    ('demo_req_fulfill_002', 'demo_tc_fulfill_001', 'verification', NOW() - INTERVAL '7 days'),
    ('demo_req_fulfill_003', 'demo_tc_fulfill_002', 'verification', NOW() - INTERVAL '5 days'),
    ('demo_req_course_002', 'demo_tc_course_001', 'verification', NOW() - INTERVAL '9 days'),
    ('demo_req_course_002', 'demo_tc_course_002', 'verification', NOW() - INTERVAL '8 days'),
    ('demo_req_course_005', 'demo_tc_course_003', 'verification', NOW() - INTERVAL '4 days');

INSERT INTO manage_defects (
    defect_id, project_id, requirement_id, title, reproduce_steps, severity, priority, status,
    reporter, dev_assignee, tester_assignee, current_assignee, created_by, created_at, updated_by, updated_at
)
VALUES
    (
        'demo_def_checkout_001',
        'demo_proj_checkout',
        'demo_req_checkout_002',
        '大促订单叠加两张券时金额被多减一分钱',
        '1. 使用黑金会员账号加入大促商品。 2. 同时选择店铺券与平台满减券。 3. 在订单确认页提交。 4. 订单金额与规则中心结果不一致。',
        'high',
        'P1',
        'in_progress',
        'user_yu_qa',
        'user_chen_fe',
        'user_yu_qa',
        'user_chen_fe',
        'user_yu_qa',
        NOW() - INTERVAL '6 days',
        'user_chen_fe',
        NOW() - INTERVAL '10 hours'
    ),
    (
        'demo_def_checkout_002',
        'demo_proj_checkout',
        'demo_req_checkout_004',
        '优惠拆分明细在 Safari 上被截断',
        'iPhone Safari 打开订单确认页，优惠明细超过两行时尾部内容不可见。',
        'medium',
        'P2',
        'open',
        'user_yu_qa',
        'user_chen_fe',
        'user_yu_qa',
        'user_chen_fe',
        'user_yu_qa',
        NOW() - INTERVAL '4 days',
        'user_yu_qa',
        NOW() - INTERVAL '4 days'
    ),
    (
        'demo_def_checkout_003',
        'demo_proj_checkout',
        'demo_req_checkout_005',
        '补偿任务重试后偶发重复推送短信',
        '支付补偿第二次重试成功后，短信通知被发送两次。',
        'medium',
        'P2',
        'resolved',
        'user_sun_ops',
        'user_chen_fe',
        'user_yu_qa',
        'user_yu_qa',
        'user_sun_ops',
        NOW() - INTERVAL '3 days',
        'user_chen_fe',
        NOW() - INTERVAL '1 day'
    ),
    (
        'demo_def_fulfill_001',
        'demo_proj_fulfillment',
        'demo_req_fulfill_002',
        '夜间波次未触发延迟出库预警',
        '凌晨 1 点后的波次达到阈值后看板无任何预警提示。',
        'critical',
        'P0',
        'open',
        'user_sun_ops',
        'user_qiao_arch',
        'user_sun_ops',
        'user_qiao_arch',
        'user_sun_ops',
        NOW() - INTERVAL '2 days',
        'user_sun_ops',
        NOW() - INTERVAL '2 days'
    ),
    (
        'demo_def_course_001',
        'demo_proj_course',
        'demo_req_course_002',
        '跨校区通勤时间未计入冲突矩阵',
        '学生在新老校区之间切换课程时，系统只按课表时间判断，未扣减通勤时间。',
        'high',
        'P1',
        'in_progress',
        'user_yu_qa',
        'user_ma_dev',
        'user_yu_qa',
        'user_ma_dev',
        'user_yu_qa',
        NOW() - INTERVAL '5 days',
        'user_ma_dev',
        NOW() - INTERVAL '11 hours'
    ),
    (
        'demo_def_course_002',
        'demo_proj_course',
        'demo_req_course_005',
        '历史快照中部分课程编码为空',
        '2024 秋季的回灌数据中存在 27 条课程编码为空，导致预测样本被丢弃。',
        'medium',
        'P2',
        'open',
        'user_ma_dev',
        'user_ma_dev',
        'user_yu_qa',
        'user_ma_dev',
        'user_ma_dev',
        NOW() - INTERVAL '3 days',
        'user_ma_dev',
        NOW() - INTERVAL '3 days'
    );

INSERT INTO manage_milestones (
    milestone_id, project_id, name, description, message, milestone_type, is_baseline,
    sprint, version, tags, metadata, created_by, created_at
)
VALUES
    (
        'demo_ms_checkout_001',
        'demo_proj_checkout',
        '结算链路基线 M1',
        '冻结会员价与优惠券叠加规则的第一版实现范围。',
        '规则引擎进入联调，自提预约需求仍在评审。',
        'baseline',
        TRUE,
        'Sprint-2026-W14',
        'checkout-1.4.0-m1',
        '["基线", "结算"]'::JSONB,
        '{"freeze_scope":["demo_req_checkout_001","demo_req_checkout_002","demo_req_checkout_003"]}'::JSONB,
        'user_lin_pm',
        NOW() - INTERVAL '11 days'
    ),
    (
        'demo_ms_checkout_002',
        'demo_proj_checkout',
        '门店自提评审版',
        '门店预约时段与短信通知方案的评审版本。',
        '待确认门店容量模型后进入开发。',
        'regular',
        FALSE,
        'Sprint-2026-W16',
        'checkout-1.5.0-review',
        '["评审", "门店"]'::JSONB,
        '{"reviewers":["store-ops","crm"]}'::JSONB,
        'user_lin_pm',
        NOW() - INTERVAL '4 days'
    ),
    (
        'demo_ms_fulfill_001',
        'demo_proj_fulfillment',
        '仓配看板基线 M1',
        '冻结看板首页、异常规则和仓组筛选能力的初始范围。',
        '夜间波次预警修复后可对外演示。',
        'baseline',
        TRUE,
        'Sprint-2026-W15',
        'fulfillment-0.9.0',
        '["看板", "预警"]'::JSONB,
        '{"warehouse_groups":3}'::JSONB,
        'user_qiao_arch',
        NOW() - INTERVAL '7 days'
    ),
    (
        'demo_ms_course_001',
        'demo_proj_course',
        '选课冲突服务基线 M1',
        '冻结冲突矩阵服务、前端提示和历史样本回灌的首轮交付范围。',
        '跨校区通勤时间算法需要在第二周补齐。',
        'baseline',
        TRUE,
        'Sprint-2026-W15',
        'course-2.3.0-m1',
        '["选课", "冲突校验"]'::JSONB,
        '{"semester":"2026-Spring"}'::JSONB,
        'user_helen',
        NOW() - INTERVAL '6 days'
    );

INSERT INTO manage_milestone_nodes (
    snapshot_id, milestone_id, requirement_id, requirement_type, status, title, description,
    parent_id, order_index, snapshot_data, created_at
)
VALUES
    (
        'demo_snap_checkout_001',
        'demo_ms_checkout_001',
        'demo_req_checkout_001',
        'top_level',
        'confirmed',
        '会员结算链路升级',
        '打通会员价、优惠券和支付补偿的统一结算链路。',
        NULL,
        0,
        '{"priority":"high","assignee":"user_lin_pm","status":"confirmed"}'::JSONB,
        NOW() - INTERVAL '11 days'
    ),
    (
        'demo_snap_checkout_002',
        'demo_ms_checkout_001',
        'demo_req_checkout_002',
        'low_level',
        'in_progress',
        '会员价与优惠券叠加规则引擎',
        '支持会员等级、活动、券种的叠加和互斥。',
        'demo_req_checkout_001',
        0,
        '{"priority":"high","assignee":"user_qiao_arch","rule_sets":12}'::JSONB,
        NOW() - INTERVAL '11 days'
    ),
    (
        'demo_snap_checkout_003',
        'demo_ms_checkout_001',
        'demo_req_checkout_003',
        'task',
        'completed',
        '结算服务增加价格快照字段',
        '固化促销前后金额与券明细。',
        'demo_req_checkout_002',
        0,
        '{"priority":"medium","assignee":"user_chen_fe","table":"order_price_snapshot"}'::JSONB,
        NOW() - INTERVAL '11 days'
    ),
    (
        'demo_snap_checkout_004',
        'demo_ms_checkout_002',
        'demo_req_checkout_006',
        'top_level',
        'under_review',
        '门店自提预约窗口',
        '允许用户选择自提日期和时段。',
        NULL,
        0,
        '{"priority":"medium","assignee":"user_lin_pm","pilot_city":"上海"}'::JSONB,
        NOW() - INTERVAL '4 days'
    ),
    (
        'demo_snap_checkout_005',
        'demo_ms_checkout_002',
        'demo_req_checkout_007',
        'low_level',
        'draft',
        '门店容量与时段配置',
        '支持按门店和日期维护容量。',
        'demo_req_checkout_006',
        0,
        '{"priority":"medium","assignee":"user_sun_ops"}'::JSONB,
        NOW() - INTERVAL '4 days'
    ),
    (
        'demo_snap_fulfill_001',
        'demo_ms_fulfill_001',
        'demo_req_fulfill_001',
        'top_level',
        'confirmed',
        '仓配异常看板',
        '统一呈现超时拣货、延迟出库和波次积压。',
        NULL,
        0,
        '{"priority":"high","assignee":"user_qiao_arch"}'::JSONB,
        NOW() - INTERVAL '7 days'
    ),
    (
        'demo_snap_fulfill_002',
        'demo_ms_fulfill_001',
        'demo_req_fulfill_002',
        'low_level',
        'in_progress',
        '延迟出库预警规则',
        '提前 30 分钟触发预警。',
        'demo_req_fulfill_001',
        0,
        '{"priority":"high","assignee":"user_sun_ops","threshold_minutes":30}'::JSONB,
        NOW() - INTERVAL '7 days'
    ),
    (
        'demo_snap_course_001',
        'demo_ms_course_001',
        'demo_req_course_001',
        'top_level',
        'confirmed',
        '选课冲突实时校验',
        '即时校验时间冲突、先修条件和人数上限。',
        NULL,
        0,
        '{"priority":"high","assignee":"user_helen"}'::JSONB,
        NOW() - INTERVAL '6 days'
    ),
    (
        'demo_snap_course_002',
        'demo_ms_course_001',
        'demo_req_course_002',
        'low_level',
        'in_progress',
        '课表冲突矩阵服务',
        '纳入实验课和跨校区通勤时间。',
        'demo_req_course_001',
        0,
        '{"priority":"high","assignee":"user_ma_dev","matrix_version":"v2"}'::JSONB,
        NOW() - INTERVAL '6 days'
    ),
    (
        'demo_snap_course_003',
        'demo_ms_course_001',
        'demo_req_course_005',
        'low_level',
        'draft',
        '历史选课数据回灌',
        '补齐近四个学期的选课快照。',
        'demo_req_course_004',
        1,
        '{"priority":"medium","assignee":"user_ma_dev","semesters":4}'::JSONB,
        NOW() - INTERVAL '6 days'
    );

INSERT INTO manage_branches (
    branch_id, project_id, base_milestone_id, name, status, metadata, created_by, created_at, updated_at
)
VALUES
    (
        'demo_branch_checkout_coupon',
        'demo_proj_checkout',
        'demo_ms_checkout_001',
        'feature/coupon-rule-engine',
        'active',
        '{"goal":"完成叠加规则与拆分展示联调"}'::JSONB,
        'user_qiao_arch',
        NOW() - INTERVAL '5 days',
        NOW() - INTERVAL '8 hours'
    ),
    (
        'demo_branch_fulfill_alert',
        'demo_proj_fulfillment',
        'demo_ms_fulfill_001',
        'fix/night-shift-alert',
        'under_review',
        '{"goal":"修复夜间波次不预警问题"}'::JSONB,
        'user_sun_ops',
        NOW() - INTERVAL '3 days',
        NOW() - INTERVAL '10 hours'
    ),
    (
        'demo_branch_course_matrix',
        'demo_proj_course',
        'demo_ms_course_001',
        'feature/commute-conflict-matrix',
        'active',
        '{"goal":"引入跨校区通勤时间冲突算法"}'::JSONB,
        'user_ma_dev',
        NOW() - INTERVAL '4 days',
        NOW() - INTERVAL '7 hours'
    );

INSERT INTO manage_change_sets (
    change_id, branch_id, change_type, requirement_id, before_data, after_data, created_by, created_at
)
VALUES
    (
        'demo_cs_checkout_001',
        'demo_branch_checkout_coupon',
        'modified',
        'demo_req_checkout_002',
        '{"stack_mode":"legacy","rule_source":"promo-center"}'::JSONB,
        '{"stack_mode":"rule_engine","rule_source":"checkout-engine","supports_vip_coupon":"true"}'::JSONB,
        'user_qiao_arch',
        NOW() - INTERVAL '4 days'
    ),
    (
        'demo_cs_checkout_002',
        'demo_branch_checkout_coupon',
        'modified',
        'demo_req_checkout_004',
        '{"show_discount_breakdown":false}'::JSONB,
        '{"show_discount_breakdown":true,"show_subsidy_tag":true}'::JSONB,
        'user_yu_qa',
        NOW() - INTERVAL '2 days'
    ),
    (
        'demo_cs_fulfill_001',
        'demo_branch_fulfill_alert',
        'modified',
        'demo_req_fulfill_002',
        '{"night_shift_enabled":false}'::JSONB,
        '{"night_shift_enabled":true,"escalation_level":"red"}'::JSONB,
        'user_sun_ops',
        NOW() - INTERVAL '2 days'
    ),
    (
        'demo_cs_fulfill_002',
        'demo_branch_fulfill_alert',
        'modified',
        'demo_req_fulfill_003',
        '{"warehouse_group_filter":["华东"]}'::JSONB,
        '{"warehouse_group_filter":["华东","华南","华北"]}'::JSONB,
        'user_chen_fe',
        NOW() - INTERVAL '1 day'
    ),
    (
        'demo_cs_course_001',
        'demo_branch_course_matrix',
        'modified',
        'demo_req_course_002',
        '{"commute_minutes_included":false}'::JSONB,
        '{"commute_minutes_included":true,"matrix_version":"v2.1"}'::JSONB,
        'user_ma_dev',
        NOW() - INTERVAL '3 days'
    ),
    (
        'demo_cs_course_002',
        'demo_branch_course_matrix',
        'modified',
        'demo_req_course_003',
        '{"copy_version":"v1"}'::JSONB,
        '{"copy_version":"v2","supports_capacity_hint":true}'::JSONB,
        'user_yu_qa',
        NOW() - INTERVAL '1 day'
    );

INSERT INTO manage_comments (
    comment_id, project_id, target_type, target_id, content, reply_to_id, created_by, created_at, updated_at, deleted
)
VALUES
    (
        'demo_comment_001',
        'demo_proj_checkout',
        'requirement',
        'demo_req_checkout_002',
        '叠加规则建议把会员等级和券种拆成两个维度，便于后续门店活动复用。',
        NULL,
        'user_lin_pm',
        NOW() - INTERVAL '5 days',
        NOW() - INTERVAL '5 days',
        FALSE
    ),
    (
        'demo_comment_002',
        'demo_proj_checkout',
        'requirement',
        'demo_req_checkout_002',
        '已按这个思路调整配置结构，今晚会补一版联调文档。',
        'demo_comment_001',
        'user_qiao_arch',
        NOW() - INTERVAL '4 days',
        NOW() - INTERVAL '4 days',
        FALSE
    ),
    (
        'demo_comment_003',
        'demo_proj_checkout',
        'defect',
        'demo_def_checkout_001',
        '一分钱误差已定位到四舍五入顺序，修复后需要再跑大促回归。',
        NULL,
        'user_chen_fe',
        NOW() - INTERVAL '2 days',
        NOW() - INTERVAL '2 days',
        FALSE
    ),
    (
        'demo_comment_004',
        'demo_proj_course',
        'test_case',
        'demo_tc_course_001',
        '测试数据里需要补一组跨校区连续两节课的样例，当前覆盖还不够。',
        NULL,
        'user_yu_qa',
        NOW() - INTERVAL '3 days',
        NOW() - INTERVAL '3 days',
        FALSE
    ),
    (
        'demo_comment_005',
        'demo_proj_fulfillment',
        'milestone',
        'demo_ms_fulfill_001',
        '夜间波次预警修好后，这个里程碑就可以作为一线值班演示版本。',
        NULL,
        'user_sun_ops',
        NOW() - INTERVAL '1 day',
        NOW() - INTERVAL '1 day',
        FALSE
    );

INSERT INTO manage_audit_logs (
    log_id, project_id, product_id, actor, action, target_type, target_id, detail, created_at
)
VALUES
    (
        'demo_log_001',
        NULL,
        'demo_prod_retail',
        'user_lin_pm',
        'create_product',
        'product',
        'demo_prod_retail',
        '{"name":"零售运营中台","owner":"user_lin_pm"}'::JSONB,
        NOW() - INTERVAL '45 days'
    ),
    (
        'demo_log_002',
        NULL,
        'demo_prod_campus',
        'user_helen',
        'create_product',
        'product',
        'demo_prod_campus',
        '{"name":"校园服务平台","owner":"user_helen"}'::JSONB,
        NOW() - INTERVAL '38 days'
    ),
    (
        'demo_log_003',
        'demo_proj_checkout',
        'demo_prod_retail',
        'user_lin_pm',
        'create_project',
        'project',
        'demo_proj_checkout',
        '{"name":"会员结算改造","session":"checkout-session-2026w15"}'::JSONB,
        NOW() - INTERVAL '32 days'
    ),
    (
        'demo_log_004',
        'demo_proj_fulfillment',
        'demo_prod_retail',
        'user_qiao_arch',
        'create_project',
        'project',
        'demo_proj_fulfillment',
        '{"name":"仓配履约看板","warehouse_groups":3}'::JSONB,
        NOW() - INTERVAL '27 days'
    ),
    (
        'demo_log_005',
        'demo_proj_course',
        'demo_prod_campus',
        'user_helen',
        'create_project',
        'project',
        'demo_proj_course',
        '{"name":"选课与排课协同","semester":"2026-Spring"}'::JSONB,
        NOW() - INTERVAL '24 days'
    ),
    (
        'demo_log_006',
        'demo_proj_checkout',
        'demo_prod_retail',
        'user_qiao_arch',
        'update_requirement_status',
        'requirement',
        'demo_req_checkout_005',
        '{"from":"draft","to":"under_review"}'::JSONB,
        NOW() - INTERVAL '2 days'
    ),
    (
        'demo_log_007',
        'demo_proj_checkout',
        'demo_prod_retail',
        'user_yu_qa',
        'create_test_case',
        'test_case',
        'demo_tc_checkout_001',
        '{"title":"会员价与满减券叠加回归"}'::JSONB,
        NOW() - INTERVAL '13 days'
    ),
    (
        'demo_log_008',
        'demo_proj_checkout',
        'demo_prod_retail',
        'user_yu_qa',
        'create_defect',
        'defect',
        'demo_def_checkout_001',
        '{"severity":"high","priority":"P1"}'::JSONB,
        NOW() - INTERVAL '6 days'
    ),
    (
        'demo_log_009',
        'demo_proj_fulfillment',
        'demo_prod_retail',
        'user_qiao_arch',
        'create_milestone',
        'milestone',
        'demo_ms_fulfill_001',
        '{"name":"仓配看板基线 M1","is_baseline":true}'::JSONB,
        NOW() - INTERVAL '7 days'
    ),
    (
        'demo_log_010',
        'demo_proj_fulfillment',
        'demo_prod_retail',
        'user_sun_ops',
        'create_branch',
        'branch',
        'demo_branch_fulfill_alert',
        '{"name":"fix/night-shift-alert"}'::JSONB,
        NOW() - INTERVAL '3 days'
    ),
    (
        'demo_log_011',
        'demo_proj_course',
        'demo_prod_campus',
        'user_ma_dev',
        'update_requirement_status',
        'requirement',
        'demo_req_course_002',
        '{"from":"draft","to":"in_progress","matrix_version":"v2"}'::JSONB,
        NOW() - INTERVAL '16 days'
    ),
    (
        'demo_log_012',
        'demo_proj_course',
        'demo_prod_campus',
        'user_yu_qa',
        'create_defect',
        'defect',
        'demo_def_course_001',
        '{"severity":"high","priority":"P1"}'::JSONB,
        NOW() - INTERVAL '5 days'
    );

COMMIT;
