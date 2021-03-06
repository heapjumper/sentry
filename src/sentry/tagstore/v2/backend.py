"""
sentry.tagstore.v2.backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2017 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

from django.db import IntegrityError, transaction

from sentry.tagstore import TagKeyStatus
from sentry.tagstore.base import TagStorage

from .models import EventTag, GroupTagKey, GroupTagValue, TagKey, TagValue


class TagStorage(TagStorage):
    """\
    The v2 tagstore backend stores and respects ``environment_id`` arguments and stores
    ``times_seen`` and ``values_seen`` in Redis for cheap incr/decrs.

    An ``environment_id`` value of ``None`` is used to keep track of the aggregate value across
    all environments.
    """

    def setup(self):
        self.setup_deletions(
            tagkey_model=TagKey,
            tagvalue_model=TagValue,
            grouptagkey_model=GroupTagKey,
            grouptagvalue_model=GroupTagValue,
            eventtag_model=EventTag,
        )

        self.setup_cleanup(
            tagvalue_model=TagValue,
            grouptagvalue_model=GroupTagValue,
            eventtag_model=EventTag,
        )

        self.setup_merge(
            grouptagkey_model=GroupTagKey,
            grouptagvalue_model=GroupTagValue,
        )

        self.setup_tasks(
            tagkey_model=TagKey,
        )

        self.setup_receivers(
            tagvalue_model=TagValue,
            grouptagvalue_model=GroupTagValue,
        )

        # TODO(brett): v2-specific receivers for keeping environment aggregates up to date

    def create_tag_key(self, project_id, environment_id, key, **kwargs):
        return TagKey.objects.create(
            project_id=project_id,
            environment_id=environment_id,
            key=key,
            **kwargs
        )

    def get_or_create_tag_key(self, project_id, environment_id, key, **kwargs):
        return TagKey.objects.get_or_create(
            project_id=project_id,
            environment_id=environment_id,
            key=key,
            **kwargs
        )

    def create_tag_value(self, project_id, environment_id, key, value, **kwargs):
        tag_key, _ = self.get_or_create_tag_key(
            project_id, environment_id, key, **kwargs)

        return TagValue.objects.create(
            project_id=project_id,
            environment_id=environment_id,
            _key_id=tag_key.id,
            value=value,
            **kwargs
        )

    def get_or_create_tag_value(self, project_id, environment_id, key, value, **kwargs):
        tag_key, _ = self.get_or_create_tag_key(
            project_id, environment_id, key, **kwargs)

        return TagValue.objects.get_or_create(
            project_id=project_id,
            environment_id=environment_id,
            _key_id=tag_key.id,
            value=value,
            **kwargs
        )

    def create_group_tag_key(self, project_id, group_id, environment_id, key, **kwargs):
        tag_key, _ = self.get_or_create_tag_key(
            project_id, environment_id, key, **kwargs)

        return GroupTagKey.objects.create(
            project_id=project_id,
            group_id=group_id,
            environment_id=environment_id,
            _key_id=tag_key.id,
            **kwargs
        )

    def get_or_create_group_tag_key(self, project_id, group_id, environment_id, key, **kwargs):
        tag_key, _ = self.get_or_create_tag_key(
            project_id, environment_id, key, **kwargs)

        return GroupTagKey.objects.get_or_create(
            project_id=project_id,
            group_id=group_id,
            environment_id=environment_id,
            _key_id=tag_key.id,
            **kwargs
        )

    def create_group_tag_value(self, project_id, group_id, environment_id, key, value, **kwargs):
        tag_key, _ = self.get_or_create_tag_key(
            project_id, environment_id, key, **kwargs)

        tag_value, _ = self.get_or_create_tag_value(
            project_id, environment_id, key, value, **kwargs)

        return GroupTagValue.objects.create(
            project_id=project_id,
            group_id=group_id,
            environment_id=environment_id,
            _key_id=tag_key.id,
            _value_id=tag_value.id,
            **kwargs
        )

    def get_or_create_group_tag_value(self, project_id, group_id,
                                      environment_id, key, value, **kwargs):
        tag_key, _ = self.get_or_create_tag_key(
            project_id, environment_id, key, **kwargs)

        tag_value, _ = self.get_or_create_tag_value(
            project_id, environment_id, key, value, **kwargs)

        return GroupTagValue.objects.get_or_create(
            project_id=project_id,
            group_id=group_id,
            environment_id=environment_id,
            _key_id=tag_key.id,
            _value_id=tag_value.id,
            **kwargs
        )

    def create_event_tags(self, project_id, group_id, environment_id, event_id, tags):
        try:
            # don't let a duplicate break the outer transaction
            with transaction.atomic():
                # Tags are bulk inserted because this is an all-or-nothing situation.
                # Either the whole transaction works, or it doesn't. There's no value
                # in a partial success where we'd need to replay half of the rows.
                EventTag.objects.bulk_create([
                    EventTag(
                        project_id=project_id,
                        environment_id=environment_id,
                        group_id=group_id,
                        event_id=event_id,
                        key_id=key_id,
                        value_id=value_id,
                    )
                    for key_id, value_id in tags
                ])
        except IntegrityError:
            pass

    def get_tag_key(self, project_id, environment_id, key, status=TagKeyStatus.VISIBLE):
        from sentry.tagstore.exceptions import TagKeyNotFound

        qs = TagKey.objects.filter(
            project_id=project_id,
            key=key,
            **self._get_environment_filter(environment_id)
        )

        if status is not None:
            qs = qs.filter(status=status)

        try:
            return qs.get()
        except TagKey.DoesNotExist:
            raise TagKeyNotFound

    def get_tag_keys(self, project_id, environment_id, status=TagKeyStatus.VISIBLE):
        qs = TagKey.objects.filter(
            project_id=project_id,
            **self._get_environment_filter(environment_id)
        )

        if status is not None:
            qs = qs.filter(status=status)

        return list(qs)

    def get_tag_value(self, project_id, environment_id, key, value):
        from sentry.tagstore.exceptions import TagValueNotFound

        qs = TagValue.objects.filter(
            project_id=project_id,
            _key__key=key,
            value=value,
            **self._get_environment_filter(environment_id)
        )

        try:
            return qs.get()
        except TagValue.DoesNotExist:
            raise TagValueNotFound

    def get_tag_values(self, project_id, environment_id, key):
        qs = TagValue.objects.filter(
            project_id=project_id,
            _key__key=key,
            **self._get_environment_filter(environment_id)
        )

        return list(qs)

    def get_group_tag_key(self, project_id, group_id, environment_id, key):
        from sentry.tagstore.exceptions import GroupTagKeyNotFound

        qs = GroupTagKey.objects.filter(
            project_id=project_id,
            group_id=group_id,
            _key__key=key,
            **self._get_environment_filter(environment_id)
        )

        try:
            return qs.get()
        except GroupTagKey.DoesNotExist:
            raise GroupTagKeyNotFound

    def get_group_tag_keys(self, project_id, group_id, environment_id, limit=None):
        qs = GroupTagKey.objects.filter(
            group_id=group_id,
            **self._get_environment_filter(environment_id)
        )

        if limit is not None:
            qs = qs[:limit]

        return list(qs)

    def get_group_tag_value(self, project_id, group_id, environment_id, key, value):
        from sentry.tagstore.exceptions import GroupTagValueNotFound

        qs = GroupTagValue.objects.filter(
            project_id=project_id,
            group_id=group_id,
            _key__key=key,
            _value__value=value,
            **self._get_environment_filter(environment_id)
        )

        try:
            return qs.get()
        except GroupTagValue.DoesNotExist:
            raise GroupTagValueNotFound

    def get_group_tag_values(self, project_id, group_id, environment_id, key):
        qs = GroupTagValue.objects.filter(
            group_id=group_id,
            _key__key=key,
            **self._get_environment_filter(environment_id)
        )

        return list(qs)

    def delete_tag_key(self, project_id, key):
        from sentry.tagstore.tasks import delete_tag_key as delete_tag_key_task

        tagkeys_qs = TagKey.objects.filter(
            project_id=project_id,
            key=key,
        )

        deleted = []
        for tagkey in tagkeys_qs:
            updated = TagKey.objects.filter(
                id=tagkey.id,
                status=TagKeyStatus.VISIBLE,
            ).update(status=TagKeyStatus.PENDING_DELETION)

            if updated:
                delete_tag_key_task.delay(object_id=tagkey.id)
                deleted.append(tagkey)

        return deleted

    def delete_all_group_tag_keys(self, group_id):
        GroupTagKey.objects.filter(
            group_id=group_id,
        ).delete()

    def delete_all_group_tag_values(self, group_id):
        GroupTagValue.objects.filter(
            group_id=group_id,
        ).delete()

    def _get_environment_filter(self, environment_id):
        if environment_id is None:
            return {'environment_id__isnull': True}
        else:
            return {'environment_id': environment_id}
