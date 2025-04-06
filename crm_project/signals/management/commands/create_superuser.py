from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError


User = get_user_model()


class Command(BaseCommand):
    help = 'Создание суперпользователя с фиксированными параметрами'

    def handle(self, *args, **options):
        username = 'admin'
        email = 'admin@example.com'
        password = 'admin'
        
        try:
            # Проверяем существование пользователя
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'Пользователь {username} уже существует')
                )
                # Обновляем пароль существующего пользователя
                user = User.objects.get(username=username)
                user.set_password(password)
                user.email = email
                user.is_staff = True
                user.is_superuser = True
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Обновлены данные пользователя {username}')
                )
            else:
                # Создаем нового пользователя
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Создан суперпользователь {username}')
                )
        except IntegrityError:
            self.stdout.write(
                self.style.ERROR(
                    f'Ошибка создания суперпользователя: пользователь {username} '
                    f'уже существует'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Произошла ошибка: {str(e)}')
            ) 