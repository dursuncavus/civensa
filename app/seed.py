import os
from sqlalchemy import select
from .models import (
    Organization, ReportingPeriod, Department, User, Program, SubProgram,
    Indicator, IndicatorValue, Activity, ActivityCostValue, DepartmentCostValue, Submission
)
from .security import hash_password

def demo_password() -> str:
    """Development/test-only demo password supplied by the environment."""
    value = os.getenv("DEMO_PASSWORD", "").strip()
    if len(value) < 12:
        raise RuntimeError("DEMO_SEED=1 iken en az 12 karakterlik DEMO_PASSWORD zorunludur.")
    return value



def seed(db):
    if db.scalar(select(Organization).limit(1)):
        return

    org = Organization(name="T.C. Büyükçekmece Belediyesi")
    period = ReportingPeriod(year=2026, status="active", template_status="verified")
    health = Department(name="Sağlık İşleri Müdürlüğü", organization=org)
    strategy = Department(name="Strateji Geliştirme Müdürlüğü", organization=org)
    db.add_all([org, period, health, strategy]); db.flush()

    db.add_all([
        User(email="strateji@civensa.local", full_name="Strateji Kullanıcısı", role="strategy", password_hash=hash_password(demo_password())),
        User(email="saglik@civensa.local", full_name="Sağlık İşleri Kullanıcısı", role="department", department_id=health.id, password_hash=hash_password(demo_password())),
    ])

    program_specs = [
        ("YOKSULLUKLA MÜCADELE VE SOSYAL YARDIMLAŞMA", "SOSYAL YARDIMLAŞMA",
         "Yoksullukla Mücadele Edilmesi ve Sosyal Yardım Programlarının Bütüncül ve Hane Odaklı Bir Yaklaşımla Etkin Bir Şekilde Yürütülmesi.",
         "Yıl içinde sunulan sağlık hizmeti sayısı: Belediyenin bir yıl boyunca vatandaşlara doğrudan sağladığı tüm sağlık hizmetlerinin toplam sayısını gösterir."),
        ("TEDAVİ EDİCİ SAĞLIK", "TEDAVİ HİZMETLERİ",
         "Tedavi Edici Sağlık Hizmetlerine Erişimin ve Kalitenin Daha Da Artırılması ve Sağlık Araştırma Faaliyetlerinin Geliştirilmesi.",
         "Toplum sağlığı eğitimleri ve danışmanlık hizmetleri sayısı: Toplumun genel sağlık bilincini artırmaya yönelik faaliyetlerin sayısını ifade eder."),
        ("KENT GÜVENLİĞİ VE ESENLİĞİ", "ÇEVRE VE HALK SAĞLIĞININ KORUNMASI",
         "Yerel Yönetimlerin Mahalli Müşterek Nitelikteki İhtiyaçların Karşılanması Doğrultusunda Kent Güvenliği ve Estetiği Hizmetlerinin Devamının Sağlanması.",
         "İlçe genelinde vektör ile mücadele edilen yer sayısı ve dezenfekte edilen yer sayısı ile çevresel sağlık çalışmalarının kapsamı izlenir."),
        ("ENGELLİLERİN TOPLUMSAL HAYATA KATILIMI VE ÖZEL EĞİTİM", "ENGELLİ BAKIMI",
         "Engellilerin Toplumsal Hayata Katılımlarının Artırılması ve Özel Eğitime Gereksinim Duyan Bireylere Yönelik Hizmetlerde Beşeri ve Fiziki İmkânların Güçlendirilmesi.",
         "Kırılgan gruplara yönelik farkındalığı artırmak amaçlı yapılan etkinlik sayısı ile toplumsal kapsayıcılık izlenir."),
    ]
    subs=[]
    for p_name,s_name,rationale,goal in program_specs:
        p=Program(period_id=period.id,name=p_name); db.add(p); db.flush()
        sp=SubProgram(period_id=period.id,program_id=p.id,name=s_name,rationale=rationale,goal=goal)
        db.add(sp); db.flush(); subs.append(sp)

    indicators=[
        (subs[0],"Yıl içinde sunulan sağlık hizmeti sayısı","Oran (%)",(12500,12500,13500,14500,16500),
         "Yıl boyunca Sağlık İşleri Müdürlüğü tarafından vatandaşlara sunulan sağlık hizmetlerinin toplam sayısı ile hizmetin yaygınlığını ölçmek amaçlanmaktadır.","Yıl içerisinde sunulan toplam sağlık hizmeti sayısıdır."),
        (subs[1],"Toplum sağlığı eğitimleri ve danışmanlık hizmetleri sayısı","Adet",(5,5,7,7,7),
         "Sağlık İşleri Müdürlüğü'nün halka yönelik düzenlediği sağlık seminerleri, bilgilendirme toplantıları ve bireysel danışmanlık hizmetlerinin toplam sayısını ifade eder.","Yıl içerisinde sunulan toplam sağlık hizmeti sayısıdır."),
        (subs[2],"İlçe genelinde vektör ile mücadele edilen yer sayısı","Oran (%)",(12500,12500,13500,14500,16500),
         "Sivrisinek, fare gibi vektörlerle mücadele çalışmalarının yürütüldüğü müdahale noktalarının sayısını gösterir.","Yıl içerisinde sunulan toplam sağlık hizmeti sayısıdır."),
        (subs[2],"İlçe genelinde dezenfekte edilen yer sayısı","Oran (%)",(800,900,1000,1100,1200),
         "Dezenfeksiyon yapılan alanların sayısı üzerinden çevresel sağlık çalışmaları izlenir.","Yıl içerisinde sunulan toplam sağlık hizmeti sayısıdır."),
        (subs[3],"Yıl içinde sunulan sağlık hizmeti sayısı","Oran (%)",(20,20,25,30,32),
         "Engellilerin toplumsal hayata katılımını desteklemek ve farkındalık oluşturmak amacıyla düzenlenen etkinliklerin sayısını ölçmek amacıyla hazırlanmıştır.","Yıl içerisinde yapılan toplam etkinlik sayısı"),
    ]
    source="Büyükçekmece Belediye Başkanlığı 2025-2029 Stratejik Planı"
    for sp,name,unit,vals,explanation,method in indicators:
        ind=Indicator(period_id=period.id,department_id=health.id,subprogram_id=sp.id,name=name,unit=unit,explanation=explanation,calculation_method=method,data_source=source,status="draft")
        db.add(ind); db.flush()
        for year,kind,val in [
            (2025,"planned",vals[0]),(2025,"year_end_estimate",vals[1]),(2026,"target",vals[2]),
            (2027,"forecast",vals[3]),(2028,"forecast",vals[4])
        ]:
            db.add(IndicatorValue(indicator_id=ind.id,year=year,value_kind=kind,value=float(val)))

    activities=[
        (subs[0],"Koruyucu sağlık hizmetleri, evde bakım, hasta nakil hizmetlerinin verilmesi","Bütüncül hizmetlerle koruyucu bakım, evde bakım ve hasta nakli sağlamak.",15850000,20605000,26786500),
        (subs[1],"Psikolojik ve Beslenme danışmanlığı hizmetinin verilmesi","Toplumun sağlık okuryazarlığı konusunda bilgilendirilmesi",120000,156000,202800),
        (subs[2],"İlçe genelinde vektörel ilaçlama ve dezenfekte İşlemlerini gerçekleştirmek","Halk sağlığı için ilçe genelinde düzenli vektörel ilaçlama ve dezenfeksiyon hizmeti vermek.",400000,520000,676000),
        (subs[3],"Özel gereksinimli bireylerin sosyal aktivite ve gelişim becerilerini desteklemek","Özel gereksinimli bireylerin sosyal yaşama katılımını ve gelişimini desteklemek.",100000,130000,169000),
    ]
    for sp,name,explanation,b26,b27,b28 in activities:
        act=Activity(period_id=period.id,department_id=health.id,subprogram_id=sp.id,name=name,explanation=explanation)
        db.add(act); db.flush()
        for year,kind,amount in [
            (2025,"budget",0),(2025,"midyear_spend",0),(2025,"year_end_estimate",0),
            (2026,"budget",b26),(2027,"forecast",b27),(2028,"forecast",b28)
        ]:
            db.add(ActivityCostValue(activity_id=act.id,year=year,value_kind=kind,funding_type="total",amount=float(amount)))
            db.add(ActivityCostValue(activity_id=act.id,year=year,value_kind=kind,funding_type="inside",amount=float(amount)))
            db.add(ActivityCostValue(activity_id=act.id,year=year,value_kind=kind,funding_type="outside",amount=0))

    for year,kind,amount in [(2026,"budget",14500987),(2027,"forecast",18851283.10),(2028,"forecast",24506668.03)]:
        db.add(DepartmentCostValue(department_id=health.id,period_id=period.id,year=year,value_kind=kind,category="personnel_sgk",amount=amount))

    db.add(Submission(department_id=health.id,period_id=period.id,status="draft"))
    db.commit()
