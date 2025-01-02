from tortoise import fields, models


class Links(models.Model):
    """
    The User model
    """

    id = fields.IntField(primary_key=True)
    url = fields.CharField(max_length=20, unique=True)
    url_hashed = fields.CharField(max_length=20, unique=True)
    title = fields.CharField(max_length=50, null=True)
    text = fields.CharField(max_length=50, null=True)
    tags = fields.CharField(max_length=30, null=True)
    private = fields.BooleanField(default=False)
    sticky = fields.BooleanField(default=False)
    image = fields.CharField(max_length=20, null=True)
    video = fields.CharField(max_length=20, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)
