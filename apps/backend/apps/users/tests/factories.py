import factory

from apps.users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    clerk_user_id = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda user: f"{user.clerk_user_id}@example.com")
    first_name = "Ana"
    last_name = "Pérez"
