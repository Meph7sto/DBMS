import unittest
from unittest import mock

import schema_bootstrap


class SchemaBootstrapTests(unittest.TestCase):
    def test_bootstraps_empty_database_and_applies_patch(self) -> None:
        conn = mock.Mock()

        with mock.patch(
            "schema_bootstrap._required_table_state",
            side_effect=[
                {
                    "manage_products": False,
                    "manage_projects": False,
                    "manage_comments": False,
                },
                {
                    "manage_products": True,
                    "manage_projects": True,
                    "manage_comments": True,
                },
                {
                    "manage_products": True,
                    "manage_projects": True,
                    "manage_comments": True,
                },
            ],
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
                {
                    "manage_products": True,
                    "manage_projects": True,
                    "manage_comments": False,
                },
                {
                    "manage_products": True,
                    "manage_projects": True,
                    "manage_comments": True,
                },
                {
                    "manage_products": True,
                    "manage_projects": True,
                    "manage_comments": True,
                },
            ],
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
        mocked_execute_file.assert_not_called()

    def test_rejects_unrecoverable_partial_schema_with_clear_error(self) -> None:
        conn = mock.Mock()

        with mock.patch(
            "schema_bootstrap._required_table_state",
            return_value={
                "manage_products": True,
                "manage_projects": False,
                "manage_comments": False,
            },
        ):
            with self.assertRaises(RuntimeError) as ctx:
                schema_bootstrap.ensure_requirements_schema(conn)

        self.assertIn("manage_projects", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
