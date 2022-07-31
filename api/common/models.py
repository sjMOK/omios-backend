from django.db.models import Model, AutoField, ForeignKey, DO_NOTHING, CharField, DateField


class TemporaryImage(Model):
    image_url = CharField(primary_key=True, max_length=200)

    class Meta:
        db_table = 'temporary_image'


class SettingGroup(Model):
    id = AutoField(primary_key=True)
    app = CharField(max_length=30)
    main_key = CharField(max_length=30)
    sub_key = CharField(max_length=30, null=True)
    name = CharField(max_length=30)
    created_at = DateField(auto_now_add=True)

    class Meta:
        db_table = 'setting_group'
        unique_together = (('app', 'name'))
        ordering = ['id']


class SettingItem(Model):
    id = AutoField(primary_key=True)
    group = ForeignKey('SettingGroup', DO_NOTHING, related_name='items')
    name = CharField(max_length=30)
    created_at = DateField(auto_now_add=True)

    class Meta:
        db_table = 'setting_item'
        unique_together = (('group', 'name'))
        ordering = ['id']
