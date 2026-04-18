-- ============================================================
-- 测试数据 (Test Data)
-- 需求管理数据库 - 管理模块
-- ============================================================

-- ============================================================
-- 一、产品层测试数据
-- ============================================================

INSERT INTO manage_products (product_id, name, description, status, roadmap, version, tags, created_by, created_at)
VALUES
    ('prod_001', '智能车载系统 V3.0', '新一代智能车载信息娱乐系统，支持语音交互、OTA升级、生态融合', 'active', '2026年Q2发布', '3.0.0-beta', '["车载", "语音交互", "OTA"]'::JSONB, 'admin', NOW() - INTERVAL '30 days'),
    ('prod_002', '智慧家庭平台', '全屋智能控制中枢，支持多协议设备接入、场景联动、AI节能', 'active', '2026年Q3发布', '2.5.0', '["IoT", "全屋智能", "AI节能"]'::JSONB, 'admin', NOW() - INTERVAL '25 days');

INSERT INTO manage_product_members (product_id, user_id, role, created_at)
VALUES
    ('prod_001', 'user_zhangsan', 'owner', NOW() - INTERVAL '30 days'),
    ('prod_001', 'user_lisi', 'admin', NOW() - INTERVAL '28 days'),
    ('prod_001', 'user_wangwu', 'member', NOW() - INTERVAL '20 days'),
    ('prod_001', 'user_zhaoliu', 'viewer', NOW() - INTERVAL '15 days'),
    ('prod_002', 'user_zhangsan', 'owner', NOW() - INTERVAL '25 days'),
    ('prod_002', 'user_sunqi', 'admin', NOW() - INTERVAL '22 days'),
    ('prod_002', 'user_wangwu', 'member', NOW() - INTERVAL '18 days');

-- ============================================================
-- 二、项目层测试数据
-- ============================================================

INSERT INTO manage_projects (project_id, name, description, status, product_id, created_by, created_at)
VALUES
    ('proj_001', '车载语音助手重构', '重构车载语音助手核心引擎，提升识别率和响应速度', 'active', 'prod_001', 'user_zhangsan', NOW() - INTERVAL '20 days'),
    ('proj_002', '多音源管理系统', '实现车内多音源混合播放与独立音量控制', 'active', 'prod_001', 'user_lisi', NOW() - INTERVAL '18 days'),
    ('proj_003', '智能家居设备接入平台', '支持Matter/ZigBee/蓝牙多协议设备统一接入', 'active', 'prod_002', 'user_zhangsan', NOW() - INTERVAL '15 days');

-- ============================================================
-- 三、需求层测试数据（含树形结构）
-- ============================================================

-- 项目1：车载语音助手重构 - 需求树
INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title, description, priority, assignee, parent_id, order_index, source_req_id, source_level, created_by, created_at)
VALUES
    ('req_001', 'proj_001', 'top_level', 'confirmed', '语音助手性能提升', '将语音助手平均响应时间从800ms降低到300ms以内', 'high', 'user_zhangsan', NULL, 0, NULL, NULL, 'user_zhangsan', NOW() - INTERVAL '15 days'),

    ('req_002', 'proj_001', 'low_level', 'in_progress', 'ASR识别引擎升级', '升级ASR引擎版本，识别率从92%提升到97%', 'high', 'user_wangwu', 'req_001', 0, NULL, NULL, 'user_wangwu', NOW() - INTERVAL '12 days'),
    ('req_003', 'proj_001', 'low_level', 'draft', 'NLU语义理解优化', '引入大语言模型提升意图识别准确率', 'medium', 'user_zhaoliu', 'req_001', 1, NULL, NULL, 'user_zhaoliu', NOW() - INTERVAL '10 days'),
    ('req_004', 'proj_001', 'task', 'completed', '本地缓存机制实现', '实现离线语音指令本地缓存，减少云端依赖', 'medium', 'user_wangwu', 'req_002', 0, NULL, NULL, 'user_wangwu', NOW() - INTERVAL '8 days'),

    ('req_005', 'proj_001', 'top_level', 'under_review', '多方言支持', '支持普通话、粤语、四川话等6种方言', 'medium', 'user_zhangsan', NULL, 1, NULL, NULL, 'user_zhangsan', NOW() - INTERVAL '14 days'),
    ('req_006', 'proj_001', 'low_level', 'draft', '方言声学模型训练', '收集并标注各地方言训练数据，训练专属声学模型', 'high', 'user_wangwu', 'req_005', 0, NULL, NULL, 'user_wangwu', NOW() - INTERVAL '9 days'),
    ('req_007', 'proj_001', 'low_level', 'draft', '方言切换UI交互', '用户可一键切换方言，提供方言切换反馈音', 'low', 'user_zhaoliu', 'req_005', 1, NULL, NULL, 'user_zhaoliu', NOW() - INTERVAL '7 days'),

    ('req_008', 'proj_001', 'top_level', 'confirmed', '车载环境降噪增强', '在高速行驶（>100km/h）环境下保持高识别率', 'high', 'user_lisi', NULL, 2, NULL, NULL, 'user_lisi', NOW() - INTERVAL '13 days'),
    ('req_009', 'proj_001', 'low_level', 'in_progress', '麦克风阵列信号增强', '采用多麦克风阵列，实现声源定位与回声消除', 'high', 'user_lisi', 'req_008', 0, NULL, NULL, 'user_lisi', NOW() - INTERVAL '6 days'),
    ('req_010', 'proj_001', 'task', 'draft', '风噪抑制算法集成', '集成自适应风噪抑制算法，衰减车窗外风噪', 'medium', 'user_wangwu', 'req_008', 1, NULL, NULL, 'user_wangwu', NOW() - INTERVAL '5 days');

