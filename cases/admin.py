from django.contrib import admin

from .models import AnalysisRun, Case

admin.site.register(Case)
admin.site.register(AnalysisRun)
