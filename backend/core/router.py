class DatabaseRouter:
    """Existing project models are read-only and never migrated by Django."""
    def db_for_read(self, model, **hints):
        return 'alsj' if model._meta.app_label == 'core' else 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'core':
            raise RuntimeError('Use an approved PostgreSQL routine for project writes.')
        return 'default'

    def allow_migrate(self, db, app_label, **hints):
        return db == 'default' and app_label in {'sessions', 'contenttypes'}

    def allow_relation(self, obj1, obj2, **hints):
        return obj1._meta.app_label == obj2._meta.app_label
