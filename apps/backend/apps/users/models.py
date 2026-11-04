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


class AdminAuditLog(models.Model):
    """Registro de altas y bajas de administradores: quién, a quién y cuándo (HU-12)."""

    class Action(models.TextChoices):
        INVITED = "admin_invited", "Administrador invitado"
        REMOVED = "admin_removed", "Administrador eliminado"

    action = models.CharField(max_length=20, choices=Action)
    # SET_NULL conserva el registro si el administrador que actuó se elimina de la base local.
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    actor_email = models.EmailField()  # Copia: sobrevive aunque cambie o se anonimice el actor.
    target_email = models.EmailField()
    target_clerk_user_id = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "admin_audit_log"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.action}: {self.actor_email} -> {self.target_email}"
