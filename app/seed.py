from sqlalchemy import select
from .models import Organization, ReportingPeriod, Department, User, Program, SubProgram, Indicator, IndicatorValue, Activity, Submission
from .security import hash_password

DEMO_PASSWORD = "Civensa2026!"

def seed(db):
    if db.scalar(select(Organization).limit(1)):
        return
    org = Organization(name="T.C. Büyükçekmece Belediyesi")
    period = ReportingPeriod(year=2026, status="active", template_status="verified")
    health = Department(name="Sağlık İşleri Müdürlüğü", organization=org)
    strategy = Department(name="Strateji Geliştirme Müdürlüğü", organization=org)
    db.add_all([org, period, health, strategy]); db.flush()
    db.add_all([
        User(email="strateji@civensa.local", full_name="Strateji Kullanıcısı", role="strategy", password_hash=hash_password(DEMO_PASSWORD)),
        User(email="saglik@civensa.local", full_name="Sağlık İşleri Kullanıcısı", role="department", department_id=health.id, password_hash=hash_password(DEMO_PASSWORD)),
    ])
    program_specs = [
        ("Yoksullukla Mücadele ve Sosyal Yardımlaşma", "Sosyal Yardımlaşma"),
        ("Tedavi Edici Sağlık", "Tedavi Hizmetleri"),
        ("Kent Güvenliği ve Esenliği", "Çevre ve Halk Sağlığının Korunması"),
        ("Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim", "Engelli Bakımı"),
    ]
    subs=[]
    for p_name,s_name in program_specs:
        p=Program(period_id=period.id,name=p_name); db.add(p); db.flush()
        sp=SubProgram(period_id=period.id,program_id=p.id,name=s_name,rationale="2026 performans programı kapsamında müdürlük hizmetleri.",goal=f"{s_name} hizmetlerinin etkin ve ölçülebilir biçimde yürütülmesi.")
        db.add(sp); db.flush(); subs.append(sp)
    indicators=[
        (subs[0],"Yıl içinde sunulan sağlık hizmeti sayısı","Oran (%)",{2025:12500,2026:13500,2027:14500,2028:16500}),
        (subs[1],"Hasta nakil hizmetinden yararlanan kişi sayısı","Adet",{2025:6000,2026:6500,2027:7000,2028:7500}),
        (subs[1],"Evde sağlık hizmeti verilen kişi sayısı","Adet",{2025:2500,2026:2700,2027:2900,2028:3100}),
        (subs[2],"Halk sağlığına yönelik gerçekleştirilen denetim sayısı","Adet",{2025:1200,2026:1350,2027:1450,2028:1550}),
        (subs[3],"Engelli bireylere sunulan destek hizmeti sayısı","Adet",{2025:850,2026:950,2027:1050,2028:1150}),
    ]
    for sp,name,unit,vals in indicators:
        ind=Indicator(period_id=period.id,department_id=health.id,subprogram_id=sp.id,name=name,unit=unit,explanation="Gösterge ilgili müdürlük kayıtlarından izlenir.",calculation_method="Yıl içindeki toplam kayıt sayısı.",data_source="Sağlık İşleri Müdürlüğü",status="draft")
        db.add(ind); db.flush()
        for year,val in vals.items(): db.add(IndicatorValue(indicator_id=ind.id,year=year,value_kind="target",value=float(val)))
    activities=[
        (subs[0],"Koruyucu ve önleyici sağlık hizmetlerinin yürütülmesi",2250000,3200000,3600000,4000000),
        (subs[1],"Hasta nakil ve evde sağlık hizmetlerinin yürütülmesi",6800000,7600000,8400000,9200000),
        (subs[2],"Çevre ve halk sağlığı denetim hizmetleri",3100000,3670000,4100000,4550000),
        (subs[3],"Engelli bireylere yönelik sağlık ve destek hizmetleri",1750000,2000000,2200000,2450000),
    ]
    for sp,name,b25,b26,b27,b28 in activities:
        db.add(Activity(period_id=period.id,department_id=health.id,subprogram_id=sp.id,name=name,explanation="İlgili alt program kapsamında yürütülen hizmetler.",budget_2025=b25,budget_2026=b26,budget_2027=b27,budget_2028=b28,budget_inside=b26,budget_outside=0))
    db.add(Submission(department_id=health.id,period_id=period.id,status="draft"))
    db.commit()
