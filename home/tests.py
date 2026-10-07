from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from .models import Service, TeamMember


class OrderingTestsMixin:
    def setUp(self):
        # Data migrations seed these models, so each test starts with empty lists.
        self.model.objects.all().delete()

    def create_item(self, name, order=0, scope=None):
        return self.model.objects.create(
            **{
                self.name_field: name,
                self.scope_field: self.initial_scope if scope is None else scope,
                "order": order,
            }
        )

    def assert_order(self, names, scope=None):
        scope = self.initial_scope if scope is None else scope
        items = self.model.objects.filter(**{self.scope_field: scope})
        self.assertEqual(
            list(items.values_list(self.name_field, "order")),
            [(name, index) for index, name in enumerate(names, start=1)],
        )

    def test_inserting_second_shifts_all_following_items(self):
        for index in range(1, 6):
            self.create_item(f"Item {index}", order=index)

        self.create_item("Inserted", order=2)

        self.assert_order(
            ["Item 1", "Inserted", "Item 2", "Item 3", "Item 4", "Item 5"]
        )

    def test_zero_and_out_of_range_positions_append(self):
        first = self.create_item("First")
        self.create_item("Second", order=99)
        self.create_item("Third")
        self.assertEqual(first.order, 1)
        self.assert_order(["First", "Second", "Third"])

    def test_moving_up_shifts_intervening_items_down(self):
        for index in range(1, 5):
            self.create_item(f"Item {index}", order=index)
        last = self.model.objects.get(**{self.name_field: "Item 4"})

        last.order = 2
        last.save()

        self.assert_order(["Item 1", "Item 4", "Item 2", "Item 3"])

    def test_moving_down_shifts_intervening_items_up(self):
        for index in range(1, 5):
            self.create_item(f"Item {index}", order=index)
        first = self.model.objects.get(**{self.name_field: "Item 1"})

        first.order = 3
        first.save(update_fields=["order"])

        self.assert_order(["Item 2", "Item 3", "Item 1", "Item 4"])

    def test_insertion_keeps_other_scope_unchanged(self):
        self.create_item("First", order=1)
        self.create_item("Second", order=2)
        self.create_item("Other first", order=1, scope=self.other_scope)
        self.create_item("Other second", order=2, scope=self.other_scope)

        self.create_item("Inserted", order=1)

        self.assert_order(["Inserted", "First", "Second"])
        self.assert_order(["Other first", "Other second"], scope=self.other_scope)

    def test_changing_scope_closes_old_gap_and_inserts_in_new_list(self):
        self.create_item("First", order=1)
        self.create_item("Moving", order=2)
        self.create_item("Third", order=3)
        self.create_item("Other first", order=1, scope=self.other_scope)
        self.create_item("Other second", order=2, scope=self.other_scope)
        moving = self.model.objects.get(**{self.name_field: "Moving"})

        setattr(moving, self.scope_field, self.other_scope)
        moving.save()

        self.assert_order(["First", "Third"])
        self.assert_order(
            ["Other first", "Moving", "Other second"], scope=self.other_scope
        )

    def test_content_save_does_not_restore_stale_order(self):
        self.create_item("First", order=1)
        self.create_item("Second", order=2)
        second = self.model.objects.get(**{self.name_field: "Second"})
        self.create_item("Inserted", order=1)

        setattr(second, self.text_field, "Updated content")
        second.save()

        self.assert_order(["Inserted", "First", "Second"])
        second.refresh_from_db()
        self.assertEqual(getattr(second, self.text_field), "Updated content")
        self.assertEqual(second.order, 3)

    def test_update_fields_excluding_order_and_scope_does_not_reorder(self):
        self.create_item("First", order=1)
        self.create_item("Second", order=2)
        second = self.model.objects.get(**{self.name_field: "Second"})
        second.order = 1
        setattr(second, self.scope_field, self.other_scope)
        setattr(second, self.text_field, "Updated content")

        second.save(update_fields=[self.text_field])

        self.assert_order(["First", "Second"])
        self.assert_order([], scope=self.other_scope)
        second.refresh_from_db()
        self.assertEqual(getattr(second, self.text_field), "Updated content")

    def test_deleting_middle_closes_gap(self):
        self.create_item("First", order=1)
        self.create_item("Second", order=2)
        self.create_item("Third", order=3)

        self.model.objects.get(**{self.name_field: "Second"}).delete()

        self.assert_order(["First", "Third"])

    def test_deleting_stale_instance_compacts_its_current_section(self):
        self.create_item("First")
        stale = self.create_item("Moving")
        self.create_item("Third")
        self.create_item("Other first", scope=self.other_scope)
        self.create_item("Other second", scope=self.other_scope)
        moving = self.model.objects.get(pk=stale.pk)
        setattr(moving, self.scope_field, self.other_scope)
        moving.save()

        stale.delete()

        self.assert_order(["First", "Third"])
        self.assert_order(["Other first", "Other second"], scope=self.other_scope)

    def test_queryset_deletion_closes_multiple_gaps(self):
        for index in range(1, 6):
            self.create_item(f"Item {index}", order=index)
        self.create_item("Other", order=1, scope=self.other_scope)

        self.model.objects.filter(order__in=[2, 4]).delete()

        self.assert_order(["Item 1", "Item 3", "Item 5"])
        self.assert_order(["Other"], scope=self.other_scope)