-- 项目2：多音源管理系统 - 需求树
INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title, description, priority, assignee, parent_id, order_index, created_by, created_at)
VALUES
    ('req_011', 'proj_002', 'top_level', 'confirmed', '多音源混音播放', '支持蓝牙音乐、导航播报、语音助手同时发声且互不干扰', 'high', 'user_lisi', NULL, 0, 'user_lisi', NOW() - INTERVAL '12 days'),
    ('req_012', 'proj_002', 'low_level', 'in_progress', '音频优先级管理', '实现多音源优先级队列，导航播报最高优先', 'high', 'user_wangwu', 'req_011', 0, 'user_wangwu', NOW() - INTERVAL '10 days'),
    ('req_013', 'proj_002', 'low_level', 'draft', '独立音量控制', '各音源音量独立可调，保存用户偏好', 'medium', 'user_zhaoliu', 'req_011', 1, 'user_zhaoliu', NOW() - INTERVAL '8 days'),
    ('req_014', 'proj_002', 'task', 'completed', '混音算法DSP实现', '在DSP芯片上实现实时混音算法，延迟<10ms', 'high', 'user_wangwu', 'req_012', 0, 'user_wangwu', NOW() - INTERVAL '5 days'),

    ('req_015', 'proj_002', 'top_level', 'draft', '音源状态可视化', '中控屏实时显示各音源播放状态与音量', 'low', 'user_lisi', NULL, 1, 'user_lisi', NOW() - INTERVAL '9 days');

-- 项目3：智能家居设备接入平台 - 需求树
INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title, description, priority, assignee, parent_id, order_index, created_by, created_at)
VALUES
    ('req_016', 'proj_003', 'top_level', 'confirmed', '多协议设备接入', '支持Matter、ZigBee、蓝牙、WiFi四种协议设备统一接入', 'high', 'user_zhangsan', NULL, 0, 'user_zhangsan', NOW() - INTERVAL '10 days'),
    ('req_017', 'proj_003', 'low_level', 'in_progress', 'Matter协议网关', '实现Matter协议主控网关，支持Matter设备发现与控制', 'high', 'user_sunqi', 'req_016', 0, 'user_sunqi', NOW() - INTERVAL '8 days'),
    ('req_018', 'proj_003', 'low_level', 'draft', 'ZigBee协议适配层', '实现ZigBee设备接入适配层，支持主流ZigBee传感器', 'medium', 'user_wangwu', 'req_016', 1, 'user_wangwu', NOW() - INTERVAL '6 days'),
    ('req_019', 'proj_003', 'task', 'draft', '设备数据模型标准化', '统一设备属性、事件、命令的数据模型', 'medium', 'user_sunqi', 'req_017', 0, 'user_sunqi', NOW() - INTERVAL '4 days'),

    ('req_020', 'proj_003', 'top_level', 'under_review', 'AI场景联动引擎', '基于用户习惯自动生成场景联动规则，支持手动编辑', 'high', 'user_zhangsan', NULL, 1, 'user_zhangsan', NOW() - INTERVAL '9 days'),
    ('req_021', 'proj_003', 'low_level', 'draft', '用户行为学习模块', '通过ML模型学习用户开关灯、温度调节等习惯', 'high', 'user_sunqi', 'req_020', 0, 'user_sunqi', NOW() - INTERVAL '3 days');

