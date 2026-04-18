import unittest
from unittest import mock

import schema_bootstrap


def make_table_state(**overrides):
    state = {name: True for name in schema_bootstrap.REQUIRED_TABLES}
    state.update(overrides)
    return state


class SchemaBootstrapTests(unittest.TestCase):
    def test_bootstraps_empty_database_and_applies_patch(self) -> None:
        conn = mock.Mock()

        with mock.patch(
            "schema_bootstrap._required_table_state",
            side_effect=[
                make_table_state(manage_products=False),
                make_table_state(),
                make_table_state(),
            ],
        ):
            with mock.patch(
                "schema_bootstrap._required_function_state",
                return_value={"fn_milestone_delivery_risk": True},
            ):
                with mock.patch("schema_bootstrap._execute_sql_file") as mocked_execute:
                    info = schema_bootstrap.ensure_requirements_schema(conn)

        self.assertTrue(info["schema_applied"])
        self.assertTrue(info["patch_applied"])
        self.assertEqual(mocked_execute.call_count, 2)
        self.assertEqual(mocked_execute.call_args_list[0].args[1], schema_bootstrap.SCHEMA_SQL_FILE)
        self.assertEqual(mocked_execute.call_args_list[1].args[1], schema_bootstrap.SCHEMA_PATCH_FILE)

    def test_repairs_missing_comments_table_and_applies_patch(self) -> None:
        conn = mock.Mock()

        with mock.patch(
            "schema_bootstrap._required_table_state",
            side_effect=[
                make_table_state(manage_comments=False),
                make_table_state(),
                make_table_state(),
            ],
        ):
            with mock.patch(
                "schema_bootstrap._required_function_state",
                return_value={"fn_milestone_delivery_risk": True},
            ):
                with mock.patch("schema_bootstrap._execute_sql_text") as mocked_execute_text:
                    with mock.patch("schema_bootstrap._execute_sql_file") as mocked_execute_file:
                        info = schema_bootstrap.ensure_requirements_schema(conn)

        self.assertTrue(info["schema_applied"])
        self.assertTrue(info["patch_applied"])
        self.assertEqual(mocked_execute_text.call_count, 2)
        self.assertEqual(mocked_execute_text.call_args_list[0].args[1], schema_bootstrap.COMMENTS_REPAIR_SQL)
        self.assertEqual(
            mocked_execute_text.call_args_list[1].args[1],
            schema_bootstrap.COMMENTS_TRIGGER_PATCH_SQL,
        )
        mocked_execute_file.assert_called_once_with(
            conn,
            schema_bootstrap.SCHEMA_PATCH_FILE,
            "schema 约束补丁",
        )

    def test_repairs_missing_partial_tables_and_applies_patch(self) -> None:
        conn = mock.Mock()

        with mock.patch(
            "schema_bootstrap._required_table_state",
            side_effect=[
                make_table_state(
                    manage_project_members=False,
                    manage_requirement_links=False,
                ),
                make_table_state(),
                make_table_state(),
            ],
        ):
            with mock.patch(
                "schema_bootstrap._required_function_state",
                return_value={"fn_milestone_delivery_risk": True},
            ):
                with mock.patch("schema_bootstrap._execute_sql_text") as mocked_execute_text:
                    with mock.patch("schema_bootstrap._execute_sql_file") as mocked_execute_file:
                        info = schema_bootstrap.ensure_requirements_schema(conn)

        self.assertTrue(info["schema_applied"])
        self.assertTrue(info["patch_applied"])
        mocked_execute_text.assert_called_once_with(
            conn,
            schema_bootstrap.PARTIAL_SCHEMA_REPAIR_SQL,
        )
        mocked_execute_file.assert_called_once_with(
            conn,
            schema_bootstrap.SCHEMA_PATCH_FILE,
            "schema 约束补丁",
        )

    def test_rejects_unrecoverable_partial_schema_with_clear_error(self) -> None:
        conn = mock.Mock()

        with mock.patch(
            "schema_bootstrap._required_table_state",
            return_value=make_table_state(
                manage_projects=False,
                manage_project_members=False,
                manage_comments=False,
            ),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                schema_bootstrap.ensure_requirements_schema(conn)

        self.assertIn("manage_projects", str(ctx.exception))

    def test_applies_patch_when_runtime_function_is_missing(self) -> None:
        conn = mock.Mock()

        with mock.patch(
            "schema_bootstrap._required_table_state",
            return_value=make_table_state(),
        ):
            with mock.patch(
                "schema_bootstrap._required_function_state",
                side_effect=[
                    {"fn_milestone_delivery_risk": False},
                    {"fn_milestone_delivery_risk": True},
                ],
            ):
                with mock.patch("schema_bootstrap._execute_sql_file") as mocked_execute_file:
                    info = schema_bootstrap.ensure_requirements_schema(conn)

        self.assertFalse(info["schema_applied"])
        self.assertTrue(info["patch_applied"])
        mocked_execute_file.assert_called_once_with(
            conn,
            schema_bootstrap.SCHEMA_PATCH_FILE,
            "schema 约束补丁",
        )


if __name__ == "__main__":
    unittest.main()
