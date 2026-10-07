from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import IntegrityError, close_old_connections, connection, connections, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from .models import Project, ProjectCategory


class ProjectFixtures:
    def setUp(self):
        super().setUp()
        self.category = ProjectCategory.objects.create(name="Research", slug="research")

    def create_project(self, title, **kwargs):
        return Project.objects.create(
            title=title,
            slug=title.lower().replace(" ", "-"),
            category=self.category,
            **kwargs,
        )

    def assert_sequence(self, titles, *, featured=False):
        self.assertEqual(
            list(
                Project.objects.filter(is_featured=featured).values_list("title", "order")
            ),
            [(title, position) for position, title in enumerate(titles, start=1)],
        )

    def seed_projects(self):
        return [self.create_project(title) for title in ("Alpha", "Bravo", "Charlie", "Delta", "Echo")]


@override_settings(SECURE_SSL_REDIRECT=False)
class ProjectOrderingTests(ProjectFixtures, TestCase):
    def test_insert_at_second_position_shifts_every_following_project(self):
        self.seed_projects()
        self.create_project("Inserted", order=2)

        self.assert_sequence(["Alpha", "Inserted", "Bravo", "Charlie", "Delta", "Echo"])

    def test_default_and_out_of_range_positions_append(self):
        self.create_project("Alpha")
        self.create_project("Bravo", order=100)
        self.create_project("Charlie", order=0)

        self.assert_sequence(["Alpha", "Bravo", "Charlie"])

    def test_existing_projects_can_move_up_and_down(self):
        alpha, bravo, charlie, delta, echo = self.seed_projects()
        echo.order = 2
        echo.save()
        self.assert_sequence(["Alpha", "Echo", "Bravo", "Charlie", "Delta"])

        alpha.order = 4
        alpha.save()
        self.assert_sequence(["Echo", "Bravo", "Charlie", "Alpha", "Delta"])

    def test_zero_or_out_of_range_move_appends(self):
        alpha, bravo, charlie, delta, echo = self.seed_projects()
        alpha.order = 0
        alpha.save()
        self.assert_sequence(["Bravo", "Charlie", "Delta", "Echo", "Alpha"])

        bravo.refresh_from_db()
        bravo.order = 100
        bravo.save()
        self.assert_sequence(["Charlie", "Delta", "Echo", "Alpha", "Bravo"])

    def test_saving_same_position_does_not_move_other_projects(self):
        self.seed_projects()
        project = Project.objects.get(title="Charlie")
        project.summary = "Updated description"
        project.save()

        self.assert_sequence(["Alpha", "Bravo", "Charlie", "Delta", "Echo"])

    def test_saving_stale_project_preserves_position_shifted_by_another_save(self):
        self.seed_projects()
        stale = Project.objects.get(title="Bravo")
        self.create_project("Inserted", order=2)

        stale.summary = "Edited after another project was inserted"
        stale.save()

        self.assert_sequence(["Alpha", "Inserted", "Bravo", "Charlie", "Delta", "Echo"])
        stale.refresh_from_db()
        self.assertEqual(stale.summary, "Edited after another project was inserted")

    def test_explicit_order_change_on_stale_instance_still_moves_project(self):
        self.seed_projects()
        stale = Project.objects.get(title="Bravo")
        self.create_project("Inserted", order=2)

        stale.order = 5
        stale.save()

        self.assert_sequence(["Alpha", "Inserted", "Charlie", "Delta", "Bravo", "Echo"])

    def test_save_with_update_fields_without_order_preserves_shifted_position(self):
        self.seed_projects()
        stale = Project.objects.get(title="Bravo")
        self.create_project("Inserted", order=2)

        stale.summary = "Updated only this field"
        stale.save(update_fields=["summary"])

        self.assert_sequence(["Alpha", "Inserted", "Bravo", "Charlie", "Delta", "Echo"])

    def test_deferred_order_and_section_fields_can_be_saved_after_a_shift(self):
        self.seed_projects()
        project = Project.objects.only("pk", "title", "summary").get(title="Bravo")
        self.assertTrue({"order", "is_featured"}.issubset(project.get_deferred_fields()))
        self.create_project("Inserted", order=2)

        project.summary = "Updated from a partially loaded project"
        project.save()

        self.assert_sequence(["Alpha", "Inserted", "Bravo", "Charlie", "Delta", "Echo"])
        project.refresh_from_db()
        self.assertEqual(project.summary, "Updated from a partially loaded project")

    def test_failed_insertion_rolls_back_neighbor_positions(self):
        self.seed_projects()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Project.objects.create(
                    title="Duplicate slug", slug="alpha", category=self.category, order=2
                )

        self.assert_sequence(["Alpha", "Bravo", "Charlie", "Delta", "Echo"])
        self.assertEqual(Project.objects.count(), 5)

    def test_featured_and_other_projects_have_independent_sequences(self):
        self.seed_projects()
        self.create_project("Featured one", is_featured=True)
        self.create_project("Featured two", is_featured=True)
        self.create_project("Featured inserted", is_featured=True, order=2)

        self.assert_sequence(["Alpha", "Bravo", "Charlie", "Delta", "Echo"])
        self.assert_sequence(["Featured one", "Featured inserted", "Featured two"], featured=True)

    def test_switching_sections_closes_source_gap_and_inserts_into_destination(self):
        self.seed_projects()
        self.create_project("Featured one", is_featured=True)
        self.create_project("Featured two", is_featured=True)
        project = Project.objects.get(title="Charlie")
        project.is_featured = True
        project.order = 2
        project.save()

        self.assert_sequence(["Alpha", "Bravo", "Delta", "Echo"])
        self.assert_sequence(["Featured one", "Charlie", "Featured two"], featured=True)

        project.is_featured = False
        project.order = 0
        project.save()
        self.assert_sequence(["Alpha", "Bravo", "Delta", "Echo", "Charlie"])
        self.assert_sequence(["Featured one", "Featured two"], featured=True)

    def test_scope_only_update_fields_persists_clamped_destination_order(self):
        self.seed_projects()
        self.create_project("Featured one", is_featured=True)
        self.create_project("Featured two", is_featured=True)
        project = Project.objects.get(title="Echo")

        project.is_featured = True
        project.save(update_fields=["is_featured"])

        self.assert_sequence(["Alpha", "Bravo", "Charlie", "Delta"])
        self.assert_sequence(["Featured one", "Featured two", "Echo"], featured=True)
        project.refresh_from_db()
        self.assertEqual(project.order, 3)

    def test_individual_deletion_closes_gap(self):
        self.seed_projects()
        Project.objects.get(title="Charlie").delete()

        self.assert_sequence(["Alpha", "Bravo", "Delta", "Echo"])

    def test_queryset_deletion_closes_all_gaps_and_preserves_other_section(self):
        self.seed_projects()
        self.create_project("Featured one", is_featured=True)
        self.create_project("Featured two", is_featured=True)
        Project.objects.filter(title__in=["Bravo", "Delta"]).delete()

        self.assert_sequence(["Alpha", "Charlie", "Echo"])
        self.assert_sequence(["Featured one", "Featured two"], featured=True)

    def test_project_page_renders_each_section_in_its_updated_order(self):
        self.create_project("Other first")
        self.create_project("Other second")
        self.create_project("Other inserted", order=2)
        self.create_project("Featured first", is_featured=True)
        self.create_project("Featured second", is_featured=True)
        self.create_project("Featured inserted", is_featured=True, order=1)

        response = self.client.get(reverse("project_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["featured_projects"].values_list("title", flat=True)),
            ["Featured inserted", "Featured first", "Featured second"],
        )
        self.assertEqual(
            list(response.context["other_projects"].values_list("title", flat=True)),
            ["Other first", "Other inserted", "Other second"],
        )
        html = response.content.decode()
        expected_titles = [
            "Featured inserted", "Featured first", "Featured second",
            "Other first", "Other inserted", "Other second",
        ]
        locations = [html.index(f"<h3>{title}</h3>") for title in expected_titles]
        self.assertEqual(locations, sorted(locations))


@override_settings(SECURE_SSL_REDIRECT=False)
class ProjectAdminOrderingTests(ProjectFixtures, TestCase):
    def setUp(self):
        super().setUp()
        user = get_user_model().objects.create_superuser(
            username="ordering-admin", email="admin@example.com", password="test-password"
        )
        self.client.force_login(user)

    def project_form_data(self, project, order):
        return {
            "title": project.title,
            "slug": project.slug,
            "category": self.category.pk,
            "order": order,
            "images-TOTAL_FORMS": "0",
            "images-INITIAL_FORMS": "0",
            "images-MIN_NUM_FORMS": "0",
            "images-MAX_NUM_FORMS": "1000",
            "_save": "Save",
        }

    def test_admin_add_inserts_project_at_requested_position(self):
        self.seed_projects()
        project = Project(title="Inserted", slug="inserted", category=self.category)

        response = self.client.post(
            reverse("admin:projects_project_add"), self.project_form_data(project, 2)
        )

        self.assertEqual(response.status_code, 302)
        self.assert_sequence(["Alpha", "Inserted", "Bravo", "Charlie", "Delta", "Echo"])

    def test_admin_change_moves_project_and_shifts_neighbors(self):
        self.seed_projects()
        project = Project.objects.get(title="Echo")

        response = self.client.post(
            reverse("admin:projects_project_change", args=[project.pk]),
            self.project_form_data(project, 2),
        )

        self.assertEqual(response.status_code, 302)
        self.assert_sequence(["Alpha", "Echo", "Bravo", "Charlie", "Delta"])

    def test_list_editable_saves_multiple_moves_without_reverting_shifted_neighbors(self):
        self.seed_projects()
        url = reverse("admin:projects_project_changelist")
        page = self.client.get(url)
        formset = page.context["cl"].formset
        moves = {"Alpha": 4, "Delta": 1}
        data = {
            "form-TOTAL_FORMS": str(len(formset.forms)),
            "form-INITIAL_FORMS": str(len(formset.forms)),
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "_save": "Save",
        }
        for index, form in enumerate(formset.forms):
            data[f"form-{index}-id"] = str(form.instance.pk)
            data[f"form-{index}-order"] = str(moves.get(form.instance.title, form.instance.order))

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.assert_sequence(["Delta", "Bravo", "Charlie", "Alpha", "Echo"])


@skipUnless(connection.vendor == 'postgresql', 'Concurrent ordering requires PostgreSQL.')
class ProjectConcurrentOrderingTests(ProjectFixtures, TransactionTestCase):
    def test_simultaneous_inserts_in_empty_section_have_distinct_positions(self):
        barrier = Barrier(3)
        category_id = self.category.pk

        def insert(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                Project.objects.create(
                    title=f'Concurrent {index}', slug=f'concurrent-{index}',
                    category_id=category_id, order=1,
                )
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(insert, index) for index in range(3)]
            for future in futures:
                future.result(timeout=30)

        self.assertEqual(list(Project.objects.values_list('order', flat=True)), [1, 2, 3])