-- ============================================================
-- 四、测试用例数据
-- ============================================================

INSERT INTO manage_test_cases (test_case_id, project_id, title, description, status, source, created_by, created_at)
VALUES
    ('tc_001', 'proj_001', 'ASR识别率测试-安静环境', '在30dB安静环境下，测试10条常用指令识别率', 'active', 'req_002', 'user_wangwu', NOW() - INTERVAL '10 days'),
    ('tc_002', 'proj_001', 'ASR识别率测试-车载噪声', '在模拟高速行驶噪声环境下测试识别率', 'active', 'req_002', 'user_wangwu', NOW() - INTERVAL '9 days'),
    ('tc_003', 'proj_001', 'ASR响应时间测试', '测试从说话结束到结果返回的端到端延迟', 'active', 'req_002', 'user_wangwu', NOW() - INTERVAL '8 days'),
    ('tc_004', 'proj_001', 'NLU意图识别测试', '测试10种不同意图的表达方式识别准确率', 'draft', 'req_003', 'user_zhaoliu', NOW() - INTERVAL '7 days'),
    ('tc_005', 'proj_001', '离线缓存功能测试', '网络断开后验证本地缓存指令仍可执行', 'active', 'req_004', 'user_wangwu', NOW() - INTERVAL '6 days'),
    ('tc_006', 'proj_001', '方言切换功能测试', '验证方言切换后识别结果正确性', 'draft', 'req_006', 'user_wangwu', NOW() - INTERVAL '5 days'),
    ('tc_007', 'proj_001', '麦克风阵列声源定位', '测试声源定位精度，误差应<15度', 'active', 'req_009', 'user_lisi', NOW() - INTERVAL '4 days'),
    ('tc_008', 'proj_001', '风噪抑制效果测试', '在80km/h模拟风速下测试语音识别率', 'draft', 'req_010', 'user_wangwu', NOW() - INTERVAL '3 days'),

    ('tc_009', 'proj_002', '多音源同时播放测试', '蓝牙音乐+导航播报同时进行，验证混音效果', 'active', 'req_011', 'user_lisi', NOW() - INTERVAL '8 days'),
    ('tc_010', 'proj_002', '导航播报打断音乐测试', '导航播报时自动压低音乐音量，播报结束后恢复', 'active', 'req_012', 'user_wangwu', NOW() - INTERVAL '7 days'),
    ('tc_011', 'proj_002', '独立音量保存测试', '调节各音源音量后重启系统，验证保存与恢复', 'active', 'req_013', 'user_zhaoliu', NOW() - INTERVAL '6 days'),
    ('tc_012', 'proj_002', 'DSP混音延迟测试', '测试混音算法实际延迟是否<10ms', 'active', 'req_014', 'user_wangwu', NOW() - INTERVAL '5 days'),

    ('tc_013', 'proj_003', 'Matter设备发现测试', '测试Matter设备上电后自动被发现', 'active', 'req_017', 'user_sunqi', NOW() - INTERVAL '6 days'),
    ('tc_014', 'proj_003', 'Matter设备控制测试', '验证开关、调光等基本控制命令正确执行', 'active', 'req_017', 'user_sunqi', NOW() - INTERVAL '5 days'),
    ('tc_015', 'proj_003', 'ZigBee设备接入测试', '测试温湿度传感器、门磁等ZigBee设备接入', 'draft', 'req_018', 'user_wangwu', NOW() - INTERVAL '4 days'),
    ('tc_016', 'proj_003', '场景联动触发测试', '设置"回家模式"场景，验证联动动作正确执行', 'draft', 'req_021', 'user_sunqi', NOW() - INTERVAL '3 days');

-- ============================================================
-- 五、需求-测试用例关联
-- ============================================================

