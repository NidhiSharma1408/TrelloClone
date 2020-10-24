import re
from django.core.exceptions import ValidationError

def validate_name(value):
    regex = re.compile('[@_!#$%^&*()<>?/\|}{~:1234567890]')
    if regex.search(value) != None:
        raise ValidationError("Can't contain special symbols and numbers.")
    if '[' in value or ']' in value:
        raise ValidationError("Can't contain special symbols and numbers.")