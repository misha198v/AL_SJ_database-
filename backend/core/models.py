# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Roles(models.Model):
    role_id = models.SmallAutoField(primary_key=True)
    role_name = models.CharField(unique=True, max_length=30)

    class Meta:
        managed = False
        db_table = 'roles'


class PipelineStages(models.Model):
    stage_id = models.SmallAutoField(primary_key=True)
    stage_name = models.CharField(unique=True, max_length=50)
    stage_order = models.SmallIntegerField(unique=True)
    description = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pipeline_stages'


class Users(models.Model):
    user_id = models.UUIDField(primary_key=True)
    full_name = models.CharField(max_length=120)
    email = models.CharField(unique=True, max_length=120, blank=True, null=True)
    phone = models.CharField(unique=True, max_length=20)
    password_hash = models.CharField(max_length=255)
    role = models.ForeignKey(Roles, models.DO_NOTHING)
    is_active = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'users'


class ClientProfiles(models.Model):
    user = models.OneToOneField(Users, models.DO_NOTHING, primary_key=True)
    national_id = models.CharField(unique=True, max_length=30)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    preferred_language = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'client_profiles'


class StaffProfiles(models.Model):
    user = models.OneToOneField(Users, models.DO_NOTHING, primary_key=True)
    employee_no = models.CharField(unique=True, max_length=20)
    date_hired = models.DateField()

    class Meta:
        managed = False
        db_table = 'staff_profiles'


class Applications(models.Model):
    application_id = models.UUIDField(primary_key=True)
    client = models.ForeignKey(Users, models.DO_NOTHING)
    assigned_agent = models.ForeignKey(Users, models.DO_NOTHING, related_name='applications_assigned_agent_set', blank=True, null=True)
    current_stage = models.ForeignKey(PipelineStages, models.DO_NOTHING)
    service_type = models.TextField()  # This field type is a guess.
    destination = models.CharField(max_length=80)
    travel_purpose = models.CharField(max_length=120, blank=True, null=True)
    preferred_travel_date = models.DateField()
    status = models.TextField()  # This field type is a guess.
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'applications'


class Documents(models.Model):
    document_id = models.UUIDField(primary_key=True)
    application = models.ForeignKey(Applications, models.DO_NOTHING)
    document_type = models.TextField()  # This field type is a guess.
    file_path = models.CharField(max_length=255)
    file_size_bytes = models.IntegerField()
    verification_status = models.TextField()  # This field type is a guess.
    verified_by = models.ForeignKey(Users, models.DO_NOTHING, db_column='verified_by', blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.CharField(max_length=500, blank=True, null=True)
    uploaded_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'documents'


class Payments(models.Model):
    payment_id = models.UUIDField(primary_key=True)
    application = models.ForeignKey(Applications, models.DO_NOTHING)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    payment_method = models.TextField()  # This field type is a guess.
    payer_phone = models.CharField(max_length=20)
    transaction_reference = models.CharField(unique=True, max_length=60, blank=True, null=True)
    status = models.TextField()  # This field type is a guess.
    initiated_at = models.DateTimeField()
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'payments'


class StageHistory(models.Model):
    history_id = models.BigAutoField(primary_key=True)
    application = models.ForeignKey(Applications, models.DO_NOTHING)
    from_stage = models.ForeignKey(PipelineStages, models.DO_NOTHING, blank=True, null=True)
    to_stage = models.ForeignKey(PipelineStages, models.DO_NOTHING, related_name='stagehistory_to_stage_set')
    changed_by = models.ForeignKey(Users, models.DO_NOTHING, db_column='changed_by', blank=True, null=True)
    changed_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'stage_history'


class ScheduleRecords(models.Model):
    schedule_id = models.UUIDField(primary_key=True)
    client = models.ForeignKey(Users, models.DO_NOTHING)
    staff = models.ForeignKey(Users, models.DO_NOTHING, related_name='schedulerecords_staff_set')
    appointment_type = models.CharField(max_length=60)
    scheduled_datetime = models.DateTimeField()
    status = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'schedule_records'


class Notifications(models.Model):
    notification_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(Users, models.DO_NOTHING)
    application = models.ForeignKey(Applications, models.DO_NOTHING, blank=True, null=True)
    channel = models.TextField()  # This field type is a guess.
    message = models.CharField(max_length=300)
    status = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'notifications'


class AuditLogs(models.Model):
    log_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(Users, models.DO_NOTHING, blank=True, null=True)
    action = models.CharField(max_length=60)
    entity_type = models.CharField(max_length=60, blank=True, null=True)
    entity_id = models.CharField(max_length=64, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'audit_logs'