INSERT INTO manage_requirement_test_links (requirement_id, test_case_id, link_type, created_at)
VALUES
    ('req_002', 'tc_001', 'verification', NOW() - INTERVAL '10 days'),
    ('req_002', 'tc_002', 'verification', NOW() - INTERVAL '9 days'),
    ('req_002', 'tc_003', 'verification', NOW() - INTERVAL '8 days'),
    ('req_003', 'tc_004', 'verification', NOW() - INTERVAL '7 days'),
    ('req_004', 'tc_005', 'verification', NOW() - INTERVAL '6 days'),
    ('req_006', 'tc_006', 'verification', NOW() - INTERVAL '5 days'),
    ('req_009', 'tc_007', 'verification', NOW() - INTERVAL '4 days'),
    ('req_010', 'tc_008', 'verification', NOW() - INTERVAL '3 days'),
    ('req_011', 'tc_009', 'verification', NOW() - INTERVAL '8 days'),
    ('req_012', 'tc_010', 'verification', NOW() - INTERVAL '7 days'),
    ('req_013', 'tc_011', 'verification', NOW() - INTERVAL '6 days'),
    ('req_014', 'tc_012', 'verification', NOW() - INTERVAL '5 days'),
    ('req_017', 'tc_013', 'verification', NOW() - INTERVAL '6 days'),
    ('req_017', 'tc_014', 'verification', NOW() - INTERVAL '5 days'),
    ('req_018', 'tc_015', 'verification', NOW() - INTERVAL '4 days'),
    ('req_021', 'tc_016', 'verification', NOW() - INTERVAL '3 days');

-- ============================================================
-- 六、缺陷数据
-- ============================================================

INSERT INTO manage_defects (defect_id, project_id, requirement_id, title, reproduce_steps, severity, priority, status, reporter, current_assignee, created_by, created_at)
VALUES
    ('def_001', 'proj_001', 'req_002', 'ASR在高速行驶时识别率骤降', '1. 车速超过100km/h\n2. 开启音乐（音量60%）\n3. 说"导航到最近的加油站"\n4. 识别失败或识别错误', 'critical', 'P0', 'in_progress', 'user_zhangsan', 'user_wangwu', 'user_zhangsan', NOW() - INTERVAL '5 days'),
    ('def_002', 'proj_001', 'req_003', 'NLU意图识别对方言口音理解偏差', '用四川话表达"把空调温度调低一点"，系统识别为"关闭空调"', 'high', 'P1', 'open', 'user_zhaoliu', 'user_zhaoliu', 'user_zhaoliu', NOW() - INTERVAL '4 days'),
    ('def_003', 'proj_001', 'req_004', '离线缓存满后未自动清理', '连续使用离线功能7天后，缓存达到500MB上限，但未触发清理', 'medium', 'P2', 'open', 'user_wangwu', 'user_wangwu', 'user_wangwu', NOW() - INTERVAL '3 days'),
    ('def_004', 'proj_001', 'req_009', '麦克风阵列在低温环境下失效', '-10°C环境下，麦克风阵列无法正常工作', 'critical', 'P0', 'open', 'user_lisi', 'user_lisi', 'user_lisi', NOW() - INTERVAL '2 days'),

    ('def_005', 'proj_002', 'req_012', '导航播报时音乐音量压低过度', '导航播报时音乐压到几乎无声，用户体验差', 'medium', 'P2', 'in_progress', 'user_lisi', 'user_wangwu', 'user_lisi', NOW() - INTERVAL '4 days'),
    ('def_006', 'proj_002', 'req_014', 'DSP混音延迟实测为15ms，超过10ms目标', '使用专业音频测试仪测量，混音延迟为15ms', 'high', 'P1', 'in_progress', 'user_wangwu', 'user_wangwu', 'user_wangwu', NOW() - INTERVAL '3 days'),

    ('def_007', 'proj_003', 'req_017', 'Matter设备配网失败率高', '10次配网尝试中有3次失败，失败原因均为超时', 'high', 'P1', 'open', 'user_sunqi', 'user_sunqi', 'user_sunqi', NOW() - INTERVAL '3 days'),
    ('def_008', 'proj_003', 'req_021', 'AI场景联动误触发', '用户仅开门（未进门），回家模式已触发，导致空调提前开启', 'medium', 'P2', 'open', 'user_zhangsan', 'user_sunqi', 'user_zhangsan', NOW() - INTERVAL '2 days');

-- ============================================================
-- 七、里程碑数据
-- ============================================================

