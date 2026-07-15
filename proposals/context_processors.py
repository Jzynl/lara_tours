from .models import CompanyProfile


def company(request):
    """Make the company profile available to every template as `company`."""
    try:
        return {"company": CompanyProfile.get_solo()}
    except Exception:
        return {"company": None}
