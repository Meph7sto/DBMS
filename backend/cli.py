"""Simple command-line demo menu for the database lab project."""

from __future__ import annotations

import json
from typing import Any, Callable, Optional

from fastapi import HTTPException
from pydantic import ValidationError

from config import get_default_connection
from database import db
from routers import crud, statistics


def print_header(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def print_result(data: Any) -> None:
    if data is None:
        print("操作完成。")
        return
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def prompt_text(label: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    return input(f"{label}{suffix}: ").strip()


def prompt_optional(label: str) -> Optional[str]:
    value = input(f"{label}（留空表示不填写）: ").strip()
    return value or None


def prompt_update_value(label: str) -> Optional[str]:
    value = input(f"{label}（留空表示不修改）: ").strip()
    return value or None


def prompt_int(label: str, default: Optional[int] = None) -> int:
    while True:
        raw = prompt_text(label, str(default) if default is not None else None)
        if not raw and default is not None:
            return default
        try:
            return int(raw)
        except ValueError:
            print("请输入整数。")


def prompt_optional_int(label: str) -> Optional[int]:
    raw = input(f"{label}（留空表示不修改）: ").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        print("输入不是整数，本次字段将忽略。")
        return None


def prompt_bool(label: str, default: Optional[bool] = None) -> bool:
    default_hint = ""
    if default is True:
        default_hint = " [Y]"
    elif default is False:
        default_hint = " [N]"

    while True:
        raw = input(f"{label} (y/n){default_hint}: ").strip().lower()
        if not raw and default is not None:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("请输入 y 或 n。")


def prompt_optional_bool(label: str) -> Optional[bool]:
    raw = input(f"{label}（输入 y/n，留空表示不修改）: ").strip().lower()
    if not raw:
        return None
    if raw in {"y", "yes"}:
        return True
    if raw in {"n", "no"}:
        return False
    print("输入无效，本次字段将忽略。")
    return None


def prompt_tags(label: str, *, update: bool = False) -> Optional[list[str]]:
    hint = "使用英文逗号分隔"
    if update:
        raw = input(f"{label}（{hint}，留空表示不修改）: ").strip()
        if not raw:
            return None
    else:
        raw = input(f"{label}（{hint}，留空表示无标签）: ").strip()
        if not raw:
            return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def run_action(func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    try:
        result = func(*args, **kwargs)
        print_result(result)
    except HTTPException as exc:
        print(f"操作失败：{exc.detail}")
    except ValidationError as exc:
        print(f"参数校验失败：{exc}")
    except Exception as exc:
        print(f"操作失败：{exc}")


def ensure_connection() -> bool:
    if db.is_connected:
        return True
    print("当前未连接数据库。")
    return connect_with_defaults()


def connect_with_defaults() -> bool:
    defaults = get_default_connection()
    try:
        info = db.connect(**defaults)
        print("已使用默认配置连接数据库：")
        print_result(info)
        return True
    except Exception as exc:
        print(f"默认连接失败：{exc}")
        return False


def reconnect_database() -> None:
    print_header("数据库连接")
    defaults = get_default_connection()
    use_defaults = prompt_bool("是否使用 .env 中的默认连接参数", default=True)
    if use_defaults:
        connect_with_defaults()
        return

    host = prompt_text("主机", defaults["host"]) or defaults["host"]
    port = prompt_int("端口", defaults["port"])
    user = prompt_text("用户名", defaults["user"]) or defaults["user"]
    password = prompt_text("密码", defaults["password"]) or defaults["password"]
    database = prompt_text("数据库名", defaults["database"]) or defaults["database"]
    try:
        info = db.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
        )
        print("连接成功。")
        print_result(info)
    except Exception as exc:
        print(f"连接失败：{exc}")


def list_products() -> None:
    run_action(crud.list_products)


def create_product() -> None:
    payload = crud.ProductCreate(
        name=prompt_text("产品名称"),
        description=prompt_optional("产品描述"),
        status=prompt_text("状态", "active") or "active",
        roadmap=prompt_optional("路线图"),
        version=prompt_optional("版本"),
        tags=prompt_tags("标签"),
        created_by=prompt_optional("创建人"),
    )
    run_action(crud.create_product, payload)


def update_product() -> None:
    product_id = prompt_text("产品 ID")
    payload = crud.ProductUpdate(
        name=prompt_update_value("产品名称"),
        description=prompt_update_value("产品描述"),
        status=prompt_update_value("状态"),
        roadmap=prompt_update_value("路线图"),
        version=prompt_update_value("版本"),
        tags=prompt_tags("标签", update=True),
    )
    run_action(crud.update_product, product_id, payload)


def delete_product() -> None:
    product_id = prompt_text("产品 ID")
    if prompt_bool(f"确认删除产品 {product_id}", default=False):
        run_action(crud.delete_product, product_id)


def list_projects() -> None:
    run_action(crud.list_projects)


def create_project() -> None:
    payload = crud.ProjectCreate(
        name=prompt_text("项目名称"),
        description=prompt_optional("项目描述"),
        status=prompt_text("状态", "active") or "active",
        product_id=prompt_optional("所属产品 ID"),
        created_by=prompt_optional("创建人"),
    )
    run_action(crud.create_project, payload)


def update_project() -> None:
    project_id = prompt_text("项目 ID")
    payload = crud.ProjectUpdate(
        name=prompt_update_value("项目名称"),
        description=prompt_update_value("项目描述"),
        status=prompt_update_value("状态"),
        product_id=prompt_update_value("所属产品 ID"),
    )
    run_action(crud.update_project, project_id, payload)


def delete_project() -> None:
    project_id = prompt_text("项目 ID")
    if prompt_bool(f"确认删除项目 {project_id}", default=False):
        run_action(crud.delete_project, project_id)


def list_requirements() -> None:
    project_id = prompt_optional("项目 ID 过滤")
    run_action(crud.list_requirements, project_id)


def create_requirement() -> None:
    payload = crud.RequirementCreate(
        project_id=prompt_text("项目 ID"),
        requirement_type=prompt_text("需求类型", "top_level") or "top_level",
        title=prompt_text("标题"),
        description=prompt_optional("描述"),
        status=prompt_text("状态", "draft") or "draft",
        priority=prompt_optional("优先级"),
        assignee=prompt_optional("负责人"),
        parent_id=prompt_optional("父需求 ID"),
        order_index=prompt_int("排序索引", 0),
        created_by=prompt_optional("创建人"),
    )
    run_action(crud.create_requirement, payload)


def update_requirement() -> None:
    req_id = prompt_text("需求 ID")
    payload = crud.RequirementUpdate(
        title=prompt_update_value("标题"),
        description=prompt_update_value("描述"),
        status=prompt_update_value("状态"),
        priority=prompt_update_value("优先级"),
        assignee=prompt_update_value("负责人"),
        parent_id=prompt_update_value("父需求 ID"),
        order_index=prompt_optional_int("排序索引"),
    )
    run_action(crud.update_requirement, req_id, payload)


def delete_requirement() -> None:
    req_id = prompt_text("需求 ID")
    if prompt_bool(f"确认删除需求 {req_id}", default=False):
        run_action(crud.delete_requirement, req_id)


def list_defects() -> None:
    project_id = prompt_optional("项目 ID 过滤")
    run_action(crud.list_defects, project_id)


def create_defect() -> None:
    payload = crud.DefectCreate(
        project_id=prompt_text("项目 ID"),
        requirement_id=prompt_text("关联需求 ID"),
        title=prompt_text("缺陷标题"),
        reproduce_steps=prompt_text("复现步骤", ""),
        severity=prompt_text("严重程度", "medium") or "medium",
        priority=prompt_text("优先级", "P2") or "P2",
        status=prompt_text("状态", "open") or "open",
        reporter=prompt_optional("报告人"),
        current_assignee=prompt_optional("当前处理人"),
        created_by=prompt_optional("创建人"),
    )
    run_action(crud.create_defect, payload)


def update_defect() -> None:
    defect_id = prompt_text("缺陷 ID")
    payload = crud.DefectUpdate(
        title=prompt_update_value("缺陷标题"),
        reproduce_steps=prompt_update_value("复现步骤"),
        severity=prompt_update_value("严重程度"),
        priority=prompt_update_value("优先级"),
        status=prompt_update_value("状态"),
        current_assignee=prompt_update_value("当前处理人"),
    )
    run_action(crud.update_defect, defect_id, payload)


def delete_defect() -> None:
    defect_id = prompt_text("缺陷 ID")
    if prompt_bool(f"确认删除缺陷 {defect_id}", default=False):
        run_action(crud.delete_defect, defect_id)


def list_test_cases() -> None:
    project_id = prompt_optional("项目 ID 过滤")
    run_action(crud.list_test_cases, project_id)


def create_test_case() -> None:
    payload = crud.TestCaseCreate(
        project_id=prompt_text("项目 ID"),
        title=prompt_text("测试用例标题"),
        description=prompt_optional("描述"),
        status=prompt_text("状态", "draft") or "draft",
        source=prompt_optional("来源需求/备注"),
        created_by=prompt_optional("创建人"),
    )
    run_action(crud.create_test_case, payload)


def update_test_case() -> None:
    test_case_id = prompt_text("测试用例 ID")
    payload = crud.TestCaseUpdate(
        title=prompt_update_value("测试用例标题"),
        description=prompt_update_value("描述"),
        status=prompt_update_value("状态"),
    )
    run_action(crud.update_test_case, test_case_id, payload)


def delete_test_case() -> None:
    test_case_id = prompt_text("测试用例 ID")
    if prompt_bool(f"确认删除测试用例 {test_case_id}", default=False):
        run_action(crud.delete_test_case, test_case_id)


def list_milestones() -> None:
    project_id = prompt_optional("项目 ID 过滤")
    run_action(crud.list_milestones, project_id)


def create_milestone() -> None:
    payload = crud.MilestoneCreate(
        project_id=prompt_text("项目 ID"),
        name=prompt_text("里程碑名称"),
        description=prompt_optional("描述"),
        message=prompt_optional("说明消息"),
        milestone_type=prompt_text("里程碑类型", "regular") or "regular",
        is_baseline=prompt_bool("是否为基线", default=False),
        sprint=prompt_optional("Sprint"),
        version=prompt_optional("版本"),
        created_by=prompt_optional("创建人"),
    )
    run_action(crud.create_milestone, payload)


def update_milestone() -> None:
    milestone_id = prompt_text("里程碑 ID")
    payload = crud.MilestoneUpdate(
        name=prompt_update_value("里程碑名称"),
        description=prompt_update_value("描述"),
        message=prompt_update_value("说明消息"),
        milestone_type=prompt_update_value("里程碑类型"),
        is_baseline=prompt_optional_bool("是否为基线"),
        sprint=prompt_update_value("Sprint"),
        version=prompt_update_value("版本"),
    )
    run_action(crud.update_milestone, milestone_id, payload)


def delete_milestone() -> None:
    milestone_id = prompt_text("里程碑 ID")
    if prompt_bool(f"确认删除里程碑 {milestone_id}", default=False):
        run_action(crud.delete_milestone, milestone_id)


def show_project_statistics() -> None:
    run_action(statistics.list_project_statistics)


def show_requirement_details() -> None:
    project_id = prompt_optional("项目 ID 过滤")
    run_action(statistics.list_requirement_details, project_id)


def show_requirement_trace() -> None:
    project_id = prompt_text("项目 ID")
    run_action(statistics.get_requirement_trace, project_id)


def show_project_progress() -> None:
    project_id = prompt_text("项目 ID")
    run_action(statistics.get_project_progress, project_id)


def show_milestone_delivery_risk() -> None:
    project_id = prompt_text("项目 ID")
    run_action(statistics.get_milestone_delivery_risk, project_id)


def entity_menu(title: str, actions: list[tuple[str, Callable[[], None]]]) -> None:
    while True:
        print_header(title)
        for index, (label, _) in enumerate(actions, start=1):
            print(f"{index}. {label}")
        print("0. 返回上一级")
        choice = input("请选择操作: ").strip()
        if choice == "0":
            return
        if not choice.isdigit():
            print("请输入数字菜单项。")
            continue
        index = int(choice) - 1
        if 0 <= index < len(actions):
            if ensure_connection():
                actions[index][1]()
        else:
            print("菜单项不存在。")


def main() -> None:
    print_header("数据库实验演示命令行菜单")
    print("本菜单直接连接 PostgreSQL，不依赖先启动 FastAPI 服务。")
    connect_with_defaults()

    while True:
        status = "已连接" if db.is_connected else "未连接"
        print_header(f"主菜单（数据库状态：{status}）")
        print("1. 产品管理")
        print("2. 项目管理")
        print("3. 需求管理")
        print("4. 缺陷管理")
        print("5. 测试用例管理")
        print("6. 里程碑管理")
        print("7. 统计与复杂查询")
        print("8. 重新连接数据库")
        print("9. 断开数据库连接")
        print("0. 退出")
        choice = input("请选择菜单项: ").strip()

        if choice == "1":
            entity_menu(
                "产品管理",
                [
                    ("查询产品列表", list_products),
                    ("新增产品", create_product),
                    ("修改产品", update_product),
                    ("删除产品", delete_product),
                ],
            )
        elif choice == "2":
            entity_menu(
                "项目管理",
                [
                    ("查询项目列表", list_projects),
                    ("新增项目", create_project),
                    ("修改项目", update_project),
                    ("删除项目", delete_project),
                ],
            )
        elif choice == "3":
            entity_menu(
                "需求管理",
                [
                    ("查询需求列表", list_requirements),
                    ("新增需求", create_requirement),
                    ("修改需求", update_requirement),
                    ("删除需求", delete_requirement),
                ],
            )
        elif choice == "4":
            entity_menu(
                "缺陷管理",
                [
                    ("查询缺陷列表", list_defects),
                    ("新增缺陷", create_defect),
                    ("修改缺陷", update_defect),
                    ("删除缺陷", delete_defect),
                ],
            )
        elif choice == "5":
            entity_menu(
                "测试用例管理",
                [
                    ("查询测试用例列表", list_test_cases),
                    ("新增测试用例", create_test_case),
                    ("修改测试用例", update_test_case),
                    ("删除测试用例", delete_test_case),
                ],
            )
        elif choice == "6":
            entity_menu(
                "里程碑管理",
                [
                    ("查询里程碑列表", list_milestones),
                    ("新增里程碑", create_milestone),
                    ("修改里程碑", update_milestone),
                    ("删除里程碑", delete_milestone),
                ],
            )
        elif choice == "7":
            entity_menu(
                "统计与复杂查询",
                [
                    ("项目统计视图", show_project_statistics),
                    ("需求明细视图", show_requirement_details),
                    ("需求追溯复杂查询", show_requirement_trace),
                    ("项目进度复杂查询", show_project_progress),
                    ("里程碑交付风险查询", show_milestone_delivery_risk),
                ],
            )
        elif choice == "8":
            reconnect_database()
        elif choice == "9":
            db.disconnect()
            print("数据库连接已断开。")
        elif choice == "0":
            if db.is_connected:
                db.disconnect()
            print("已退出演示菜单。")
            return
        else:
            print("菜单项不存在。")


if __name__ == "__main__":
    main()
