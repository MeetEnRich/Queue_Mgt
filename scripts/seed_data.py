"""
FULafia DQMS — Seed Data Script
================================
Seeds the database with 4 offices, staff accounts, 25 student profiles,
complaint categories, and realistic token history across 3 days.

Usage:
    python scripts/seed_data.py
"""

import sys
import os
import random
from datetime import datetime, date, timedelta, time

# Ensure project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import Office, ComplaintCategory, Student, Staff, Complaint, QueueToken


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_header(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def _print_step(msg: str):
    print(f"  -> {msg}")


# ---------------------------------------------------------------------------
# Office definitions
# ---------------------------------------------------------------------------

OFFICES = [
    {
        "name": "Management Information System (M.I.S/ICT)",
        "slug": "mis",
        "description": "Handles portal, result, registration, and ICT-related student issues.",
        "max_queue_capacity": 50,
        "active_counters": 3,
        "office_open_time": time(8, 0),
        "office_close_time": time(16, 0),
        "categories": [
            "Portal Login Issue",
            "Payment Verification Error",
            "Result/Grade Issue",
            "Course Registration Problem",
            "Technical/Portal Glitch",
            "Other",
        ],
    },
    {
        "name": "Registry",
        "slug": "registry",
        "description": "Admissions, transcripts, certificates, and student records.",
        "max_queue_capacity": 40,
        "active_counters": 2,
        "office_open_time": time(8, 0),
        "office_close_time": time(16, 0),
        "categories": [
            "Admission Verification",
            "Transcript Request",
            "Change of Programme/Department",
            "Certificate Collection",
            "Data Correction",
            "Other",
        ],
    },
    {
        "name": "Bursary",
        "slug": "bursary",
        "description": "Fee payments, refunds, scholarships, and financial records.",
        "max_queue_capacity": 60,
        "active_counters": 3,
        "office_open_time": time(8, 0),
        "office_close_time": time(15, 0),
        "categories": [
            "Fee Payment Discrepancy",
            "Refund Request",
            "Scholarship/Bursary Inquiry",
            "Receipt Issue",
            "Other",
        ],
    },
    {
        "name": "Student Affairs",
        "slug": "student-affairs",
        "description": "Hostel allocation, disciplinary matters, welfare, and ID cards.",
        "max_queue_capacity": 30,
        "active_counters": 2,
        "office_open_time": time(9, 0),
        "office_close_time": time(16, 0),
        "categories": [
            "Hostel/Accommodation Complaint",
            "Disciplinary Matter",
            "ID Card Issue",
            "Welfare Support",
            "Other",
        ],
    },
]


# ---------------------------------------------------------------------------
# Staff definitions (per office)
# ---------------------------------------------------------------------------

STAFF_PER_OFFICE = {
    "mis": {
        "admin": {
            "username": "mis_admin",
            "full_name": "Mrs. Hauwa Garba",
            "password": "admin123",
            "role": "office_admin",
            "counter": None,
        },
        "staff": [
            {"username": "mis_staff1", "full_name": "Mr. Yusuf Abdullahi", "password": "staff123", "counter": 1},
            {"username": "mis_staff2", "full_name": "Miss. Fatima Idris", "password": "staff123", "counter": 2},
        ],
    },
    "registry": {
        "admin": {
            "username": "reg_admin",
            "full_name": "Dr. Musa Suleiman",
            "password": "admin123",
            "role": "office_admin",
            "counter": None,
        },
        "staff": [
            {"username": "reg_staff1", "full_name": "Mrs. Blessing Okoro", "password": "staff123", "counter": 1},
            {"username": "reg_staff2", "full_name": "Mr. Tunde Adeyemi", "password": "staff123", "counter": 2},
        ],
    },
    "bursary": {
        "admin": {
            "username": "bur_admin",
            "full_name": "Mr. Emmanuel Okafor",
            "password": "admin123",
            "role": "office_admin",
            "counter": None,
        },
        "staff": [
            {"username": "bur_staff1", "full_name": "Mrs. Amina Mohammed", "password": "staff123", "counter": 1},
            {"username": "bur_staff2", "full_name": "Mr. Peter Audu", "password": "staff123", "counter": 2},
        ],
    },
    "student-affairs": {
        "admin": {
            "username": "sa_admin",
            "full_name": "Mrs. Grace Adamu",
            "password": "admin123",
            "role": "office_admin",
            "counter": None,
        },
        "staff": [
            {"username": "sa_staff1", "full_name": "Mr. Daniel Bako", "password": "staff123", "counter": 1},
            {"username": "sa_staff2", "full_name": "Miss. Halima Usman", "password": "staff123", "counter": 2},
        ],
    },
}


# ---------------------------------------------------------------------------
# Student profiles (25 realistic Nigerian names + FULafia matric format)
# ---------------------------------------------------------------------------

STUDENTS = [
    {"matric_no": "2021/CP/CSC/0295", "full_name": "Ajunwa Stephen Oche", "department": "Computer Science"},
    {"matric_no": "2021/NS/CSC/0101", "full_name": "Chinedu Okonkwo", "department": "Computer Science"},
    {"matric_no": "2022/CP/CSC/0202", "full_name": "Abubakar Sadiq Ibrahim", "department": "Computer Science"},
    {"matric_no": "2020/AR/PHY/0055", "full_name": "Ngozi Adaeze Nwosu", "department": "Physics"},
    {"matric_no": "2021/NS/PHY/0078", "full_name": "Mohammed Kabir Yusuf", "department": "Physics"},
    {"matric_no": "2022/CP/CHM/0130", "full_name": "Oluwaseun Adebayo", "department": "Chemistry"},
    {"matric_no": "2021/NS/CHM/0045", "full_name": "Fatimah Binta Umar", "department": "Chemistry"},
    {"matric_no": "2020/CP/MTH/0032", "full_name": "Emeka Chukwuemeka Obi", "department": "Mathematics"},
    {"matric_no": "2022/NS/MTH/0167", "full_name": "Hauwa Aliyu Danjuma", "department": "Mathematics"},
    {"matric_no": "2021/CP/BIO/0214", "full_name": "Adaobi Nneka Eze", "department": "Biology"},
    {"matric_no": "2020/NS/BIO/0089", "full_name": "Ibrahim Musa Lawal", "department": "Biology"},
    {"matric_no": "2022/AR/ENG/0150", "full_name": "Chiamaka Blessing Ogu", "department": "English"},
    {"matric_no": "2021/NS/ENG/0073", "full_name": "Garba Sani Abubakar", "department": "English"},
    {"matric_no": "2020/CP/HIS/0041", "full_name": "Tolulope Funmi Akinwale", "department": "History"},
    {"matric_no": "2022/NS/HIS/0192", "full_name": "Usman Bello Abdulkadir", "department": "History"},
    {"matric_no": "2021/CP/ECO/0118", "full_name": "Chinwe Amaka Udofia", "department": "Economics"},
    {"matric_no": "2020/AR/ECO/0063", "full_name": "Abdullahi Nasir Shuaibu", "department": "Economics"},
    {"matric_no": "2022/CP/POL/0085", "full_name": "Omotola Grace Bakare", "department": "Political Science"},
    {"matric_no": "2021/NS/POL/0146", "full_name": "Isah Haruna Garba", "department": "Political Science"},
    {"matric_no": "2020/CP/GEO/0027", "full_name": "Chisom Victor Okafor", "department": "Geology"},
    {"matric_no": "2022/NS/GEO/0199", "full_name": "Maryam Binta Aliyu", "department": "Geology"},
    {"matric_no": "2021/AR/CSC/0310", "full_name": "Taiwo Olamide Ogunleye", "department": "Computer Science"},
    {"matric_no": "2020/CP/CSC/0043", "full_name": "Zainab Aisha Balarabe", "department": "Computer Science"},
    {"matric_no": "2022/NS/BIO/0225", "full_name": "Obinna Nnamdi Igwe", "department": "Biology"},
    {"matric_no": "2021/CP/MTH/0157", "full_name": "Aminu Danladi Salisu", "department": "Mathematics"},
]


# Complaint descriptions keyed by category name
COMPLAINT_DESCRIPTIONS = {
    # M.I.S
    "Portal Login Issue": [
        "I cannot log in to my portal since last week.",
        "My portal keeps redirecting to a blank page.",
        "My password reset link expired before I could use it.",
    ],
    "Payment Verification Error": [
        "I paid N50,000 school fees but portal still shows unpaid.",
        "My receipt number is not recognized on the portal.",
    ],
    "Result/Grade Issue": [
        "My CSC 301 result is showing F but I scored 58.",
        "My second semester results are completely missing.",
    ],
    "Course Registration Problem": [
        "I cannot register more than 15 credit units even though I'm allowed 24.",
        "The system rejected my elective course registration.",
    ],
    "Technical/Portal Glitch": [
        "Portal times out every time I try to print my course form.",
        "Error 500 when opening my student profile.",
    ],
    # Registry
    "Admission Verification": [
        "My JAMB admission status doesn't reflect on the school portal.",
        "I need a letter to confirm my admission for a visa application.",
    ],
    "Transcript Request": [
        "I submitted a transcript request 3 months ago with no update.",
        "I need my academic transcript urgently for NYSC mobilization.",
    ],
    "Change of Programme/Department": [
        "I applied for a change from Physics to Computer Science.",
        "My change of department form was submitted but not processed.",
    ],
    "Certificate Collection": [
        "I graduated in 2022 and my certificate is still not ready.",
        "I was told to come collect my certificate but it was not found.",
    ],
    "Data Correction": [
        "My surname is misspelled on my school records.",
        "My date of birth is wrong in the registry system.",
    ],
    # Bursary
    "Fee Payment Discrepancy": [
        "I was charged twice for acceptance fee.",
        "Portal says I owe N20,000 but I already paid in full.",
    ],
    "Refund Request": [
        "I overpaid my school fees and need a refund.",
        "I withdrew from the programme and need my deposit back.",
    ],
    "Scholarship/Bursary Inquiry": [
        "I was awarded a state scholarship but it hasn't reflected.",
        "I need confirmation of my TETFund scholarship status.",
    ],
    "Receipt Issue": [
        "My payment receipt was not generated after paying online.",
        "I need a reprint of my school fees receipt from last session.",
    ],
    # Student Affairs
    "Hostel/Accommodation Complaint": [
        "The tap water in Block C has not been running for 2 weeks.",
        "My hostel room was reassigned without notice.",
    ],
    "Disciplinary Matter": [
        "I received a query letter I believe was sent in error.",
        "I want to appeal a suspension decision.",
    ],
    "ID Card Issue": [
        "My student ID card has the wrong department on it.",
        "I submitted for an ID card replacement but haven't received it.",
    ],
    "Welfare Support": [
        "I need an emergency loan for medical treatment.",
        "I would like information about the student welfare fund.",
    ],
    # Shared
    "Other": [
        "I have a general inquiry not covered by other categories.",
        "I need assistance with an issue I can't classify.",
        "I need to speak with someone about a unique situation.",
    ],
}


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------

def seed():
    _print_header("FULafia DQMS — Database Seeder")

    app = create_app()

    with app.app_context():
        # ---- Drop & recreate ----
        _print_step("Dropping all existing tables...")
        db.drop_all()
        _print_step("Creating all tables from models...")
        db.create_all()
        print()

        # ==================================================================
        # 1. OFFICES
        # ==================================================================
        _print_header("1. Creating Offices")
        office_map = {}  # slug -> Office
        category_map = {}  # (office_slug, category_name) -> ComplaintCategory

        for odef in OFFICES:
            office = Office(
                name=odef["name"],
                slug=odef["slug"],
                description=odef["description"],
                max_queue_capacity=odef["max_queue_capacity"],
                active_counters=odef["active_counters"],
                office_open_time=odef["office_open_time"],
                office_close_time=odef["office_close_time"],
                is_active=True,
            )
            db.session.add(office)
            db.session.flush()  # get the id
            office_map[odef["slug"]] = office
            _print_step(f"Office: {office.name} (slug={office.slug}, capacity={office.max_queue_capacity}, counters={office.active_counters})")

            # Categories
            for cat_name in odef["categories"]:
                cat = ComplaintCategory(office_id=office.id, name=cat_name, is_active=True)
                db.session.add(cat)
                db.session.flush()
                category_map[(odef["slug"], cat_name)] = cat

        db.session.commit()
        _print_step(f"Total offices: {len(office_map)}")
        _print_step(f"Total categories: {len(category_map)}")

        # ==================================================================
        # 2. STAFF ACCOUNTS
        # ==================================================================
        _print_header("2. Creating Staff Accounts")
        staff_map = {}  # username -> Staff

        # Super Admin
        super_admin = Staff(
            office_id=None,
            username="superadmin",
            full_name="Prof. Ibrahim Bello",
            role="super_admin",
            assigned_counter=None,
            is_active=True,
        )
        super_admin.set_password("admin123")
        db.session.add(super_admin)
        db.session.flush()
        staff_map["superadmin"] = super_admin
        _print_step(f"Super Admin: superadmin / admin123  (Prof. Ibrahim Bello)")

        # Per-office staff
        for slug, office in office_map.items():
            sdef = STAFF_PER_OFFICE[slug]

            # Office admin
            adm_info = sdef["admin"]
            admin_staff = Staff(
                office_id=office.id,
                username=adm_info["username"],
                full_name=adm_info["full_name"],
                role="office_admin",
                assigned_counter=adm_info["counter"],
                is_active=True,
            )
            admin_staff.set_password(adm_info["password"])
            db.session.add(admin_staff)
            db.session.flush()
            staff_map[adm_info["username"]] = admin_staff
            _print_step(f"  [{slug}] Office Admin: {adm_info['username']} / {adm_info['password']}  ({adm_info['full_name']})")

            # Regular staff
            for sinfo in sdef["staff"]:
                s = Staff(
                    office_id=office.id,
                    username=sinfo["username"],
                    full_name=sinfo["full_name"],
                    role="staff",
                    assigned_counter=sinfo["counter"],
                    is_active=True,
                )
                s.set_password(sinfo["password"])
                db.session.add(s)
                db.session.flush()
                staff_map[sinfo["username"]] = s
                _print_step(f"  [{slug}] Staff: {sinfo['username']} / {sinfo['password']}  ({sinfo['full_name']}, counter {sinfo['counter']})")

        db.session.commit()
        _print_step(f"Total staff accounts: {len(staff_map)}")

        # ==================================================================
        # 3. STUDENT PROFILES
        # ==================================================================
        _print_header("3. Creating Student Profiles")
        student_objs = []

        for sdef in STUDENTS:
            student = Student(
                matric_no=sdef["matric_no"],
                full_name=sdef["full_name"],
                department=sdef["department"],
            )
            db.session.add(student)
            db.session.flush()
            student_objs.append(student)
            _print_step(f"  {sdef['matric_no']}  {sdef['full_name']}  ({sdef['department']})")

        db.session.commit()
        _print_step(f"Total students: {len(student_objs)}")

        # ==================================================================
        # 4. TOKEN HISTORY (3 days x 4 offices)
        # ==================================================================
        _print_header("4. Creating Token History")

        today = date.today()
        dates = [today - timedelta(days=2), today - timedelta(days=1), today]
        date_labels = ["Day before yesterday", "Yesterday", "Today"]

        random.seed(42)  # reproducible

        total_tokens = 0
        total_complaints = 0

        for slug, office in office_map.items():
            _print_step(f"\n  Office: {office.name}")

            # Get staff for this office
            office_staff = [s for s in staff_map.values() if s.office_id == office.id and s.role == "staff"]
            # Get categories for this office
            office_cats = [v for (k, _), v in category_map.items() if k == slug]

            for day_idx, (q_date, day_label) in enumerate(zip(dates, date_labels)):
                is_today = (q_date == today)
                num_tokens = random.randint(15, 25)
                _print_step(f"    {day_label} ({q_date}): {num_tokens} tokens")

                # Build a shuffled student pool for this office-day
                student_pool = random.sample(student_objs, min(num_tokens, len(student_objs)))
                if len(student_pool) < num_tokens:
                    student_pool = student_pool + random.choices(student_objs, k=num_tokens - len(student_pool))

                # Status distribution
                statuses = []
                if is_today:
                    # ~60% completed, ~15% skipped, ~10% cancelled, ~10% waiting, ~5% being_served
                    n_completed = int(num_tokens * 0.60)
                    n_skipped = int(num_tokens * 0.15)
                    n_cancelled = int(num_tokens * 0.10)
                    n_being_served = 1  # max 1 per office
                    n_waiting = num_tokens - n_completed - n_skipped - n_cancelled - n_being_served
                    if n_waiting < 0:
                        n_waiting = 0
                        n_completed = num_tokens - n_skipped - n_cancelled - n_being_served
                    statuses = (
                        ["completed"] * n_completed
                        + ["skipped"] * n_skipped
                        + ["cancelled"] * n_cancelled
                        + ["being_served"] * n_being_served
                        + ["waiting"] * n_waiting
                    )
                else:
                    # Past days: only completed, skipped, cancelled
                    n_completed = int(num_tokens * 0.70)
                    n_skipped = int(num_tokens * 0.15)
                    n_cancelled = num_tokens - n_completed - n_skipped
                    statuses = (
                        ["completed"] * n_completed
                        + ["skipped"] * n_skipped
                        + ["cancelled"] * n_cancelled
                    )

                # Shuffle to mix the statuses
                random.shuffle(statuses)

                # Create tokens
                base_hour = office.office_open_time.hour
                for token_num_idx, status in enumerate(statuses, start=1):
                    student = student_pool[token_num_idx - 1]
                    category = random.choice(office_cats)

                    # Timestamps
                    minutes_offset = (token_num_idx - 1) * random.randint(2, 8)
                    joined_at = datetime.combine(q_date, time(base_hour, 0)) + timedelta(minutes=minutes_offset)

                    # Create complaint
                    cat_descriptions = COMPLAINT_DESCRIPTIONS.get(category.name, COMPLAINT_DESCRIPTIONS["Other"])
                    desc = random.choice(cat_descriptions)

                    complaint = Complaint(
                        office_id=office.id,
                        student_id=student.id,
                        category_id=category.id,
                        description=desc,
                        created_at=joined_at,
                    )
                    db.session.add(complaint)
                    db.session.flush()
                    total_complaints += 1

                    # Build token
                    wait_seconds = None
                    service_seconds = None
                    called_at = None
                    completed_at = None
                    assigned_staff_id = None
                    counter = None

                    if status == "completed":
                        wait_secs = random.randint(60, 600)
                        service_secs = random.randint(120, 900)
                        called_at = joined_at + timedelta(seconds=wait_secs)
                        completed_at = called_at + timedelta(seconds=service_secs)
                        wait_seconds = wait_secs
                        service_seconds = service_secs
                        staff_member = random.choice(office_staff)
                        assigned_staff_id = staff_member.id
                        counter = staff_member.assigned_counter

                    elif status == "skipped":
                        wait_secs = random.randint(60, 600)
                        called_at = joined_at + timedelta(seconds=wait_secs)
                        completed_at = called_at + timedelta(seconds=random.randint(10, 30))
                        wait_seconds = wait_secs
                        staff_member = random.choice(office_staff)
                        assigned_staff_id = staff_member.id
                        counter = staff_member.assigned_counter

                    elif status == "cancelled":
                        # Student cancelled after some waiting
                        completed_at = joined_at + timedelta(seconds=random.randint(60, 300))

                    elif status == "being_served":
                        wait_secs = random.randint(60, 300)
                        called_at = joined_at + timedelta(seconds=wait_secs)
                        wait_seconds = wait_secs
                        staff_member = random.choice(office_staff)
                        assigned_staff_id = staff_member.id
                        counter = staff_member.assigned_counter

                    elif status == "waiting":
                        # No called_at or completed_at
                        pass

                    token = QueueToken(
                        office_id=office.id,
                        token_number=token_num_idx,
                        queue_date=q_date,
                        student_id=student.id,
                        complaint_id=complaint.id,
                        status=status,
                        assigned_staff_id=assigned_staff_id,
                        counter=counter,
                        joined_at=joined_at,
                        called_at=called_at,
                        completed_at=completed_at,
                        wait_seconds=wait_seconds,
                        service_seconds=service_seconds,
                    )
                    db.session.add(token)
                    total_tokens += 1

                db.session.commit()

        _print_step(f"\nTotal complaints created: {total_complaints}")
        _print_step(f"Total tokens created: {total_tokens}")

        # ==================================================================
        # 5. CROSS-OFFICE STUDENT REUSE SUMMARY
        # ==================================================================
        _print_header("5. Cross-Office Reuse Check")
        from sqlalchemy import func
        reuse_query = (
            db.session.query(Student.full_name, func.count(QueueToken.id).label("token_count"))
            .join(QueueToken, QueueToken.student_id == Student.id)
            .group_by(Student.id)
            .having(func.count(QueueToken.id) > 1)
            .order_by(func.count(QueueToken.id).desc())
            .limit(10)
            .all()
        )
        if reuse_query:
            for name, count in reuse_query:
                _print_step(f"  {name}: {count} tokens across offices/days")
        else:
            _print_step("  (No cross-office reuse detected — all tokens unique per student)")

        # ==================================================================
        # SUMMARY
        # ==================================================================
        _print_header("SEED COMPLETE — Summary")
        _print_step(f"Offices:            {len(office_map)}")
        _print_step(f"Categories:         {len(category_map)}")
        _print_step(f"Staff accounts:     {len(staff_map)}")
        _print_step(f"Student profiles:   {len(student_objs)}")
        _print_step(f"Complaints:         {total_complaints}")
        _print_step(f"Queue tokens:       {total_tokens}")
        print()
        _print_step("Default Credentials:")
        _print_step(f"  Super Admin:    superadmin / admin123")
        _print_step(f"  MIS Admin:      mis_admin / admin123")
        _print_step(f"  Registry Admin: reg_admin / admin123")
        _print_step(f"  Bursary Admin:  bur_admin / admin123")
        _print_step(f"  Student Affairs Admin: sa_admin / admin123")
        _print_step(f"  All regular staff: <prefix>_staff1, <prefix>_staff2 / staff123")
        print()


if __name__ == "__main__":
    seed()