INSERT INTO manage_milestones (milestone_id, project_id, name, description, message, milestone_type, is_baseline, sprint, version, tags, created_by, created_at)
VALUES
    ('ms_001', 'proj_001', 'V3.0-M1 语音核心', '语音助手核心性能优化第一阶段里程碑', '完成ASR引擎升级与本地缓存', 'baseline', TRUE, 'Sprint-2026-W13', '3.0.0-M1', '["语音", "性能"]'::JSONB, 'user_zhangsan', NOW() - INTERVAL '10 days'),
    ('ms_002', 'proj_001', 'V3.0-M2 方言支持', '多方言支持功能里程碑', '完成方言声学模型训练与集成', 'regular', FALSE, 'Sprint-2026-W16', '3.0.0-M2', '["方言", "语音"]'::JSONB, 'user_zhangsan', NOW() - INTERVAL '8 days'),
    ('ms_003', 'proj_001', 'V3.0-M3 降噪增强', '车载环境降噪最终里程碑', '完成麦克风阵列与降噪算法集成', 'regular', FALSE, 'Sprint-2026-W19', '3.0.0-M3', '["降噪", "车载"]'::JSONB, 'user_lisi', NOW() - INTERVAL '6 days'),

    ('ms_004', 'proj_002', 'V2.1-M1 混音架构', '多音源混音架构完成里程碑', 'DSP混音算法验证完成', 'baseline', TRUE, 'Sprint-2026-W14', '2.1.0-M1', '["混音", "DSP"]'::JSONB, 'user_lisi', NOW() - INTERVAL '9 days'),
    ('ms_005', 'proj_002', 'V2.1-M2 产品发布', '多音源管理系统正式发布', '所有功能通过验收测试', 'regular', FALSE, 'Sprint-2026-W17', '2.1.0', '["发布"]'::JSONB, 'user_lisi', NOW() - INTERVAL '5 days'),

    ('ms_006', 'proj_003', 'V2.5-M1 协议接入', '多协议接入第一阶段', '完成Matter协议网关实现', 'baseline', TRUE, 'Sprint-2026-W15', '2.5.0-M1', '["Matter", "接入"]'::JSONB, 'user_zhangsan', NOW() - INTERVAL '7 days');

-- ============================================================
-- 八、里程碑节点数据（需求快照）
-- ============================================================

INSERT INTO manage_milestone_nodes (snapshot_id, milestone_id, requirement_id, requirement_type, status, title, description, parent_id, order_index, snapshot_data, created_at)
VALUES
    ('snap_001', 'ms_001', 'req_002', 'low_level', 'in_progress', 'ASR识别引擎升级', '升级ASR引擎版本，识别率从92%提升到97%', 'req_001', 0, '{"priority": "high", "assignee": "user_wangwu"}'::JSONB, NOW() - INTERVAL '10 days'),
    ('snap_002', 'ms_001', 'req_003', 'low_level', 'draft', 'NLU语义理解优化', '引入大语言模型提升意图识别准确率', 'req_001', 1, '{"priority": "medium", "assignee": "user_zhaoliu"}'::JSONB, NOW() - INTERVAL '10 days'),
    ('snap_003', 'ms_001', 'req_004', 'task', 'completed', '本地缓存机制实现', '实现离线语音指令本地缓存，减少云端依赖', 'req_002', 0, '{"priority": "medium", "assignee": "user_wangwu"}'::JSONB, NOW() - INTERVAL '10 days'),
    ('snap_004', 'ms_001', 'req_008', 'top_level', 'confirmed', '车载环境降噪增强', '在高速行驶环境下保持高识别率', NULL, 2, '{"priority": "high", "assignee": "user_lisi"}'::JSONB, NOW() - INTERVAL '10 days'),

    ('snap_005', 'ms_004', 'req_011', 'top_level', 'confirmed', '多音源混音播放', '支持多音源同时发声且互不干扰', NULL, 0, '{"priority": "high", "assignee": "user_lisi"}'::JSONB, NOW() - INTERVAL '9 days'),
    ('snap_006', 'ms_004', 'req_012', 'low_level', 'in_progress', '音频优先级管理', '实现多音源优先级队列', 'req_011', 0, '{"priority": "high", "assignee": "user_wangwu"}'::JSONB, NOW() - INTERVAL '9 days'),
    ('snap_007', 'ms_004', 'req_014', 'task', 'completed', '混音算法DSP实现', '在DSP芯片上实现实时混音算法', 'req_012', 0, '{"priority": "high", "assignee": "user_wangwu"}'::JSONB, NOW() - INTERVAL '9 days'),

    ('snap_008', 'ms_006', 'req_016', 'top_level', 'confirmed', '多协议设备接入', '支持四种协议设备统一接入', NULL, 0, '{"priority": "high", "assignee": "user_zhangsan"}'::JSONB, NOW() - INTERVAL '7 days'),
    ('snap_009', 'ms_006', 'req_017', 'low_level', 'in_progress', 'Matter协议网关', '实现Matter协议主控网关', 'req_016', 0, '{"priority": "high", "assignee": "user_sunqi"}'::JSONB, NOW() - INTERVAL '7 days');

