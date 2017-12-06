from __future__ import absolute_import

import pytest

from datetime import datetime

from sentry.testutils import TestCase
from sentry.tagstore import TagKeyStatus
from sentry.tagstore.v2.backend import TagStorage
from sentry.tagstore.v2.models import TagKey, TagValue, GroupTagKey, GroupTagValue, EventTag
from sentry.tagstore.exceptions import TagKeyNotFound, TagValueNotFound, GroupTagKeyNotFound, GroupTagValueNotFound


class V2TagStorage(TestCase):
    def setUp(self):
        self.ts = TagStorage()

        self.proj1 = self.create_project()
        self.proj1group1 = self.create_group(self.proj1)
        self.proj1group2 = self.create_group(self.proj1)
        self.proj1env1 = self.create_environment(project=self.proj1)
        self.proj1env2 = self.create_environment(project=self.proj1)
        self.proj1group1event1 = self.create_event(project=self.proj1, group=self.proj1group1)
        self.proj1group1event2 = self.create_event(project=self.proj1, group=self.proj1group1)
        self.proj1group1event3 = self.create_event(project=self.proj1, group=self.proj1group1)

        self.proj2 = self.create_project()
        self.proj2group1 = self.create_group(self.proj2)
        self.proj2env1 = self.create_environment(project=self.proj2)

        self.key1 = 'key1'
        self.value1 = 'value1'

    def test_create_tag_key(self):
        with pytest.raises(TagKeyNotFound):
            self.ts.get_tag_key(
                project_id=self.proj1.id,
                environment_id=self.proj1env1.id,
                key=self.key1,
            )

        assert self.ts.get_tag_keys(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
        ) == []

        tk = self.ts.create_tag_key(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        )

        assert self.ts.get_tag_key(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        ).id == tk.id

        assert self.ts.get_tag_keys(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
        ) == [tk]

        assert TagKey.objects.all().count() == 1

    def test_get_or_create_tag_key(self):
        tk1, _ = self.ts.get_or_create_tag_key(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        )

        tk2, _ = self.ts.get_or_create_tag_key(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        )

        assert tk1.id == tk2.id
        assert TagKey.objects.filter(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        ).count() == 1
        assert TagKey.objects.all().count() == 1

    def test_create_tag_value(self):
        with pytest.raises(TagValueNotFound):
            self.ts.get_tag_value(
                project_id=self.proj1.id,
                environment_id=self.proj1env1.id,
                key=self.key1,
                value=self.value1,
            )

        assert self.ts.get_tag_values(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        ) == []

        tv = self.ts.create_tag_value(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
            value=self.value1,
        )

        assert self.ts.get_tag_values(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        ) == [tv]

        assert self.ts.get_tag_value(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
            value=self.value1,
        ).id == tv.id
        assert TagKey.objects.all().count() == 1
        assert TagValue.objects.all().count() == 1

    def test_get_or_create_tag_value(self):
        tv1, _ = self.ts.get_or_create_tag_value(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
            value=self.value1,
        )

        tv2, _ = self.ts.get_or_create_tag_value(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
            value=self.value1,
        )

        assert tv1.id == tv2.id

        tk = TagKey.objects.get(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        )

        assert TagKey.objects.all().count() == 1

        assert TagValue.objects.filter(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            _key_id=tk.id,
            value=self.value1,
        ).count() == 1
        assert TagValue.objects.all().count() == 1

    def test_create_group_tag_key(self):
        with pytest.raises(GroupTagKeyNotFound):
            self.ts.get_group_tag_key(
                project_id=self.proj1.id,
                group_id=self.proj1group1.id,
                environment_id=self.proj1env1.id,
                key=self.key1,
            )

        assert self.ts.get_group_tag_keys(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
        ) == []

        gtk = self.ts.create_group_tag_key(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        )

        self.ts.get_group_tag_keys(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
        ) == [gtk]

        TagKey.objects.get(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        )
        assert TagKey.objects.all().count() == 1

        assert self.ts.get_group_tag_key(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        ).id == gtk.id
        assert GroupTagKey.objects.all().count() == 1

    def test_get_or_create_group_tag_key(self):
        gtk1, _ = self.ts.get_or_create_group_tag_key(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        )

        gtk2, _ = self.ts.get_or_create_group_tag_key(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        )

        assert gtk1.id == gtk2.id

        tk = TagKey.objects.get(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        )
        assert TagKey.objects.all().count() == 1

        assert GroupTagKey.objects.filter(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            _key_id=tk.id,
        ).count() == 1
        assert GroupTagKey.objects.all().count() == 1

    def test_create_group_tag_value(self):
        with pytest.raises(GroupTagValueNotFound):
            self.ts.get_group_tag_value(
                project_id=self.proj1.id,
                group_id=self.proj1group1.id,
                environment_id=self.proj1env1.id,
                key=self.key1,
                value=self.value1,
            )

        assert self.ts.get_group_tag_values(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        ) == []

        gtv = self.ts.create_group_tag_value(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
            value=self.value1,
        )

        assert self.ts.get_group_tag_values(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        ) == [gtv]

        assert TagKey.objects.all().count() == 1
        assert TagValue.objects.all().count() == 1

        assert self.ts.get_group_tag_value(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
            value=self.value1,
        ).id == gtv.id
        assert GroupTagValue.objects.all().count() == 1

    def test_get_or_create_group_tag_value(self):
        gtv1, _ = self.ts.get_or_create_group_tag_value(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
            value=self.value1,
        )

        gtv2, _ = self.ts.get_or_create_group_tag_value(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
            value=self.value1,
        )

        assert gtv1.id == gtv2.id

        tk = TagKey.objects.get(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        )
        assert TagKey.objects.all().count() == 1

        tv = TagValue.objects.get(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            _key_id=tk.id,
            value=self.value1,
        )
        assert TagValue.objects.all().count() == 1

        assert GroupTagValue.objects.filter(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            _key_id=tk.id,
            _value_id=tv.id,
        ).count() == 1
        assert GroupTagValue.objects.all().count() == 1

    def test_create_event_tags(self):
        v1, _ = self.ts.get_or_create_tag_value(self.proj1.id, self.proj1env1.id, 'k1', 'v1')
        v2, _ = self.ts.get_or_create_tag_value(self.proj1.id, self.proj1env1.id, 'k2', 'v2')
        v3, _ = self.ts.get_or_create_tag_value(self.proj1.id, self.proj1env1.id, 'k3', 'v3')

        tags = [(v1._key.id, v1.id), (v2._key.id, v2.id), (v3._key.id, v3.id)]
        self.ts.create_event_tags(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            event_id=self.proj1group1event1.id,
            tags=tags
        )

        assert EventTag.objects.count() == 3
        for (key_id, value_id) in tags:
            assert EventTag.objects.get(
                project_id=self.proj1.id,
                group_id=self.proj1group1.id,
                environment_id=self.proj1env1.id,
                event_id=self.proj1group1event1.id,
                key_id=key_id,
                value_id=value_id,
            ) is not None

    def test_delete_tag_key(self):
        tk1 = self.ts.create_tag_key(
            project_id=self.proj1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        )

        tk2 = self.ts.create_tag_key(
            project_id=self.proj1.id,
            environment_id=self.proj1env2.id,
            key=self.key1,
        )

        assert TagKey.objects.filter(
            project_id=self.proj1.id,
            status=TagKeyStatus.VISIBLE,
        ).count() == 2

        deleted = self.ts.delete_tag_key(self.proj1.id, self.key1)
        assert tk1 in deleted
        assert tk2 in deleted

        assert TagKey.objects.filter(
            project_id=self.proj1.id,
            status=TagKeyStatus.VISIBLE,
        ).count() == 0

    def test_delete_all_group_tag_keys(self):
        assert GroupTagKey.objects.count() == 0

        self.ts.create_group_tag_key(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
        )

        assert GroupTagKey.objects.count() == 1

        self.ts.delete_all_group_tag_keys(self.proj1.id, self.proj1group1.id)

        assert GroupTagKey.objects.count() == 0

    def test_delete_all_group_tag_values(self):
        assert GroupTagValue.objects.count() == 0

        self.ts.create_group_tag_value(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            key=self.key1,
            value=self.value1,
        )

        assert GroupTagValue.objects.count() == 1

        self.ts.delete_all_group_tag_values(self.proj1.id, self.proj1group1.id)

        assert GroupTagValue.objects.count() == 0

    def test_get_group_event_ids(self):
        tags = {
            'abc': 'xyz',
            'foo': 'bar',
            'baz': 'quux',
        }

        def _create_tags_for_dict(tags):
            ids = []
            for k, v in tags.items():
                key, _ = self.ts.get_or_create_tag_key(self.proj1.id, self.proj1env1.id, k)
                value, _ = self.ts.get_or_create_tag_value(self.proj1.id, self.proj1env1.id, k, v)
                ids.append((key.id, value.id))
            return ids

        tags_ids = _create_tags_for_dict(tags)

        # 2 events with the same tags
        for event in (self.proj1group1event1, self.proj1group1event2):
            self.ts.create_event_tags(
                project_id=self.proj1.id,
                group_id=self.proj1group1.id,
                environment_id=self.proj1env1.id,
                event_id=event.id,
                tags=tags_ids,
            )

        different_tags = {
            'abc': 'DIFFERENT',
            'foo': 'bar',
            'baz': 'quux',
        }

        different_tags_ids = _create_tags_for_dict(different_tags)

        # 1 event with different tags
        self.ts.create_event_tags(
            project_id=self.proj1.id,
            group_id=self.proj1group1.id,
            environment_id=self.proj1env1.id,
            event_id=self.proj1group1event3.id,
            tags=different_tags_ids,
        )

        assert len(
            self.ts.get_group_event_ids(
                self.proj1.id,
                self.proj1group1.id,
                self.proj1env1.id,
                tags)) == 2

    def test_get_groups_user_counts(self):
        k1, _ = self.ts.get_or_create_group_tag_key(
            self.proj1.id,
            self.proj1group1.id,
            self.proj1env1.id,
            'sentry:user')
        k1.values_seen = 7
        k1.save()

        k2, _ = self.ts.get_or_create_group_tag_key(
            self.proj1.id,
            self.proj1group2.id,
            self.proj1env1.id,
            'sentry:user')
        k2.values_seen = 11
        k2.save()

        assert dict(self.ts.get_groups_user_counts(
            self.proj1.id,
            [self.proj1group1.id, self.proj1group2.id],
            self.proj1env1.id).items()) == {k1.id: 7, k2.id: 11}

    def test_get_group_tag_value_count(self):
        v1, _ = self.ts.get_or_create_group_tag_value(
            self.proj1.id,
            self.proj1group1.id,
            self.proj1env1.id,
            self.key1,
            'value1')
        v1.times_seen = 7
        v1.save()

        v2, _ = self.ts.get_or_create_group_tag_value(
            self.proj1.id,
            self.proj1group1.id,
            self.proj1env1.id,
            self.key1,
            'value2')
        v2.times_seen = 11
        v2.save()

        assert self.ts.get_group_tag_value_count(
            self.proj1.id,
            self.proj1group1.id,
            self.proj1env1.id,
            self.key1,
        ) == 18

    def test_get_top_group_tag_values(self):
        v1, _ = self.ts.get_or_create_group_tag_value(
            self.proj1.id,
            self.proj1group1.id,
            self.proj1env1.id,
            self.key1,
            'value1')
        v1.times_seen = 7
        v1.save()

        v2, _ = self.ts.get_or_create_group_tag_value(
            self.proj1.id,
            self.proj1group1.id,
            self.proj1env1.id,
            self.key1,
            'value2')
        v2.times_seen = 11
        v2.save()

        resp = list(
            self.ts.get_top_group_tag_values(
                self.proj1.id,
                self.proj1group1.id,
                self.proj1env1.id,
                self.key1,
            )
        )

        assert resp[0].times_seen == 11
        assert resp[0].key == self.key1
        assert resp[0].group_id == self.proj1group1.id

        assert resp[1].times_seen == 7
        assert resp[1].key == self.key1
        assert resp[1].group_id == self.proj1group1.id

    def test_get_first_release(self):
        v1, _ = self.ts.get_or_create_group_tag_value(
            self.proj1.id,
            self.proj1group1.id,
            self.proj1env1.id,
            'sentry:release',
            '1.0')
        v1.first_seen = datetime(2000, 1, 1)
        v1.save()

        v2, _ = self.ts.get_or_create_group_tag_value(
            self.proj1.id,
            self.proj1group1.id,
            self.proj1env1.id,
            'sentry:release',
            '2.0')
        v2.first_seen = datetime(2000, 1, 2)
        v2.save()

        assert self.ts.get_first_release(
            self.proj1.id,
            self.proj1group1.id,
        ) == '1.0'

    def test_get_last_release(self):
        v1, _ = self.ts.get_or_create_group_tag_value(
            self.proj1.id,
            self.proj1group1.id,
            self.proj1env1.id,
            'sentry:release',
            '1.0')
        v1.last_seen = datetime(2000, 1, 1)
        v1.save()

        v2, _ = self.ts.get_or_create_group_tag_value(
            self.proj1.id,
            self.proj1group1.id,
            self.proj1env1.id,
            'sentry:release',
            '2.0')
        v2.last_seen = datetime(2000, 1, 2)
        v2.save()

        assert self.ts.get_last_release(
            self.proj1.id,
            self.proj1group1.id,
        ) == '2.0'

    def test_get_release_tags(self):
        # self.ts.get_release_tags(project_ids, environment_id, versions)
        pass

    def test_get_group_ids_for_users(self):
        # self.ts.get_group_ids_for_users(project_ids, event_users, limit=100)
        pass

    def test_get_group_tag_values_for_users(self):
        # self.ts.get_group_tag_values_for_users(event_users, limit=100)
        pass

    def test_get_tags_for_search_filter(self):
        # self.ts.get_tags_for_search_filter(project_id, tags)
        pass

    def test_update_group_tag_key_values_seen(self):
        # self.ts.update_group_tag_key_values_seen(project_id, group_ids)
        pass

    def test_get_tag_value_qs(self):
        # self.ts.get_tag_value_qs(project_id, environment_id, key, query=None)
        pass

    def test_get_group_tag_value_qs(self):
        # self.ts.get_group_tag_value_qs(project_id, group_id, environment_id, key)
        pass

    def test_update_group_for_events(self):
        # self.ts.update_group_for_events(project_id, event_ids, destination_id)
        pass
