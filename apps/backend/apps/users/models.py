from django.db import models


class User(models.Model):
    """Perfil mínimo vinculado a Clerk.

    Contraseñas, sesiones y roles viven en Clerk; esta tabla existe para tener una clave
    foránea local (carrito, pedidos, direcciones) y mostrar nombre y correo sin consultar a Clerk.
    """

    clerk_user_id = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email or self.clerk_user_id

    # DRF consulta estas propiedades para tratar al usuario como autenticado.
    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False