-- ============================================================
-- 九、分支与变更数据
-- ============================================================

INSERT INTO manage_branches (branch_id, project_id, base_milestone_id, name, status, metadata, created_by, created_at)
VALUES
    ('branch_001', 'proj_001', 'ms_001', 'feature/dialect-support', 'active', '{"reason": "多方言支持需要独立开发分支"}'::JSONB, 'user_wangwu', NOW() - INTERVAL '5 days'),
    ('branch_002', 'proj_001', 'ms_001', 'feature/noise-reduction', 'active', '{"reason": "降噪算法独立验证分支"}'::JSONB, 'user_lisi', NOW() - INTERVAL '4 days'),

    ('branch_003', 'proj_002', 'ms_004', 'fix/audio-latency', 'under_review', '{"reason": "修复DSP混音延迟超标问题"}'::JSONB, 'user_wangwu', NOW() - INTERVAL '3 days'),

    ('branch_004', 'proj_003', 'ms_006', 'feature/ai-scenarios', 'active', '{"reason": "AI场景联动功能开发分支"}'::JSONB, 'user_sunqi', NOW() - INTERVAL '4 days');

INSERT INTO manage_change_sets (change_id, branch_id, change_type, requirement_id, before_data, after_data, created_by, created_at)
VALUES
    ('cs_001', 'branch_001', 'added', 'req_006', NULL, '{"title": "方言声学模型训练", "status": "draft"}'::JSONB, 'user_wangwu', NOW() - INTERVAL '4 days'),
    ('cs_002', 'branch_001', 'added', 'req_007', NULL, '{"title": "方言切换UI交互", "status": "draft"}'::JSONB, 'user_wangwu', NOW() - INTERVAL '3 days'),
    ('cs_003', 'branch_001', 'modified', 'req_005', '{"status": "confirmed"}'::JSONB, '{"status": "under_review"}'::JSONB, 'user_wangwu', NOW() - INTERVAL '2 days'),
    ('cs_004', 'branch_001', 'added', 'req_007', NULL, '{"title": "方言切换功能测试", "status": "draft"}'::JSONB, 'user_wangwu', NOW() - INTERVAL '2 days'),

    ('cs_005', 'branch_002', 'added', 'req_009', NULL, '{"title": "麦克风阵列信号增强", "status": "in_progress"}'::JSONB, 'user_lisi', NOW() - INTERVAL '3 days'),
    ('cs_006', 'branch_002', 'added', 'req_010', NULL, '{"title": "风噪抑制算法集成", "status": "draft"}'::JSONB, 'user_lisi', NOW() - INTERVAL '2 days'),
    ('cs_007', 'branch_002', 'added', 'req_009', NULL, '{"title": "麦克风阵列声源定位", "status": "active"}'::JSONB, 'user_lisi', NOW() - INTERVAL '2 days'),

    ('cs_008', 'branch_003', 'modified', 'req_014', '{"DSP_latency": "15ms"}'::JSONB, '{"DSP_latency": "8ms", "status": "completed"}'::JSONB, 'user_wangwu', NOW() - INTERVAL '2 days'),

    ('cs_009', 'branch_004', 'added', 'req_020', NULL, '{"title": "AI场景联动引擎", "status": "under_review"}'::JSONB, 'user_sunqi', NOW() - INTERVAL '3 days'),
    ('cs_010', 'branch_004', 'added', 'req_021', NULL, '{"title": "用户行为学习模块", "status": "draft"}'::JSONB, 'user_sunqi', NOW() - INTERVAL '2 days');

-- ============================================================
-- 十、审计日志数据
-- ============================================================

