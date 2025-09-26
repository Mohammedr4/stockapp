from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # This is the emergency script. It will run once when the server starts.
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        username = 'admin'
        password = 'stocksavvyadminpassword123'
        email = 'admin@stocksavvy.com'

        if not User.objects.filter(username=username).exists():
            print(f'Creating emergency superuser: {username}')
            User.objects.create_superuser(username, email, password)
        else:
            print(f'Emergency superuser {username} already exists. Ensuring password is correct.')
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()