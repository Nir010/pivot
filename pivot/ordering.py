"""Contiguous positions for content lists edited through the admin."""

from hashlib import blake2b

from django.db import connections, models, router, transaction
from django.db.models.signals import post_delete, pre_delete


ORDER_HELP_TEXT = (
    "Position in this section, starting at 1. Use 0 to place it last. "
    "Other items shift automatically."
)


def lock_ordering(model, using):
    """Serialize PostgreSQL edits, including inserts into an empty section."""
    connection = connections[using]
    if connection.vendor == 'postgresql':
        lock_id = int.from_bytes(
            blake2b(model._meta.db_table.encode(), digest_size=8).digest(),
            byteorder='big', signed=True,
        )
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_xact_lock(%s)', [lock_id])


def assign_positions(manager, items):
    changed = []
    for position, item in enumerate(items, start=1):
        if item.order != position:
            item.order = position
            changed.append(item)
    if changed:
        manager.bulk_update(changed, ['order'])


class OrderedModel(models.Model):
    """Insert and move rows within the section defined by ordering_scope."""

    ordering_scope = ()

    class Meta:
        abstract = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        pre_delete.connect(lock_before_ordered_delete, sender=cls)
        post_delete.connect(close_ordered_gap, sender=cls)

    @classmethod
    def from_db(cls, db, field_names, values, **kwargs):
        instance = super().from_db(db, field_names, values, **kwargs)
        if 'order' in field_names:
            instance._loaded_order = instance.order
        return instance

    def refresh_from_db(self, using=None, fields=None, from_queryset=None):
        super().refresh_from_db(using=using, fields=fields, from_queryset=from_queryset)
        if (fields is None or 'order' in fields) and 'order' in self.__dict__:
            self._loaded_order = self.order

    def save(self, *, force_insert=False, force_update=False, using=None, update_fields=None):
        using = using or router.db_for_write(type(self), instance=self)
        if update_fields is not None:
            update_fields = frozenset(update_fields)
            if not update_fields or not update_fields.intersection({'order', *self.ordering_scope}):
                return super().save(
                    force_insert=force_insert, force_update=force_update,
                    using=using, update_fields=update_fields,
                )

        with transaction.atomic(using=using):
            lock_ordering(type(self), using)
            manager = type(self)._base_manager.db_manager(using)
            current = manager.select_for_update().filter(pk=self.pk).first() if self.pk else None
            target_scope = {
                field: getattr(self, field)
                if current is None or update_fields is None or field in update_fields
                else getattr(current, field)
                for field in self.ordering_scope
            }
            source_scope = {field: getattr(current, field) for field in self.ordering_scope} if current else None

            # Admin list forms hold objects loaded before any rows are saved.
            # Preserve shifts made by earlier forms when this form didn't move.
            order_changed = current is None or (
                (update_fields is None or 'order' in update_fields)
                and (
                    self.order != getattr(self, '_loaded_order', current.order)
                    or (update_fields is not None and 'order' in update_fields)
                )
            )
            scope_changed = current is not None and source_scope != target_scope
            requested = self.order if order_changed or scope_changed else current.order
            if requested < 0:
                raise ValueError('Order must be zero or a positive position.')

            if current is not None and not order_changed and not scope_changed:
                self.order = current.order
                result = super().save(
                    force_insert=force_insert, force_update=force_update,
                    using=using, update_fields=update_fields,
                )
                self._loaded_order = self.order
                return result

            siblings = list(
                manager.select_for_update().filter(**target_scope).exclude(pk=self.pk)
            )
            position = len(siblings) + 1 if requested == 0 else max(1, min(requested, len(siblings) + 1))
            self.order = position
            if update_fields is not None:
                update_fields = update_fields | {'order'}
            result = super().save(
                force_insert=force_insert, force_update=force_update,
                using=using, update_fields=update_fields,
            )
            siblings.insert(position - 1, self)
            assign_positions(manager, siblings)

            if scope_changed:
                remaining = list(manager.select_for_update().filter(**source_scope))
                assign_positions(manager, remaining)

            self._loaded_order = self.order
            return result


def lock_before_ordered_delete(sender, instance, using, **kwargs):
    lock_ordering(sender, using)
    current = (
        sender._base_manager.using(using).select_for_update()
        .filter(pk=instance.pk).values(*sender.ordering_scope).first()
    )
    instance._deletion_scope = current


def close_ordered_gap(sender, instance, using, **kwargs):
    scope = getattr(instance, '_deletion_scope', None)
    if scope is not None:
        manager = sender._base_manager.db_manager(using)
        remaining = list(manager.select_for_update().filter(**scope))
        assign_positions(manager, remaining)
