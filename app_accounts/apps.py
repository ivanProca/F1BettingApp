from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_accounts'
    verbose_name = 'User Accounts'
    
    def ready(self):
        # Import and connect signal handlers
        import app_accounts.signals