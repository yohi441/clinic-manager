from django import forms
from .models import LensType, Patient

class PatientForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lens_type'].queryset = LensType.objects.filter(is_active=True)

    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 'contact',
            'prescription_od', 'prescription_os', 'lens_type',
            'address', 'notes', 'status', 'last_visit',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all', 'placeholder': 'John'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all', 'placeholder': 'Doe'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'text', 'class': 'datepicker w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all', 'placeholder': 'YYYY-MM-DD'}),
            'gender': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all bg-white'}),
            'contact': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all', 'placeholder': '+1 (555) 123-4567'}),
            'prescription_od': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all', 'placeholder': '-2.50 SPH / -0.75 CYL'}),
            'prescription_os': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all', 'placeholder': '-2.25 SPH / -0.50 CYL'}),
            'lens_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all bg-white'}),
            'status': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all bg-white'}),
            'last_visit': forms.DateInput(attrs={'type': 'text', 'class': 'datepicker w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all', 'placeholder': 'YYYY-MM-DD'}),
            'address': forms.Textarea(attrs={'rows': '2', 'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all resize-none', 'placeholder': '123 Main St, New York, NY'}),
            'notes': forms.Textarea(attrs={'rows': '2', 'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all resize-none', 'placeholder': 'Allergies, medical history, frame preferences...'}),
        }