class ServiceOrderingTests(OrderingTestsMixin, TestCase):
    model = Service
    name_field = "title"
    scope_field = "is_primary"
    text_field = "summary"
    initial_scope = True
    other_scope = False


class TeamMemberOrderingTests(OrderingTestsMixin, TestCase):
    model = TeamMember
    name_field = "name"
    scope_field = "group"
    text_field = "role"
    initial_scope = "members"
    other_scope = "leadership"


@override_settings(SECURE_SSL_REDIRECT=False)
class OrderingAdminTests(TestCase):
    def setUp(self):
        Service.objects.all().delete()
        TeamMember.objects.all().delete()
        user = get_user_model().objects.create_superuser(
            username="ordering-admin", email="admin@example.com", password="test-password"
        )
        self.client.force_login(user)

    def test_service_admin_add_inserts_at_requested_position(self):
        Service.objects.create(title="First", order=1)
        Service.objects.create(title="Second", order=2)

        response = self.client.post(
            reverse("admin:home_service_add"),
            {"title": "Inserted", "order": "2", "is_primary": "on", "_save": "Save"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            list(Service.objects.values_list("title", "order")),
            [("First", 1), ("Inserted", 2), ("Second", 3)],
        )

    def test_team_admin_change_moves_member(self):
        TeamMember.objects.create(name="First", order=1)
        second = TeamMember.objects.create(name="Second", order=2)
        TeamMember.objects.create(name="Third", order=3)

        response = self.client.post(
            reverse("admin:home_teammember_change", args=[second.pk]),
            {"name": "Second", "group": "members", "order": "1", "_save": "Save"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            list(TeamMember.objects.values_list("name", "order")),
            [("Second", 1), ("First", 2), ("Third", 3)],
        )

    def test_service_list_editable_combines_moves_and_category_changes(self):
        Service.objects.create(title="First", order=1)
        Service.objects.create(title="Second", order=2)
        Service.objects.create(title="Third", order=3)
        Service.objects.create(title="Other first", order=1, is_primary=False)
        Service.objects.create(title="Other second", order=2, is_primary=False)
        url = reverse("admin:home_service_changelist")
        response = self.client.get(url)
        formset = response.context["cl"].formset
        data = {
            "_save": "Save",
            "form-TOTAL_FORMS": str(len(formset.forms)),
            "form-INITIAL_FORMS": str(len(formset.forms)),
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        }
        for index, form in enumerate(formset.forms):
            service = form.instance
            prefix = f"form-{index}"
            data[f"{prefix}-id"] = str(service.pk)
            data[f"{prefix}-order"] = "2" if service.title == "First" else str(service.order)
            if service.is_primary and service.title != "Second":
                data[f"{prefix}-is_primary"] = "on"

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            list(Service.objects.filter(is_primary=True).values_list("title", "order")),
            [("First", 1), ("Third", 2)],
        )
        self.assertEqual(
            list(Service.objects.filter(is_primary=False).values_list("title", "order")),
            [("Other first", 1), ("Second", 2), ("Other second", 3)],
        )


class OrderingMigrationTests(TransactionTestCase):
    migrate_from = [
        ("home", "0016_notice_image_notice_pdf_file"),
        ("projects", "0003_project_order"),
    ]
    migrate_to = [
        ("home", "0017_automatic_ordering"),
        ("projects", "0004_automatic_ordering"),
    ]

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        self.old_apps = executor.loader.project_state(self.migrate_from).apps
        # Historical models bypass today's automatic ordering when creating
        # legacy duplicates and gaps, as they would exist before this migration.
        for app_label, model_name in [
            ("home", "Service"),
            ("home", "TeamMember"),
            ("projects", "Project"),
        ]:
            self.old_apps.get_model(app_label, model_name).objects.all().delete()

    def tearDown(self):
        # Other tests must always see the current schema, including after failure.
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_normalization_preserves_relative_order_in_every_section(self):
        fixtures = [
            ("home", "Service", "title", "is_primary", [False, True]),
            ("home", "TeamMember", "name", "group", ["leadership", "members"]),
        ]
        expected = []
        for app_label, model_name, name_field, scope_field, scopes in fixtures:
            model = self.old_apps.get_model(app_label, model_name)
            for scope in scopes:
                for name, position in [("Zero", 0), ("Zulu", 4), ("Alpha", 4), ("Tail", 20)]:
                    model.objects.create(
                        **{name_field: name, scope_field: scope, "order": position}
                    )
                queryset = model.objects.filter(**{scope_field: scope})
                self.assertEqual(
                    list(queryset.values_list(name_field, flat=True)),
                    ["Zero", "Alpha", "Zulu", "Tail"],
                )
                expected.append(
                    (app_label, model_name, scope_field, scope, list(queryset.values_list("pk", flat=True)))
                )

        category_model = self.old_apps.get_model("projects", "ProjectCategory")
        category = category_model.objects.create(name="Migration category", slug="migration-category")
        project_model = self.old_apps.get_model("projects", "Project")
        for is_featured in [False, True]:
            for index, (title, position, day) in enumerate(
                [("Zero", 0, 1), ("Older tied", 8, 1), ("Newer tied", 8, 2),
                 ("Newest id tied", 8, 2), ("Tail", 20, 3)]
            ):
                project = project_model.objects.create(
                    title=title,
                    slug=f"migration-{is_featured}-{index}",
                    category=category,
                    order=position,
                    is_featured=is_featured,
                )
                project_model.objects.filter(pk=project.pk).update(
                    created_at=datetime(2026, 1, day, tzinfo=timezone.utc)
                )
            queryset = project_model.objects.filter(is_featured=is_featured)
            self.assertEqual(
                list(queryset.values_list("title", flat=True)),
                ["Zero", "Newest id tied", "Newer tied", "Older tied", "Tail"],
            )
            expected.append(
                ("projects", "Project", "is_featured", is_featured,
                 list(queryset.values_list("pk", flat=True)))
            )

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        new_apps = executor.loader.project_state(self.migrate_to).apps

        for app_label, model_name, scope_field, scope, original_ids in expected:
            with self.subTest(model=model_name, scope=scope):
                model = new_apps.get_model(app_label, model_name)
                positions = model.objects.filter(**{scope_field: scope}).values_list("pk", "order")
                self.assertEqual(
                    list(positions),
                    [(pk, position) for position, pk in enumerate(original_ids, start=1)],
                )