INSERT INTO manage_audit_logs (log_id, project_id, product_id, actor, action, target_type, target_id, detail, created_at)
VALUES
    -- 产品创建日志
    ('log_001', NULL, 'prod_001', 'user_zhangsan', '创建产品', 'product', 'prod_001', '{"product_name": "智能车载系统 V3.0"}'::JSONB, NOW() - INTERVAL '30 days'),
    ('log_002', NULL, 'prod_002', 'user_zhangsan', '创建产品', 'product', 'prod_002', '{"product_name": "智慧家庭平台"}'::JSONB, NOW() - INTERVAL '25 days'),

    -- 项目创建日志
    ('log_003', 'proj_001', 'prod_001', 'user_zhangsan', '创建项目', 'project', 'proj_001', '{"project_name": "车载语音助手重构"}'::JSONB, NOW() - INTERVAL '20 days'),
    ('log_004', 'proj_002', 'prod_001', 'user_lisi', '创建项目', 'project', 'proj_002', '{"project_name": "多音源管理系统"}'::JSONB, NOW() - INTERVAL '18 days'),
    ('log_005', 'proj_003', 'prod_002', 'user_zhangsan', '创建项目', 'project', 'proj_003', '{"project_name": "智能家居设备接入平台"}'::JSONB, NOW() - INTERVAL '15 days'),

    -- 需求状态变更
    ('log_006', 'proj_001', 'prod_001', 'user_zhangsan', '确认需求', 'requirement', 'req_001', '{"title": "语音助手性能提升", "old_status": "draft", "new_status": "confirmed"}'::JSONB, NOW() - INTERVAL '15 days'),
    ('log_007', 'proj_001', 'prod_001', 'user_wangwu', '开始工作', 'requirement', 'req_002', '{"title": "ASR识别引擎升级", "old_status": "draft", "new_status": "in_progress"}'::JSONB, NOW() - INTERVAL '12 days'),
    ('log_008', 'proj_001', 'prod_001', 'user_wangwu', '完成任务', 'requirement', 'req_004', '{"title": "本地缓存机制实现", "old_status": "in_progress", "new_status": "completed"}'::JSONB, NOW() - INTERVAL '8 days'),
    ('log_009', 'proj_001', 'prod_001', 'user_zhangsan', '提交评审', 'requirement', 'req_005', '{"title": "多方言支持", "old_status": "confirmed", "new_status": "under_review"}'::JSONB, NOW() - INTERVAL '14 days'),
    ('log_010', 'proj_001', 'prod_001', 'user_lisi', '确认需求', 'requirement', 'req_008', '{"title": "车载环境降噪增强", "old_status": "draft", "new_status": "confirmed"}'::JSONB, NOW() - INTERVAL '13 days'),
    ('log_011', 'proj_001', 'prod_001', 'user_lisi', '开始工作', 'requirement', 'req_009', '{"title": "麦克风阵列信号增强", "old_status": "draft", "new_status": "in_progress"}'::JSONB, NOW() - INTERVAL '6 days'),

    -- 项目2需求变更
    ('log_012', 'proj_002', 'prod_001', 'user_lisi', '确认需求', 'requirement', 'req_011', '{"title": "多音源混音播放", "old_status": "draft", "new_status": "confirmed"}'::JSONB, NOW() - INTERVAL '12 days'),
    ('log_013', 'proj_002', 'prod_001', 'user_wangwu', '开始工作', 'requirement', 'req_012', '{"title": "音频优先级管理", "old_status": "draft", "new_status": "in_progress"}'::JSONB, NOW() - INTERVAL '10 days'),
    ('log_014', 'proj_002', 'prod_001', 'user_wangwu', '完成任务', 'requirement', 'req_014', '{"title": "混音算法DSP实现", "old_status": "in_progress", "new_status": "completed"}'::JSONB, NOW() - INTERVAL '5 days'),

    -- 项目3需求变更
    ('log_015', 'proj_003', 'prod_002', 'user_zhangsan', '确认需求', 'requirement', 'req_016', '{"title": "多协议设备接入", "old_status": "draft", "new_status": "confirmed"}'::JSONB, NOW() - INTERVAL '10 days'),
    ('log_016', 'proj_003', 'prod_002', 'user_sunqi', '开始工作', 'requirement', 'req_017', '{"title": "Matter协议网关", "old_status": "draft", "new_status": "in_progress"}'::JSONB, NOW() - INTERVAL '8 days'),
    ('log_017', 'proj_003', 'prod_002', 'user_zhangsan', '提交评审', 'requirement', 'req_020', '{"title": "AI场景联动引擎", "old_status": "draft", "new_status": "under_review"}'::JSONB, NOW() - INTERVAL '9 days'),

    -- 缺陷创建与更新
    ('log_018', 'proj_001', 'prod_001', 'user_zhangsan', '创建缺陷', 'defect', 'def_001', '{"title": "ASR在高速行驶时识别率骤降", "severity": "critical", "priority": "P0"}'::JSONB, NOW() - INTERVAL '5 days'),
    ('log_019', 'proj_001', 'prod_001', 'user_wangwu', '开始修复', 'defect', 'def_001', '{"old_status": "open", "new_status": "in_progress", "assignee": "user_wangwu"}'::JSONB, NOW() - INTERVAL '4 days'),
    ('log_020', 'proj_001', 'prod_001', 'user_zhaoliu', '创建缺陷', 'defect', 'def_002', '{"title": "NLU意图识别对方言口音理解偏差", "severity": "high", "priority": "P1"}'::JSONB, NOW() - INTERVAL '4 days'),
    ('log_021', 'proj_001', 'prod_001', 'user_lisi', '创建缺陷', 'defect', 'def_004', '{"title": "麦克风阵列在低温环境下失效", "severity": "critical", "priority": "P0"}'::JSONB, NOW() - INTERVAL '2 days'),
    ('log_022', 'proj_002', 'prod_001', 'user_wangwu', '开始修复', 'defect', 'def_006', '{"old_status": "open", "new_status": "in_progress"}'::JSONB, NOW() - INTERVAL '3 days'),
    ('log_023', 'proj_003', 'prod_002', 'user_sunqi', '创建缺陷', 'defect', 'def_007', '{"title": "Matter设备配网失败率高", "severity": "high", "priority": "P1"}'::JSONB, NOW() - INTERVAL '3 days'),

    -- 里程碑创建
    ('log_024', 'proj_001', 'prod_001', 'user_zhangsan', '创建里程碑', 'milestone', 'ms_001', '{"name": "V3.0-M1 语音核心", "is_baseline": true}'::JSONB, NOW() - INTERVAL '10 days'),
    ('log_025', 'proj_001', 'prod_001', 'user_zhangsan', '创建里程碑', 'milestone', 'ms_002', '{"name": "V3.0-M2 方言支持", "is_baseline": false}'::JSONB, NOW() - INTERVAL '8 days'),
    ('log_026', 'proj_002', 'prod_001', 'user_lisi', '创建里程碑', 'milestone', 'ms_004', '{"name": "V2.1-M1 混音架构", "is_baseline": true}'::JSONB, NOW() - INTERVAL '9 days'),
    ('log_027', 'proj_003', 'prod_002', 'user_zhangsan', '创建里程碑', 'milestone', 'ms_006', '{"name": "V2.5-M1 协议接入", "is_baseline": true}'::JSONB, NOW() - INTERVAL '7 days'),

    -- 分支创建
    ('log_028', 'proj_001', 'prod_001', 'user_wangwu', '创建分支', 'branch', 'branch_001', '{"name": "feature/dialect-support", "base_milestone": "ms_001"}'::JSONB, NOW() - INTERVAL '5 days'),
    ('log_029', 'proj_001', 'prod_001', 'user_lisi', '创建分支', 'branch', 'branch_002', '{"name": "feature/noise-reduction", "base_milestone": "ms_001"}'::JSONB, NOW() - INTERVAL '4 days'),
    ('log_030', 'proj_003', 'prod_002', 'user_sunqi', '创建分支', 'branch', 'branch_004', '{"name": "feature/ai-scenarios", "base_milestone": "ms_006"}'::JSONB, NOW() - INTERVAL '4 days'),

    -- 测试用例创建
    ('log_031', 'proj_001', 'prod_001', 'user_wangwu', '创建测试用例', 'test_case', 'tc_001', '{"title": "ASR识别率测试-安静环境"}'::JSONB, NOW() - INTERVAL '10 days'),
    ('log_032', 'proj_001', 'prod_001', 'user_wangwu', '创建测试用例', 'test_case', 'tc_003', '{"title": "ASR响应时间测试"}'::JSONB, NOW() - INTERVAL '8 days'),
    ('log_033', 'proj_002', 'prod_001', 'user_lisi', '创建测试用例', 'test_case', 'tc_009', '{"title": "多音源同时播放测试"}'::JSONB, NOW() - INTERVAL '8 days'),
    ('log_034', 'proj_003', 'prod_002', 'user_sunqi', '创建测试用例', 'test_case', 'tc_013', '{"title": "Matter设备发现测试"}'::JSONB, NOW() - INTERVAL '6 days');
