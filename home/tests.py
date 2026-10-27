from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from blog.models import Category, Post
from projects.models import Project, ProjectCategory
from .models import Notice, Service, TeamMember


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


class NoticeOrderingTests(TestCase):
    def assert_order(self, titles):
        self.assertEqual(
            list(Notice.objects.values_list("title", "order")),
            [(title, position) for position, title in enumerate(titles, start=1)],
        )

    def test_insert_move_append_and_delete_use_one_global_priority_list(self):
        first = Notice.objects.create(title="First", is_important=True)
        hidden = Notice.objects.create(title="Hidden", is_active=False)
        Notice.objects.create(title="Last", order=99)
        inserted = Notice.objects.create(title="Inserted", order=2)
        self.assertEqual(first.order, 1)
        self.assert_order(["First", "Inserted", "Hidden", "Last"])

        inserted.order = 1
        inserted.save(update_fields=["order"])
        self.assert_order(["Inserted", "First", "Hidden", "Last"])

        inserted.order = 0
        inserted.save()
        self.assert_order(["First", "Hidden", "Last", "Inserted"])

        hidden.delete()
        self.assert_order(["First", "Last", "Inserted"])

        Notice.objects.filter(title__in=["First", "Last"]).delete()
        self.assert_order(["Inserted"])

    def test_content_save_preserves_priority_shift_from_another_notice(self):
        Notice.objects.create(title="First")
        Notice.objects.create(title="Second")
        second = Notice.objects.get(title="Second")
        Notice.objects.create(title="Inserted", order=1)

        second.body = "Updated announcement"
        second.is_important = True
        second.save()

        self.assert_order(["Inserted", "First", "Second"])
        second.refresh_from_db()
        self.assertEqual(second.body, "Updated announcement")
        self.assertTrue(second.is_important)
        self.assertEqual(second.order, 3)

    def test_update_fields_without_order_preserves_position(self):
        Notice.objects.create(title="First")
        second = Notice.objects.create(title="Second")
        second.order = 1
        second.body = "Updated announcement"

        second.save(update_fields=["body"])

        self.assert_order(["First", "Second"])
        second.refresh_from_db()
        self.assertEqual(second.body, "Updated announcement")


