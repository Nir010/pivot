from django.db import migrations


# The service descriptions were originally hardcoded in html/services.html.
# This seeds them into the database so the Services page becomes dynamic.
def seed_services(apps, schema_editor):
    Service = apps.get_model("home", "Service")
    services = [
        # (title, detail, is_primary)
        (
            "Actuarial Valuation",
            "We provide a comprehensive range of actuarial services tailored to meet your business requirements. Our expertise includes actuarial valuation, product pricing, risk assessment, financial modelling, reserving, solvency analysis and strategic advisory to support informed decision making.",
            True,
        ),
        (
            "Employee Benefits Valuation",
            "We provide actuarial valuation services for employee and retirement benefits, including gratuity, leave, pension and other long-term benefits. Our solutions help employers understand their future obligations, meet reporting requirements and make informed decisions regarding employee benefit programmes.",
            True,
        ),
        (
            "Risk Management",
            "We help organizations identify, assess, prioritize and manage risks across business, technology, operational, financial and external environments. We support clients in developing and implementing effective risk management frameworks that strengthen governance, improve decision making and help prevent potential losses.",
            True,
        ),
        (
            "Reinsurance Risk Analytics",
            "We provide analytical solutions for reinsurance pricing, exposure analysis, portfolio assessment, risk modelling and reinsurance structure evaluation. Our services help insurers better understand their risk exposures and develop effective strategies for risk transfer and reinsurance management.",
            True,
        ),
        (
            "Engineering Valuation and Assessment",
            "We provide professional valuation and assessment services for properties, infrastructure, industrial assets and engineering projects. Our valuations support insurance requirements, asset management, risk assessment and financial decision making through reliable and well supported analysis.",
            True,
        ),
        (
            "Loss Assessment and Survey",
            "We provide professional loss assessment and survey services across various insurance classes, including property, engineering, motor, marine and consequential loss. Our assessments combine technical expertise and industry practices to support accurate claims evaluation and effective risk management.",
            True,
        ),
        (
            "Financial Advisory",
            "We provide financial advisory services covering financial modelling, analysis, planning, risk assessment and strategic decision support. We work with clients to evaluate financial opportunities and challenges and develop practical solutions aligned with their business objectives.",
            True,
        ),
        (
            "Insurance and Reinsurance Advisory",
            "We provide specialized insurance and reinsurance advisory services to help clients manage risks, strengthen underwriting practices and make informed decisions. Our services cover insurance portfolio analysis, underwriting review, reinsurance programme design, pricing, exposure assessment, claims advisory and risk transfer strategies.",
            True,
        ),
        (
            "Data Analytics",
            "We study your data to find patterns and useful insights that help you make better decisions.",
            False,
        ),
        (
            "Modelling and Business Planning",
            "We build simple models and plans that help you forecast the future and plan your business with confidence.",
            False,
        ),
        (
            "Reinsurance Analytics",
            "We analyse how insurance companies share big risks, helping them choose the best way to protect themselves.",
            False,
        ),
        (
            "Catastrophic Modelling",
            "We estimate the damage that major disasters like earthquakes and floods could cause to people, property and businesses.",
            False,
        ),
        (
            "Risk Financing and Advisory",
            "We help businesses find the best ways to pay for unexpected losses and protect their money.",
            False,
        ),
        (
            "Corporate Restructuring and Reorganization",
            "We help companies reorganize their structure and operations so they can work better and stay financially healthy.",
            False,
        ),
        (
            "Governance and Risk Compliance",
            "We help businesses follow the rules and regulations and manage risk the right way.",
            False,
        ),
        (
            "Research and Reporting",
            "We study markets and data and write clear, simple reports that help businesses make informed decisions.",
            False,
        ),
    ]
    for title, detail, is_primary in services:
        Service.objects.create(title=title, detail=detail, is_primary=is_primary)


def unseed_services(apps, schema_editor):
    Service = apps.get_model("home", "Service")
    Service.objects.filter(is_primary__in=[True, False]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0003_teammember_group"),
    ]

    operations = [
        migrations.RunPython(seed_services, unseed_services),
    ]
