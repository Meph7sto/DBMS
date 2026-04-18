from __future__ import annotations

import copy
import re
from collections import defaultdict
from dataclasses import dataclass
from itertools import count
from typing import Any


def _normalize_sql(query: Any) -> str:
    return re.sub(r"\s+", " ", str(query)).strip().lower()


@dataclass
class FakeQueryResult:
    rows: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "result",
            "columns": list(self.rows[0].keys()) if self.rows else [],
            "rows": copy.deepcopy(self.rows),
            "row_count": len(self.rows),
        }


class FakeDB:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.products: dict[str, dict[str, Any]] = {}
        self.projects: dict[str, dict[str, Any]] = {}
        self.requirements: dict[str, dict[str, Any]] = {}
        self.test_cases: dict[str, dict[str, Any]] = {}
        self.defects: dict[str, dict[str, Any]] = {}
        self.milestones: dict[str, dict[str, Any]] = {}
        self.milestone_nodes: dict[str, dict[str, Any]] = {}
        self.branches: dict[str, dict[str, Any]] = {}
        self.change_sets: dict[str, dict[str, Any]] = {}
        self.comments: dict[str, dict[str, Any]] = {}
        self.audit_logs: dict[str, dict[str, Any]] = {}
        self.requirement_test_links: dict[int, dict[str, Any]] = {}
        self.requirement_links: dict[int, dict[str, Any]] = {}
        self._serials = defaultdict(lambda: count(1))
        self._clock = count(1)
        self.is_connected = True
        self.connection_info = {
            "host": "fake-localhost",
            "port": 5438,
            "database": "fake_db",
        }

    def seed_product(
        self,
        product_id: str,
        *,
        name: str,
        status: str = "active",
    ) -> dict[str, Any]:
        record = {
            "product_id": product_id,
            "name": name,
            "status": status,
            "description": None,
            "roadmap": None,
            "version": None,
            "tags": [],
            "created_by": None,
            "created_at": next(self._clock),
            "updated_at": next(self._clock),
        }
        self.products[product_id] = record
        return record

    def seed_project(
        self,
        project_id: str,
        *,
        name: str,
        product_id: str | None = None,
        status: str = "active",
    ) -> dict[str, Any]:
        record = {
            "project_id": project_id,
            "name": name,
            "status": status,
            "description": None,
            "product_id": product_id,
            "current_session_id": None,
            "created_by": None,
            "created_at": next(self._clock),
            "updated_at": next(self._clock),
        }
        self.projects[project_id] = record
        return record

    def seed_requirement(
        self,
        req_id: str,
        *,
        project_id: str,
        title: str,
        requirement_type: str,
        status: str = "draft",
        priority: str | None = None,
        parent_id: str | None = None,
        deleted: bool = False,
    ) -> dict[str, Any]:
        record = {
            "req_id": req_id,
            "project_id": project_id,
            "requirement_type": requirement_type,
            "status": status,
            "title": title,
            "description": None,
            "priority": priority,
            "assignee": None,
            "tags": [],
            "due_date": None,
            "parent_id": parent_id,
            "order_index": 0,
            "source_req_id": None,
            "source_level": None,
            "custom_fields": {},
            "is_planned": False,
            "created_by": None,
            "created_at": next(self._clock),
            "updated_by": None,
            "updated_at": next(self._clock),
            "deleted": deleted,
        }
        self.requirements[req_id] = record
        return record

    def seed_test_case(
        self,
        test_case_id: str,
        *,
        project_id: str,
        title: str,
        status: str = "draft",
    ) -> dict[str, Any]:
        record = {
            "test_case_id": test_case_id,
            "project_id": project_id,
            "title": title,
            "description": None,
            "status": status,
            "source": None,
            "created_by": None,
            "created_at": next(self._clock),
        }
        self.test_cases[test_case_id] = record
        return record

    def seed_defect(
        self,
        defect_id: str,
        *,
        project_id: str,
        requirement_id: str,
        title: str,
        severity: str = "medium",
        priority: str = "P2",
        status: str = "open",
    ) -> dict[str, Any]:
        record = {
            "defect_id": defect_id,
            "project_id": project_id,
            "requirement_id": requirement_id,
            "title": title,
            "reproduce_steps": "",
            "severity": severity,
            "priority": priority,
            "status": status,
            "reporter": None,
            "dev_assignee": None,
            "tester_assignee": None,
            "current_assignee": None,
            "created_by": None,
            "created_at": next(self._clock),
            "updated_by": None,
            "updated_at": next(self._clock),
        }
        self.defects[defect_id] = record
        return record

    def seed_milestone(
        self,
        milestone_id: str,
        *,
        project_id: str,
        name: str,
        milestone_type: str = "regular",
        is_baseline: bool = False,
        sprint: str | None = None,
        version: str | None = None,
    ) -> dict[str, Any]:
        record = {
            "milestone_id": milestone_id,
            "project_id": project_id,
            "name": name,
            "description": None,
            "message": None,
            "milestone_type": milestone_type,
            "is_baseline": is_baseline,
            "sprint": sprint,
            "version": version,
            "tags": [],
            "metadata": {},
            "created_by": None,
            "created_at": next(self._clock),
        }
        self.milestones[milestone_id] = record
        return record

    def seed_milestone_node(
        self,
        snapshot_id: str,
        *,
        milestone_id: str,
        requirement_id: str,
        status: str = "draft",
    ) -> dict[str, Any]:
        requirement = self.requirements[requirement_id]
        record = {
            "snapshot_id": snapshot_id,
            "milestone_id": milestone_id,
            "requirement_id": requirement_id,
            "requirement_type": requirement["requirement_type"],
            "status": status,
            "title": requirement["title"],
            "description": requirement["description"],
            "parent_id": requirement["parent_id"],
            "order_index": requirement["order_index"],
            "snapshot_data": {},
            "created_at": next(self._clock),
        }
        self.milestone_nodes[snapshot_id] = record
        return record

    def seed_requirement_test_link(
        self,
        requirement_id: str,
        test_case_id: str,
        *,
        link_type: str = "verification",
    ) -> dict[str, Any]:
        link_id = next(self._serials["requirement_test_links"])
        record = {
            "link_id": link_id,
            "requirement_id": requirement_id,
            "test_case_id": test_case_id,
            "link_type": link_type,
            "created_at": next(self._clock),
        }
        self.requirement_test_links[link_id] = record
        return record

    def seed_requirement_link(
        self,
        source_req_id: str,
        target_req_id: str,
        *,
        link_type: str,
    ) -> dict[str, Any]:
        link_id = next(self._serials["requirement_links"])
        record = {
            "link_id": link_id,
            "source_req_id": source_req_id,
            "target_req_id": target_req_id,
            "link_type": link_type,
        }
        self.requirement_links[link_id] = record
        return record

    def seed_branch(
        self,
        branch_id: str,
        *,
        project_id: str,
        base_milestone_id: str,
        name: str,
        status: str = "active",
    ) -> dict[str, Any]:
        record = {
            "branch_id": branch_id,
            "project_id": project_id,
            "base_milestone_id": base_milestone_id,
            "name": name,
            "status": status,
            "metadata": {},
            "created_by": None,
            "created_at": next(self._clock),
            "updated_at": next(self._clock),
        }
        self.branches[branch_id] = record
        return record

    def seed_change_set(
        self,
        change_id: str,
        *,
        branch_id: str,
        change_type: str,
        requirement_id: str | None = None,
    ) -> dict[str, Any]:
        record = {
            "change_id": change_id,
            "branch_id": branch_id,
            "change_type": change_type,
            "requirement_id": requirement_id,
            "before_data": {},
            "after_data": {},
            "created_by": None,
            "created_at": next(self._clock),
        }
        self.change_sets[change_id] = record
        return record

    def seed_comment(
        self,
        comment_id: str,
        *,
        project_id: str,
        target_type: str,
        target_id: str,
        content: str,
        reply_to_id: str | None = None,
        deleted: bool = False,
    ) -> dict[str, Any]:
        record = {
            "comment_id": comment_id,
            "project_id": project_id,
            "target_type": target_type,
            "target_id": target_id,
            "content": content,
            "reply_to_id": reply_to_id,
            "created_by": "seed",
            "deleted": deleted,
            "created_at": next(self._clock),
            "updated_at": next(self._clock),
        }
        self.comments[comment_id] = record
        return record

    def seed_audit_log(
        self,
        log_id: str,
        *,
        actor: str,
        action: str,
        project_id: str | None = None,
        product_id: str | None = None,
    ) -> dict[str, Any]:
        record = {
            "log_id": log_id,
            "project_id": project_id,
            "product_id": product_id,
            "actor": actor,
            "action": action,
            "target_type": None,
            "target_id": None,
            "detail": {},
            "created_at": next(self._clock),
        }
        self.audit_logs[log_id] = record
        return record

    def execute(self, query: Any, params: tuple[Any, ...] | None = None) -> dict[str, Any]:
        params = params or ()
        normalized = _normalize_sql(query)

        if normalized.startswith("select 1 from manage_products where product_id = %s"):
            return self._rows([{"?column?": 1}] if params[0] in self.products else [])
        if normalized.startswith("select 1 from manage_projects where project_id = %s"):
            return self._rows([{"?column?": 1}] if params[0] in self.projects else [])
        if normalized.startswith("select product_id, name from manage_products where product_id = %s"):
            product = self.products.get(params[0])
            return self._rows([self._pick(product, "product_id", "name")] if product else [])
        if normalized.startswith("select project_id, name, product_id from manage_projects where project_id = %s"):
            project = self.projects.get(params[0])
            return self._rows([self._pick(project, "project_id", "name", "product_id")] if project else [])
        if normalized.startswith("select req_id, project_id, requirement_type, parent_id, deleted from manage_requirements where req_id = %s"):
            requirement = self.requirements.get(params[0])
            if requirement and ("and deleted = false" not in normalized or not requirement["deleted"]):
                return self._rows([self._pick(requirement, "req_id", "project_id", "requirement_type", "parent_id", "deleted")])
            return self._rows([])
        if normalized.startswith("select req_id, project_id, title, requirement_type from manage_requirements where req_id = %s and deleted = false"):
            requirement = self.requirements.get(params[0])
            if requirement and not requirement["deleted"]:
                return self._rows([self._pick(requirement, "req_id", "project_id", "title", "requirement_type")])
            return self._rows([])
        if normalized.startswith("select test_case_id, project_id, title from manage_test_cases where test_case_id = %s"):
            test_case = self.test_cases.get(params[0])
            return self._rows([self._pick(test_case, "test_case_id", "project_id", "title")] if test_case else [])
        if normalized.startswith("select milestone_id, project_id, name from manage_milestones where milestone_id = %s"):
            milestone = self.milestones.get(params[0])
            return self._rows([self._pick(milestone, "milestone_id", "project_id", "name")] if milestone else [])
        if normalized.startswith("select branch_id, project_id, name from manage_branches where branch_id = %s"):
            branch = self.branches.get(params[0])
            return self._rows([self._pick(branch, "branch_id", "project_id", "name")] if branch else [])
        if normalized.startswith("select comment_id, project_id from manage_comments where comment_id = %s"):
            comment = self.comments.get(params[0])
            return self._rows([self._pick(comment, "comment_id", "project_id")] if comment else [])
        if normalized.startswith("select comment_id, project_id, target_type, target_id, reply_to_id, content, created_by, deleted from manage_comments where comment_id = %s"):
            comment = self.comments.get(params[0])
            return self._rows([self._pick(comment, "comment_id", "project_id", "target_type", "target_id", "reply_to_id", "content", "created_by", "deleted")] if comment else [])
        if normalized.startswith("select defect_id as target_id, project_id from manage_defects where defect_id = %s"):
            defect = self.defects.get(params[0])
            if defect:
                return self._rows([{"target_id": defect["defect_id"], "project_id": defect["project_id"]}])
            return self._rows([])
        if normalized.startswith("select test_case_id as target_id, project_id from manage_test_cases where test_case_id = %s"):
            test_case = self.test_cases.get(params[0])
            if test_case:
                return self._rows([{"target_id": test_case["test_case_id"], "project_id": test_case["project_id"]}])
            return self._rows([])
        if normalized.startswith("select milestone_id as target_id, project_id from manage_milestones where milestone_id = %s"):
            milestone = self.milestones.get(params[0])
            if milestone:
                return self._rows([{"target_id": milestone["milestone_id"], "project_id": milestone["project_id"]}])
            return self._rows([])
        if normalized.startswith("select req_id as target_id, project_id from manage_requirements where req_id = %s and deleted = false"):
            requirement = self.requirements.get(params[0])
            if requirement and not requirement["deleted"]:
                return self._rows([{"target_id": requirement["req_id"], "project_id": requirement["project_id"]}])
            return self._rows([])
        if normalized.startswith("select log_id, project_id, product_id, actor, action, target_type, target_id, detail from manage_audit_logs where log_id = %s"):
            audit_log = self.audit_logs.get(params[0])
            return self._rows([self._pick(audit_log, "log_id", "project_id", "product_id", "actor", "action", "target_type", "target_id", "detail")] if audit_log else [])
        if normalized.startswith("with recursive ancestors as ("):
            return self._rows([{"?column?": 1}] if self._would_create_cycle(params[0], params[1]) else [])

        if normalized.startswith("insert into manage_requirements"):
            return self._insert_requirement(params)
        if normalized.startswith("update manage_requirements set deleted = true"):
            return self._soft_delete_requirement(params)
        if normalized.startswith("update manage_requirements set"):
            return self._update_requirement(query, params)
        if normalized.startswith("insert into manage_test_cases"):
            return self._insert_test_case(params)
        if normalized.startswith("insert into manage_requirement_test_links"):
            return self._insert_requirement_test_link(params)
        if normalized.startswith("insert into manage_defects"):
            return self._insert_defect(params)
        if normalized.startswith("insert into manage_branches"):
            return self._insert_branch(params)
        if normalized.startswith("insert into manage_change_sets"):
            return self._insert_change_set(params)
        if normalized.startswith("delete from manage_milestones where milestone_id = %s"):
            return self._delete_milestone(params[0])
        if normalized.startswith("insert into manage_comments"):
            return self._insert_comment(params)
        if normalized.startswith("insert into manage_audit_logs"):
            return self._insert_audit_log(params)

        if normalized.startswith("select * from fn_requirement_trace(%s)"):
            return self._rows(self._requirement_trace_rows(params[0]))
        if normalized.startswith("select * from fn_project_progress(%s)"):
            return self._rows(self._project_progress_rows(params[0]))
        if normalized.startswith("select * from fn_milestone_delivery_risk(%s)"):
            return self._rows(self._milestone_risk_rows(params[0]))

        raise NotImplementedError(f"Unsupported query in FakeDB: {query}")

    def _rows(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        return FakeQueryResult(rows).to_dict()

    def _command(self, row_count: int) -> dict[str, Any]:
        return {
            "type": "command",
            "message": f"OK — {row_count} row(s) affected",
            "row_count": row_count,
        }

    @staticmethod
    def _pick(record: dict[str, Any] | None, *keys: str) -> dict[str, Any]:
        if record is None:
            return {}
        return {key: record.get(key) for key in keys}

    def _would_create_cycle(self, parent_id: str, current_req_id: str) -> bool:
        visited: set[str] = set()
        cursor = parent_id
        while cursor:
            if cursor == current_req_id:
                return True
            if cursor in visited:
                break
            visited.add(cursor)
            requirement = self.requirements.get(cursor)
            cursor = requirement.get("parent_id") if requirement else None
        return False

    def _insert_requirement(self, params: tuple[Any, ...]) -> dict[str, Any]:
        req_id, project_id, requirement_type, title, description, status, priority, assignee, parent_id, order_index, created_by = params
        if project_id not in self.projects:
            raise Exception("foreign key violation: project_id")
        self.requirements[req_id] = {
            "req_id": req_id,
            "project_id": project_id,
            "requirement_type": requirement_type,
            "status": status,
            "title": title,
            "description": description,
            "priority": priority,
            "assignee": assignee,
            "tags": [],
            "due_date": None,
            "parent_id": parent_id,
            "order_index": order_index,
            "source_req_id": None,
            "source_level": None,
            "custom_fields": {},
            "is_planned": False,
            "created_by": created_by,
            "created_at": next(self._clock),
            "updated_by": None,
            "updated_at": next(self._clock),
            "deleted": False,
        }
        return self._command(1)

    def _update_requirement(self, query: Any, params: tuple[Any, ...]) -> dict[str, Any]:
        normalized = _normalize_sql(query)
        fields = self._extract_update_fields(normalized)
        req_id = params[-2]
        deleted_flag = params[-1]
        record = self.requirements.get(req_id)
        if not record or record["deleted"] != deleted_flag:
            return self._command(0)
        for field, value in zip(fields, params[:-2], strict=True):
            record[field] = value
        record["updated_at"] = next(self._clock)
        return self._command(1)

    def _soft_delete_requirement(self, params: tuple[Any, ...]) -> dict[str, Any]:
        req_id = params[0]
        record = self.requirements.get(req_id)
        if not record or record["deleted"]:
            return self._command(0)
        record["deleted"] = True
        record["updated_at"] = next(self._clock)
        return self._command(1)

    def _insert_test_case(self, params: tuple[Any, ...]) -> dict[str, Any]:
        test_case_id, project_id, title, description, status, source, created_by = params
        if project_id not in self.projects:
            raise Exception("foreign key violation: project_id")
        self.test_cases[test_case_id] = {
            "test_case_id": test_case_id,
            "project_id": project_id,
            "title": title,
            "description": description,
            "status": status,
            "source": source,
            "created_by": created_by,
            "created_at": next(self._clock),
        }
        return self._command(1)

    def _insert_requirement_test_link(self, params: tuple[Any, ...]) -> dict[str, Any]:
        requirement_id, test_case_id, link_type = params
        for link in self.requirement_test_links.values():
            if link["requirement_id"] == requirement_id and link["test_case_id"] == test_case_id:
                raise Exception("duplicate key value violates unique constraint requirement_test_link")
        record = self.seed_requirement_test_link(requirement_id, test_case_id, link_type=link_type)
        return self._rows([{"link_id": record["link_id"]}])

    def _insert_defect(self, params: tuple[Any, ...]) -> dict[str, Any]:
        defect_id, project_id, requirement_id, title, reproduce_steps, severity, priority, status, reporter, current_assignee, created_by = params
        requirement = self.requirements.get(requirement_id)
        if requirement is None or requirement["deleted"]:
            raise Exception("foreign key violation: requirement_id")
        if requirement["project_id"] != project_id:
            raise Exception("foreign key violation: requirement project scope")
        self.defects[defect_id] = {
            "defect_id": defect_id,
            "project_id": project_id,
            "requirement_id": requirement_id,
            "title": title,
            "reproduce_steps": reproduce_steps,
            "severity": severity,
            "priority": priority,
            "status": status,
            "reporter": reporter,
            "dev_assignee": None,
            "tester_assignee": None,
            "current_assignee": current_assignee,
            "created_by": created_by,
            "created_at": next(self._clock),
            "updated_by": None,
            "updated_at": next(self._clock),
        }
        return self._command(1)

    def _insert_branch(self, params: tuple[Any, ...]) -> dict[str, Any]:
        branch_id, project_id, base_milestone_id, name, status, metadata, created_by = params
        for branch in self.branches.values():
            if branch["project_id"] == project_id and branch["name"] == name:
                raise Exception("duplicate key value violates unique constraint manage_branches_project_id_name_key")
        self.branches[branch_id] = {
            "branch_id": branch_id,
            "project_id": project_id,
            "base_milestone_id": base_milestone_id,
            "name": name,
            "status": status,
            "metadata": metadata or {},
            "created_by": created_by,
            "created_at": next(self._clock),
            "updated_at": next(self._clock),
        }
        return self._command(1)

    def _insert_change_set(self, params: tuple[Any, ...]) -> dict[str, Any]:
        change_id, branch_id, change_type, requirement_id, before_data, after_data, created_by = params
        self.change_sets[change_id] = {
            "change_id": change_id,
            "branch_id": branch_id,
            "change_type": change_type,
            "requirement_id": requirement_id,
            "before_data": before_data or {},
            "after_data": after_data or {},
            "created_by": created_by,
            "created_at": next(self._clock),
        }
        return self._command(1)

    def _delete_milestone(self, milestone_id: str) -> dict[str, Any]:
        if milestone_id not in self.milestones:
            return self._command(0)
        if any(branch["base_milestone_id"] == milestone_id for branch in self.branches.values()):
            raise Exception("foreign key violation: milestone is still referenced by branch")
        del self.milestones[milestone_id]
        return self._command(1)

    def _insert_comment(self, params: tuple[Any, ...]) -> dict[str, Any]:
        comment_id, project_id, target_type, target_id, content, reply_to_id, created_by, deleted = params
        if reply_to_id:
            parent = self.comments.get(reply_to_id)
            if parent and parent["project_id"] != project_id:
                raise Exception("foreign key violation: reply_to_id cross-project")
        self.comments[comment_id] = {
            "comment_id": comment_id,
            "project_id": project_id,
            "target_type": target_type,
            "target_id": target_id,
            "content": content,
            "reply_to_id": reply_to_id,
            "created_by": created_by,
            "deleted": deleted,
            "created_at": next(self._clock),
            "updated_at": next(self._clock),
        }
        return self._command(1)

    def _insert_audit_log(self, params: tuple[Any, ...]) -> dict[str, Any]:
        log_id, project_id, product_id, actor, action, target_type, target_id, detail = params
        if project_id and product_id:
            project = self.projects.get(project_id)
            if not project or project.get("product_id") != product_id:
                raise Exception("check violation: audit log project/product scope mismatch")
        self.audit_logs[log_id] = {
            "log_id": log_id,
            "project_id": project_id,
            "product_id": product_id,
            "actor": actor,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "detail": detail or {},
            "created_at": next(self._clock),
        }
        return self._command(1)

    @staticmethod
    def _extract_update_fields(normalized_query: str) -> list[str]:
        match = re.search(r"set (.+?) where", normalized_query)
        if not match:
            return []
        fields: list[str] = []
        for chunk in match.group(1).split(","):
            field = chunk.split("=")[0].strip()
            if field == "updated_at":
                continue
            fields.append(field)
        return fields

    def _requirement_trace_rows(self, project_id: str) -> list[dict[str, Any]]:
        project = self.projects.get(project_id)
        if not project:
            return []
        rows = []
        for requirement in sorted(self.requirements.values(), key=lambda item: item["created_at"], reverse=True):
            if requirement["project_id"] != project_id or requirement["deleted"]:
                continue
            test_links = [
                link for link in self.requirement_test_links.values()
                if link["requirement_id"] == requirement["req_id"]
            ]
            test_cases = []
            for link in test_links:
                test_case = self.test_cases.get(link["test_case_id"])
                if test_case:
                    test_cases.append({
                        "test_case_id": test_case["test_case_id"],
                        "title": test_case["title"],
                        "status": test_case["status"],
                        "link_type": link["link_type"],
                    })
            defects = []
            open_defect_count = 0
            for defect in self.defects.values():
                if defect["requirement_id"] != requirement["req_id"]:
                    continue
                defects.append({
                    "defect_id": defect["defect_id"],
                    "title": defect["title"],
                    "severity": defect["severity"],
                    "priority": defect["priority"],
                    "status": defect["status"],
                    "current_assignee": defect["current_assignee"],
                })
                if defect["status"] in {"open", "in_progress"}:
                    open_defect_count += 1
            rows.append({
                "req_id": requirement["req_id"],
                "requirement_title": requirement["title"],
                "requirement_type": requirement["requirement_type"],
                "status": requirement["status"],
                "priority": requirement["priority"],
                "assignee": requirement["assignee"],
                "project_name": project["name"],
                "test_cases": test_cases,
                "defects": defects,
                "test_case_count": len(test_cases),
                "total_defect_count": len(defects),
                "open_defect_count": open_defect_count,
            })
        return rows

    def _project_progress_rows(self, project_id: str) -> list[dict[str, Any]]:
        project = self.projects.get(project_id)
        if not project:
            return []
        requirements = [
            item for item in self.requirements.values()
            if item["project_id"] == project_id and not item["deleted"]
        ]
        defects = [item for item in self.defects.values() if item["project_id"] == project_id]
        milestones = [item for item in self.milestones.values() if item["project_id"] == project_id]
        covered_requirement_ids = {
            link["requirement_id"]
            for link in self.requirement_test_links.values()
            if self.requirements.get(link["requirement_id"], {}).get("project_id") == project_id
        }
        total_requirements = len(requirements)
        completed_requirements = sum(item["status"] == "completed" for item in requirements)
        in_progress_requirements = sum(item["status"] == "in_progress" for item in requirements)
        draft_requirements = sum(item["status"] == "draft" for item in requirements)
        total_defects = len(defects)
        critical_defects = sum(item["severity"] == "critical" for item in defects)
        open_defects = sum(item["status"] in {"open", "in_progress"} for item in defects)
        covered_requirements = len(covered_requirement_ids)
        completion_rate = round((completed_requirements / total_requirements) * 100, 2) if total_requirements else 0
        test_coverage_rate = round((covered_requirements / total_requirements) * 100, 2) if total_requirements else 0
        return [{
            "project_id": project["project_id"],
            "project_name": project["name"],
            "project_status": project["status"],
            "total_requirements": total_requirements,
            "completed_requirements": completed_requirements,
            "in_progress_requirements": in_progress_requirements,
            "draft_requirements": draft_requirements,
            "completion_rate_percent": completion_rate,
            "total_defects": total_defects,
            "critical_defects": critical_defects,
            "open_defects": open_defects,
            "total_requirements_for_coverage": total_requirements,
            "covered_requirements": covered_requirements,
            "test_coverage_rate_percent": test_coverage_rate,
            "total_milestones": len(milestones),
            "baseline_count": sum(item["is_baseline"] for item in milestones),
        }]

    def _milestone_risk_rows(self, project_id: str) -> list[dict[str, Any]]:
        project = self.projects.get(project_id)
        if not project:
            return []
        rows = []
        milestones = [
            milestone for milestone in self.milestones.values()
            if milestone["project_id"] == project_id
        ]
        for milestone in milestones:
            scoped_ids = [
                node["requirement_id"]
                for node in self.milestone_nodes.values()
                if node["milestone_id"] == milestone["milestone_id"]
            ]
            scoped_requirements = [
                self.requirements[req_id]
                for req_id in scoped_ids
                if req_id in self.requirements and not self.requirements[req_id]["deleted"]
            ]
            incomplete = sum(req["status"] != "completed" for req in scoped_requirements)
            uncovered = 0
            blocked = 0
            unresolved = 0
            critical = 0
            for req in scoped_requirements:
                active_links = [
                    link for link in self.requirement_test_links.values()
                    if link["requirement_id"] == req["req_id"]
                    and self.test_cases.get(link["test_case_id"], {}).get("status") == "active"
                ]
                if not active_links:
                    uncovered += 1
                has_blocker = any(
                    link["source_req_id"] == req["req_id"]
                    and link["link_type"] == "depends_on"
                    and not self.requirements.get(link["target_req_id"], {}).get("deleted", True)
                    and self.requirements.get(link["target_req_id"], {}).get("status") != "completed"
                    for link in self.requirement_links.values()
                )
                if has_blocker:
                    blocked += 1
                for defect in self.defects.values():
                    if defect["project_id"] == project_id and defect["requirement_id"] == req["req_id"]:
                        if defect["status"] not in {"closed", "rejected"}:
                            unresolved += 1
                            if defect["severity"] == "critical":
                                critical += 1
            milestone_branches = [
                branch for branch in self.branches.values()
                if branch["base_milestone_id"] == milestone["milestone_id"]
            ]
            active_branch_count = sum(branch["status"] in {"active", "under_review"} for branch in milestone_branches)
            pending_change_count = sum(
                1
                for change_set in self.change_sets.values()
                if self.branches.get(change_set["branch_id"], {}).get("base_milestone_id") == milestone["milestone_id"]
            )
            risk_score = incomplete * 2 + uncovered * 1.5 + blocked * 2 + unresolved * 2 + critical * 3 + pending_change_count
            if risk_score >= 8:
                risk_level = "high"
            elif risk_score >= 4:
                risk_level = "medium"
            else:
                risk_level = "low"
            latest_activity = max(
                (branch["updated_at"] for branch in milestone_branches),
                default=None,
            )
            rows.append({
                "milestone_id": milestone["milestone_id"],
                "milestone_name": milestone["name"],
                "milestone_type": milestone["milestone_type"],
                "is_baseline": milestone["is_baseline"],
                "sprint": milestone["sprint"],
                "version": milestone["version"],
                "project_name": project["name"],
                "scoped_requirement_count": len(scoped_requirements),
                "incomplete_requirement_count": incomplete,
                "uncovered_requirement_count": uncovered,
                "blocked_requirement_count": blocked,
                "unresolved_defect_count": unresolved,
                "critical_defect_count": critical,
                "active_branch_count": active_branch_count,
                "pending_change_count": pending_change_count,
                "latest_branch_activity": latest_activity,
                "risk_score": risk_score,
                "risk_level": risk_level,
            })
        return rows
