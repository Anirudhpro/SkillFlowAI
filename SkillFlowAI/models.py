from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    resume = models.CharField(max_length=15000, default="", null=True)  # Stores PDFs
    textDescription = models.CharField(max_length=5000, default="", null=True) # Stores text based resume

class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Links chat to user
    timestamp = models.DateTimeField(auto_now_add=True)  # Auto-sets date/time of chat
    user_input = models.TextField()  # Stores user's message
    chat_output = models.TextField()  # Stores AI response
    jobListing = models.JSONField(null=True, blank=True)  # Stores JSON metadata (e.g., tokens used)

    def __str__(self):
        return f"Chat by {self.user.username} on {self.timestamp}"