@override_settings(SECURE_SSL_REDIRECT=False)
class NoticePriorityViewTests(TestCase):
    def test_popup_and_notice_list_render_priority_before_creation_date(self):
        hidden = Notice.objects.create(
            title="Hidden announcement", is_active=False, is_important=True
        )
        older = Notice.objects.create(title="Older urgent announcement", is_important=True)
        ordinary = Notice.objects.create(title="Ordinary announcement")
        newer = Notice.objects.create(title="Newer routine announcement", is_important=True)
        for notice, day in [(hidden, 4), (older, 1), (ordinary, 3), (newer, 2)]:
            Notice.objects.filter(pk=notice.pk).update(
                created_at=datetime(2026, 1, day, tzinfo=timezone.utc)
            )

        for url_name, expected in [
            ("home", [older, newer]),
            ("notices", [older, ordinary, newer]),
        ]:
            with self.subTest(page=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(list(response.context["notices"]), expected)
                html = response.content.decode()
                positions = [html.index(notice.title) for notice in expected]
                self.assertEqual(positions, sorted(positions))
                self.assertNotContains(response, hidden.title)
                if url_name == "home":
                    self.assertNotContains(response, ordinary.title)

    def test_equal_priorities_use_newest_date_then_newest_id(self):
        older = Notice.objects.create(title="Older tied priority", is_important=True)
        newer = Notice.objects.create(title="Newer tied priority", is_important=True)
        newest_id = Notice.objects.create(title="Newest id tied priority", is_important=True)
        for notice, day in [(older, 1), (newer, 2), (newest_id, 2)]:
            # Bulk updates represent tied priorities already present in the DB.
            Notice.objects.filter(pk=notice.pk).update(
                order=1, created_at=datetime(2026, 1, day, tzinfo=timezone.utc)
            )

        self.assertEqual(list(Notice.objects.all()), [newest_id, newer, older])
        for url_name in ["home", "notices"]:
            with self.subTest(page=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(
                    list(response.context["notices"]), [newest_id, newer, older]
                )


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

    def test_notice_list_editable_moves_rows_loaded_before_sibling_shifts(self):
        for title in ["First", "Second", "Third", "Fourth"]:
            Notice.objects.create(title=title)
        url = reverse("admin:home_notice_changelist")
        response = self.client.get(url)
        formset = response.context["cl"].formset
        self.assertEqual(
            [form.instance.title for form in formset.forms],
            ["First", "Second", "Third", "Fourth"],
        )
        data = {
            "_save": "Save",
            "form-TOTAL_FORMS": str(len(formset.forms)),
            "form-INITIAL_FORMS": str(len(formset.forms)),
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        }
        positions = {"First": 4, "Second": 3, "Third": 3, "Fourth": 4}
        for index, form in enumerate(formset.forms):
            notice = form.instance
            data[f"form-{index}-id"] = str(notice.pk)
            data[f"form-{index}-order"] = str(positions[notice.title])

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            list(Notice.objects.values_list("title", "order")),
            [("Third", 1), ("Fourth", 2), ("Second", 3), ("First", 4)],
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


class NoticeOrderingMigrationTests(TransactionTestCase):
    migrate_from = [("home", "0018_notice_home_notice_is_acti_7bfa2e_idx_and_more")]
    migrate_to = [("home", "0019_notice_order")]

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        self.old_apps = executor.loader.project_state(self.migrate_from).apps
        self.old_apps.get_model("home", "Notice").objects.all().delete()

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_existing_notice_priority_preserves_newest_first_order_and_uploads(self):
        old_notice = self.old_apps.get_model("home", "Notice")
        for title, day, active, important in [
            ("Older urgent", 1, True, True),
            ("Newer ordinary", 2, True, False),
            ("Newest id tied", 2, True, True),
            ("Newest hidden", 3, False, True),
        ]:
            notice = old_notice.objects.create(
                title=title,
                body=f"Body for {title}",
                image=f"notices/{day}.png",
                pdf_file=f"notices/pdfs/{day}.pdf",
                is_active=active,
                is_important=important,
            )
            old_notice.objects.filter(pk=notice.pk).update(
                created_at=datetime(2026, 1, day, tzinfo=timezone.utc)
            )
        fields = ["pk", "title", "body", "image", "pdf_file", "is_active", "is_important", "created_at"]
        expected = list(old_notice.objects.order_by("-created_at", "-pk").values_list(*fields))

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        new_notice = executor.loader.project_state(self.migrate_to).apps.get_model("home", "Notice")

        self.assertEqual(
            list(new_notice.objects.values_list(*fields, "order")),
            [(*row, position) for position, row in enumerate(expected, start=1)],
        )


@override_settings(SITE_URL="https://example.test", SECURE_SSL_REDIRECT=False)
class SeoEndpointTests(TestCase):
    def test_page_metadata_has_description_and_canonical_url(self):
        response = self.client.get(reverse("about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<meta name="description"')
        self.assertContains(
            response,
            '<link rel="canonical" href="https://example.test/about/"',
        )
        self.assertContains(response, '<meta property="og:title"')
        self.assertContains(response, '<meta name="twitter:card"')

    def test_detail_pages_use_content_for_metadata(self):
        category = Category.objects.create(name="Research", slug="research")
        post = Post.objects.create(
            category=category,
            title="Risk insight",
            slug="risk-insight",
            excerpt="A useful article summary.",
            body="Full article content.",
        )
        project_category = ProjectCategory.objects.create(
            name="Advisory", slug="advisory"
        )
        project = Project.objects.create(
            category=project_category,
            title="Risk review",
            slug="risk-review",
            summary="A useful project summary.",
        )

        post_response = self.client.get(reverse("blog_detail", args=[post.slug]))
        project_response = self.client.get(
            reverse("project_detail", args=[project.slug])
        )

        self.assertContains(post_response, "Risk insight — Pivot Risk")
        self.assertContains(post_response, "A useful article summary.")
        self.assertContains(project_response, "Risk review — Pivot Risk")
        self.assertContains(project_response, "A useful project summary.")

    def test_sitemap_lists_public_content_only(self):
        category = Category.objects.create(name="Research", slug="research")
        Post.objects.create(
            category=category,
            title="Published insight",
            slug="published-insight",
            body="Published",
            is_published=True,
        )
        Post.objects.create(
            category=category,
            title="Draft insight",
            slug="draft-insight",
            body="Draft",
            is_published=False,
        )
        project_category = ProjectCategory.objects.create(
            name="Advisory", slug="advisory"
        )
        Project.objects.create(
            category=project_category,
            title="Listed project",
            slug="listed-project",
        )

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertIn(
            "https://example.test/blog/published-insight/",
            content,
        )
        self.assertIn("https://example.test/projects/listed-project/", content)
        self.assertNotIn("draft-insight", content)

    def test_robots_points_crawlers_to_sitemap(self):
        response = self.client.get(reverse("robots"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertContains(response, "Disallow: /admin/")
        self.assertContains(response, "Sitemap: https://example.test/sitemap.xml")
