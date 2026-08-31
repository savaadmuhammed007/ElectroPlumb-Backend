from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import UserProfile, Item, MaterialList, ListItem

class Command(BaseCommand):
    help = 'Seeds initial database with Electrical and Plumbing items, default users, and sample lists'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting database seeding..."))

        # 1. Create Default Users
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@electricalplumbing.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            UserProfile.objects.create(
                user=admin_user,
                role='admin',
                phone='+91 98765 43210',
                business_name='ElectroPlumb Solutions Admin',
                city='Calicut',
                state='Kerala'
            )
            self.stdout.write(self.style.SUCCESS("Created admin user (admin / admin123)"))

        worker_user, created = User.objects.get_or_create(
            username='savaad',
            defaults={
                'email': 'savaad@workmaster.com',
                'first_name': 'Savaad',
                'last_name': 'Rahman',
                'is_staff': False
            }
        )
        if created:
            worker_user.set_password('worker123')
            worker_user.save()
            UserProfile.objects.create(
                user=worker_user,
                role='electrician',
                phone='+91 98765 00112',
                whatsapp='+91 98765 00112',
                business_name='Savaad Electrical & Plumbing Works',
                address='1st Floor, Building #45, Near Civil Station',
                city='Calicut',
                state='Kerala',
                pin_code='673020',
                about='Licensed Master Electrician & Professional Plumbing Contractor with 8+ years experience in commercial & residential projects.'
            )
            self.stdout.write(self.style.SUCCESS("Created worker user (savaad / worker123)"))

        # 2. Electrical Items Catalog
        electrical_items = [
            # Wires & Cables
            ("1.5mm FR Wire (Red)", "ELE-WIR-101", "Wires & Cables", "Meter", "Single core flame retardant copper wire for lighting circuits"),
            ("1.5mm FR Wire (Black)", "ELE-WIR-102", "Wires & Cables", "Meter", "Single core flame retardant neutral wire"),
            ("2.5mm FR Wire (Red)", "ELE-WIR-103", "Wires & Cables", "Meter", "Heavy duty wire for power socket circuits"),
            ("2.5mm FR Wire (Black)", "ELE-WIR-104", "Wires & Cables", "Meter", "Heavy duty neutral wire"),
            ("4.0mm FR Wire (Green/Yellow)", "ELE-WIR-105", "Wires & Cables", "Meter", "Earthing & main distribution power wire"),
            ("6.0mm Main Feeder Wire", "ELE-WIR-106", "Wires & Cables", "Meter", "Main power inlet cable"),
            ("Submersible Cable 3-Core 4mm", "ELE-WIR-107", "Wires & Cables", "Meter", "Waterproof 3-core cable for submersible pumps"),

            # Modular Switches & Sockets
            ("1-Way Modular Switch 6A", "ELE-SWI-201", "Switches & Sockets", "Piece", "Standard 6A modular switch for lights/fans"),
            ("2-Way Modular Switch 6A", "ELE-SWI-202", "Switches & Sockets", "Piece", "Two-way switch for staircase/bedroom controls"),
            ("Power Switch 16A", "ELE-SWI-203", "Switches & Sockets", "Piece", "Heavy duty 16A switch for appliances"),
            ("3-Pin Modular Socket 6A/16A", "ELE-SOC-204", "Switches & Sockets", "Piece", "Universal shuttered combination socket"),
            ("Modular Fan Regulator (2-Step)", "ELE-REG-205", "Switches & Sockets", "Piece", "Compact hum-free fan speed control knob"),
            ("Modular Bell Push Switch", "ELE-SWI-206", "Switches & Sockets", "Piece", "Doorbell switch with LED indicator"),
            ("TV Socket Outlet", "ELE-SOC-207", "Switches & Sockets", "Piece", "Coaxial cable TV connector module"),

            # Circuit Protection (MCB / DB)
            ("Single Pole MCB 10A (C-Curve)", "ELE-MCB-301", "Circuit Protection", "Piece", "Miniature circuit breaker for lighting"),
            ("Single Pole MCB 16A (C-Curve)", "ELE-MCB-302", "Circuit Protection", "Piece", "Miniature circuit breaker for power outlets"),
            ("Single Pole MCB 32A", "ELE-MCB-303", "Circuit Protection", "Piece", "MCB for high load AC/Water Heater"),
            ("Double Pole Isolator 40A", "ELE-ISO-304", "Circuit Protection", "Piece", "Main isolator switch for single phase board"),
            ("RCCB 40A 30mA (Double Pole)", "ELE-ELCB-305", "Circuit Protection", "Piece", "Earth leakage circuit breaker for shock protection"),
            ("Distribution Board 8-Way (Double Door)", "ELE-DB-306", "Circuit Protection", "Piece", "IP42 metal enclosure distribution box"),

            # Conduit & Accessories
            ("PVC Rigid Conduit Pipe 20mm (Medium)", "ELE-CND-401", "Conduit & Pipes", "Length", "20mm heavy duty PVC electrical pipe (3m length)"),
            ("PVC Rigid Conduit Pipe 25mm", "ELE-CND-402", "Conduit & Pipes", "Length", "25mm conduit pipe for main wire runs"),
            ("Flexible PVC Pipe 20mm", "ELE-FLX-403", "Conduit & Pipes", "Meter", "Corrugated flexible pipe for bends & ceilings"),
            ("PVC Junction Box (4-Way)", "ELE-JNB-404", "Conduit & Pipes", "Piece", "Deep surface junction box"),
            ("PVC Conduit Elbow 20mm", "ELE-ELB-405", "Conduit & Pipes", "Piece", "90 degree conduit bend"),
            ("Metal Fan Box with Rods", "ELE-BOX-406", "Conduit & Pipes", "Piece", "Heavy duty ceiling fan box with downrod hook"),
            ("Modular Metal Switch Box (6-Module)", "ELE-BOX-407", "Conduit & Pipes", "Piece", "Concealed GI metal wall box"),

            # Lighting & Fixtures
            ("LED Downlight Panel 12W (Warm White)", "ELE-LGT-501", "Lighting", "Piece", "Recessed ceiling LED panel light"),
            ("LED Batten Tube 20W (Cool Day Light)", "ELE-LGT-502", "Lighting", "Piece", "4ft slim LED tubelight fixture"),
            ("Modular Ceiling Rose", "ELE-LGT-503", "Lighting", "Piece", "Ceiling junction light connector"),
            ("Electrical Insulation Tape (Black)", "ELE-MIS-504", "Accessories", "Roll", "Flame retardant PVC adhesive tape"),
            ("Cable Ties 200mm (Pack of 100)", "ELE-MIS-505", "Accessories", "Packet", "Nylon wire binding straps"),
        ]

        for name, code, cat, unit, desc in electrical_items:
            Item.objects.get_or_create(
                item_code=code,
                defaults={
                    'name': name,
                    'item_type': 'electrical',
                    'category': cat,
                    'unit': unit,
                    'description': desc,
                    'status': 'active'
                }
            )

        # 3. Plumbing Items Catalog
        plumbing_items = [
            # Pipes
            ("CPVC Pipe 3/4 inch (SDR 11)", "PLM-PIP-101", "Pipes", "Length", "Hot & cold water pressure pipe (3m length)"),
            ("CPVC Pipe 1 inch (SDR 11)", "PLM-PIP-102", "Pipes", "Length", "Main supply CPVC pipe (3m length)"),
            ("PVC Drainage Pipe 4 inch (4kg/cm2)", "PLM-PIP-103", "Pipes", "Length", "Soil & waste water drainage pipe"),
            ("PVC Drainage Pipe 2.5 inch", "PLM-PIP-104", "Pipes", "Length", "Grey water waste drainage line pipe"),
            ("SWR Pipe 110mm with Ring", "PLM-PIP-105", "Pipes", "Length", "Heavy duty outdoor sewer pipe"),

            # Fittings (Elbows, Tees, Couplers)
            ("CPVC Elbow 90 Degree 3/4 inch", "PLM-FTG-201", "Fittings", "Piece", "CPVC right angle elbow fitting"),
            ("CPVC Equal Tee 3/4 inch", "PLM-FTG-202", "Fittings", "Piece", "Tee junction connector for water lines"),
            ("CPVC Coupler 3/4 inch", "PLM-FTG-203", "Fittings", "Piece", "Straight pipe joining socket"),
            ("CPVC Brass Elbow 3/4 x 1/2 inch", "PLM-FTG-204", "Fittings", "Piece", "Brass threaded elbow for wall tap fitting"),
            ("CPVC Brass Tee 3/4 x 1/2 inch", "PLM-FTG-205", "Fittings", "Piece", "Threaded outlet tee for concealed valves"),
            ("CPVC Male Threaded Adaptor (MTA) 3/4\"", "PLM-FTG-206", "Fittings", "Piece", "Male thread adaptor for pump & tank hookups"),
            ("CPVC Female Threaded Adaptor (FTA) 3/4\"", "PLM-FTG-207", "Fittings", "Piece", "Female thread adapter"),
            ("PVC Bend 4 inch 90 Degree (Door)", "PLM-FTG-208", "Fittings", "Piece", "Inspection door bend for waste line"),
            ("PVC Y-Tee 4 inch", "PLM-FTG-209", "Fittings", "Piece", "45 degree Y branch drain connector"),

            # Valves & Controls
            ("CPVC Ball Valve 3/4 inch", "PLM-VLV-301", "Valves & Controls", "Piece", "Quarter turn shut-off water control valve"),
            ("CPVC Ball Valve 1 inch", "PLM-VLV-302", "Valves & Controls", "Piece", "Main overhead tank supply isolation valve"),
            ("Brass Concealed Stop Cock 1/2 inch", "PLM-VLV-303", "Valves & Controls", "Piece", "Heavy brass wall valve for shower/flush controls"),
            ("Non Return Valve (NRV) 1 inch", "PLM-VLV-304", "Valves & Controls", "Piece", "Check valve to prevent water backflow"),

            # Taps, Showers & Fixtures
            ("Bib Tap Brass Chrome Plated", "PLM-FIX-401", "Taps & Showers", "Piece", "Standard wall mounted water tap"),
            ("2-in-1 Wall Mixer Tap", "PLM-FIX-402", "Taps & Showers", "Piece", "Hot & cold water mixer unit for shower"),
            ("Overhead Rain Shower 4x4 inch", "PLM-FIX-403", "Taps & Showers", "Piece", "Chrome rainfall shower head with arm"),
            ("Health Faucet / Jet Spray with Hose", "PLM-FIX-404", "Taps & Showers", "Piece", "Toilet hand spray set with 1.2m SS hose"),
            ("SS Kitchen Sink Waste Coupling 4 inch", "PLM-FIX-405", "Taps & Showers", "Piece", "Stainless steel sink drain strainer outlet"),
            ("Floor Trap PVC 4 inch x 2 inch", "PLM-TRP-406", "Traps & Drains", "Piece", "Bathroom floor drain trap with water seal"),
            ("Cockroach Trap SS Grating 5x5 inch", "PLM-TRP-407", "Traps & Drains", "Piece", "Anti-odour anti-pest floor drain cover"),

            # Chemicals & Hardware Accessories
            ("CPVC Solvent Cement 250ml", "PLM-CHM-501", "Chemicals", "Can", "Heavy duty liquid weld adhesive for CPVC"),
            ("Teflon Thread Seal Tape 12mm", "PLM-ACC-502", "Accessories", "Roll", "PTFE thread sealing tape for leak prevention"),
            ("G.I. Pipe Clamps 1 inch (Pack of 20)", "PLM-ACC-503", "Accessories", "Packet", "Heavy metal wall mounting saddle clamps"),
            ("Rubber Washer Set (Assorted)", "PLM-ACC-504", "Accessories", "Packet", "Sealing gaskets for taps and hoses"),
            ("Silicone Sealant Clear Tube", "PLM-CHM-505", "Chemicals", "Tube", "Waterproof gap filler for basins & sinks"),
        ]

        for name, code, cat, unit, desc in plumbing_items:
            Item.objects.get_or_create(
                item_code=code,
                defaults={
                    'name': name,
                    'item_type': 'plumbing',
                    'category': cat,
                    'unit': unit,
                    'description': desc,
                    'status': 'active'
                }
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(electrical_items)} Electrical items & {len(plumbing_items)} Plumbing items!"))

        # 4. Create Sample Material List for Worker
        sample_list, created = MaterialList.objects.get_or_create(
            user=worker_user,
            client_name="Abdul Rahman",
            list_type="electrical",
            defaults={
                'client_phone': "+91 98470 12345",
                'project_name': "Green Villa New Residence",
                'location': "Calicut, Kerala",
                'date': "11 August 2026",
                'notes': "Please deliver all materials by Thursday morning. Ensure Havells or Finolex ISI brand cables."
            }
        )
        if created:
            wire1 = Item.objects.get(item_code="ELE-WIR-101")
            wire2 = Item.objects.get(item_code="ELE-WIR-103")
            switch1 = Item.objects.get(item_code="ELE-SWI-201")
            conduit = Item.objects.get(item_code="ELE-CND-401")

            ListItem.objects.create(material_list=sample_list, item=wire1, item_name=wire1.name, category=wire1.category, unit=wire1.unit, quantity=50)
            ListItem.objects.create(material_list=sample_list, item=wire2, item_name=wire2.name, category=wire2.category, unit=wire2.unit, quantity=30)
            ListItem.objects.create(material_list=sample_list, item=switch1, item_name=switch1.name, category=switch1.category, unit=switch1.unit, quantity=24)
            ListItem.objects.create(material_list=sample_list, item=conduit, item_name=conduit.name, category=conduit.category, unit=conduit.unit, quantity=20)
            self.stdout.write(self.style.SUCCESS("Created sample material list for Savaad"))

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
