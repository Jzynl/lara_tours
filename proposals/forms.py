from django import forms

from .models import Booking, Destination


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            "full_name", "email", "phone", "destination", "trip_title",
            "num_adults", "num_children", "start_date", "end_date",
            "flexible_dates", "message",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Your full name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@email.com"}),
            "phone": forms.TextInput(attrs={"placeholder": "+255 …"}),
            "trip_title": forms.TextInput(attrs={"placeholder": "e.g. Honeymoon in Bali (if not in the list)"}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "message": forms.Textarea(attrs={"rows": 4, "placeholder": "Tell us what you have in mind…"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["destination"].queryset = Destination.objects.all().order_by("region", "name")
        self.fields["destination"].required = False
        self.fields["destination"].empty_label = "— Choose a destination —"
        self.fields["trip_title"].required = False
        self.fields["phone"].required = True
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput,)):
                field.widget.attrs.setdefault("class", "fld")

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("destination") and not cleaned.get("trip_title"):
            raise forms.ValidationError("Please choose a destination or describe the trip you'd like.")
        return cleaned


from .models import Review, NewsletterSubscriber


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["author_name", "location", "rating", "body", "trip"]
        widgets = {
            "author_name": forms.TextInput(attrs={"placeholder": "Your name"}),
            "location": forms.TextInput(attrs={"placeholder": "City / country (optional)"}),
            "rating": forms.Select(choices=[(5, "★★★★★"), (4, "★★★★"), (3, "★★★"), (2, "★★"), (1, "★")]),
            "body": forms.Textarea(attrs={"rows": 4, "placeholder": "Tell us about your trip…"}),
            "trip": forms.TextInput(attrs={"placeholder": "Which trip? (optional)"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", "fld")


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ["email"]
        widgets = {"email": forms.EmailInput(attrs={"placeholder": "your@email.com"})}
