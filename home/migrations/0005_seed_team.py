from django.db import migrations


# Seeds the team from the data previously stored in html/team.html,
# so the Team page is driven by the database instead of a JSON array.
def seed_team(apps, schema_editor):
    TeamMember = apps.get_model('home', 'TeamMember')
    team = [
        # (group, name, role, photo, qualifications, experience, works)
        ('leadership', 'Er. Udaya Raj Adhikari', 'Executive Director', 'team/udaya.png',
         "MACS \u2013 Risk Analytics, BE Computer Engineering",
         "20 years of experience in Risk Analytics, Catastrophe Modelling, Actuarial Valuations and Risk Advisory\n"
         "Dynamic experience in IT Process Design, ICT Framework, Risk Modelling",
         "Insurance Industry Specialist on Strengthening the Enabling Environment for Disaster Risk Financing in Nepal\n"
         "Solvency Assessment and Loss Reserving Techniques"),

        ('leadership', 'Er. Krishna Aryal', 'Director', 'team/krishna.png',
         "ME \u2013 Chemical Engineering, BE Structural Engineering \u2013 IOE",
         "Exclusive experience in designing Seismic Resistant Buildings\n"
         "Risk Analysis of Civil Structures",
         "Estimation and Valuation of Civil and Mechanical Structures\n"
         "Supervision and Monitoring of rural infrastructural development work for quality assurance"),
        
        ('members', 'Aadarsha Shrestha', 'Assistant Actuarial Manager', 'team/aadarsha.png',
         "Bachelor in Mathematical Sciences (BMS)",
         "1.5+ years of experience in Actuarial and Risk Analytics",
         "Employee Benefit Valuation of Gratuity, Leave, Pension, and Retirement Benefit Plans\n"
         "Risk-Based Capital (RBC) valuation and solvency assessment for non-life insurance companies\n"
         "Development of Own Risk and Solvency Assessment (ORSA) policies in line with applicable ORSA guidelines and toolkits for life insurance companies\n"
         "Ratio analysis of general insurance companies in Nepal, including analysis of loss ratio, expense ratio, combined ratio, premium, claims, and other key financial and operational indicators"),
       
        ('members', 'Sabita Gaihre', 'HR/Finance Officer', 'team/sabita.png',
         "MBS \u2013 Currently Pursuing",
         "7 Years of experience in Finance",
         "Handled audit, taxation, accounting and financial reporting engagements\n"
         "Preparation and review of VAT, Income Tax, and Excise Tax returns, financial statements, accounting records and related engagement documentation, while effectively liaising with clients and engagement teams"),
      
        ('members', 'Sokphungwa Limbu', 'Survey Analytics', 'team/sokphungwa.png',
         "Bachelor in Mathematical Sciences",
         "1.3 years of experience in Employee Benefit Valuation & Loss Assessment",
         "Designed a commercial parametric insurance policy for vertical farming, including risk identification, coverage structure, and pricing considerations\n"
         "Actuarial valuations of employee benefit plans, including gratuity, leave, and retirement benefits\n"
         "Survey valuation and Loss assessment for Marine, Property, and Engineering/EEI insurance claims"),
      
        ('members', 'Eva Chaudhary', 'Assistant Survey Manager', 'team/eva.png',
         "Master in Business Studies",
         "Around 5 years of experience in Survey Valuation and Loss Assessment",
         "Handling, evaluation and reporting several insurance related cases ranging from property, marine, motor, engineering cases and other related works\n"
         "Landing Cost, Rate Analysis, Reporting and Policy understanding and familiarities with insurance terminologies/clauses, excess and so on"),
      
        ('members', 'Sudhir Thapa', 'Assistant Survey Manager', 'team/sudhir.png',
         "MBA on finance",
         "8 years of experience in Motor insurance loss assessment, property insurance",
         "Loss assessment report on motor, fire & property"),
      
        ('members', 'Laxmi Pathak Adhikari', 'Operation and Legal Head', 'team/laxmi.png',
         "MA/LLB",
         "5 years of experience in legal and operational management",
         "Legal advisory and operational management of the company\n"
         "Other all types of legal works"),
        ]
    for group, name, role, photo, quals, exp, works in team:
        TeamMember.objects.create(
            group=group, name=name, role=role, photo=photo,
            qualifications=quals, experience=exp, works=works,
        )


def unseed_team(apps, schema_editor):
    TeamMember = apps.get_model('home', 'TeamMember')
    TeamMember.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_seed_services'),
    ]

    operations = [
        migrations.RunPython(seed_team, unseed_team),
    ]