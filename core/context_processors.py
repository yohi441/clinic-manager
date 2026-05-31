from .models import ClinicSetting


def clinic_settings(request):
    return {'CLINIC_NAME': ClinicSetting.load().clinic_name}
