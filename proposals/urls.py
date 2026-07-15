from django.urls import path

from . import views

urlpatterns = [
    # ---- public site ----
    path("", views.public_home, name="home"),
    path("packages/", views.packages, name="packages"),
    path("packages/<slug:slug>/", views.package_detail, name="package_detail"),
    path("destinations/", views.public_destinations, name="destinations"),
    path("destinations/<int:pk>/", views.public_destination, name="destination_detail"),
    path("journal/", views.journal, name="journal"),
    path("journal/<slug:slug>/", views.journal_post, name="journal_post"),
    path("reviews/", views.reviews, name="reviews"),
    path("faq/", views.faqs, name="faq"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("book/", views.book, name="book"),
    path("booking/<uuid:token>/", views.booking_status, name="booking_status"),
    path("newsletter/", views.newsletter_subscribe, name="newsletter"),

    # ---- staff: proposal studio ----
    path("studio/", views.proposal_list, name="proposal_list"),
    path("studio/proposal/new/", views.proposal_form, name="proposal_new"),
    path("studio/proposal/<int:pk>/edit/", views.proposal_form, name="proposal_edit"),
    path("studio/proposal/<int:pk>/", views.proposal_detail, name="proposal_detail"),
    path("studio/proposal/<int:pk>/pdf/", views.proposal_pdf, name="proposal_pdf"),
    path("studio/library/search/", views.stock_search, name="stock_search"),
    path("studio/library/import/", views.stock_import, name="stock_import"),
]
