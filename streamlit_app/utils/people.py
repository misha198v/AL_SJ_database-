from utils.auth import hash_password
from utils.db import audit, run, tx
from utils.ui import FormError, need


def _create_user(c, full_name, phone, email, password, role_id=None, role_name=None):
    need(full_name=full_name, phone=phone)
    if len(password or "") < 8:
        raise FormError("Use a password of at least 8 characters.")
    return run(c, """INSERT INTO users (full_name, email, phone, password_hash, role_id)
                     VALUES (:n, :e, :p, :h,
                             COALESCE(CAST(:rid AS smallint), (SELECT role_id FROM roles WHERE role_name = :rn)))
                     RETURNING user_id""",
               {"n": full_name.strip(), "e": (email or "").strip() or None, "p": phone.strip(),
                "h": hash_password(password), "rid": role_id, "rn": role_name}).scalar()


def create_client(actor, full_name, phone, password, national_id, email=None, dob=None, address=None):
    need(national_id=national_id)
    with tx(actor) as c:
        uid = _create_user(c, full_name, phone, email, password, role_name="Client")
        run(c, """INSERT INTO client_profiles (user_id, national_id, date_of_birth, address, preferred_language)
                  VALUES (:u, :n, :d, :a, 'EN')""",
            {"u": uid, "n": national_id.strip(), "d": dob, "a": (address or "").strip() or None})
        audit(c, actor, "CLIENT_ADDED", "users", uid)
    return uid


def create_staff(actor, full_name, phone, password, role_id, employee_no, email=None, date_hired=None):
    need(employee_no=employee_no)
    with tx(actor) as c:
        uid = _create_user(c, full_name, phone, email, password, role_id=role_id)
        run(c, """INSERT INTO staff_profiles (user_id, employee_no, date_hired)
                  VALUES (:u, :n, COALESCE(CAST(:d AS date), CURRENT_DATE))""",
            {"u": uid, "n": employee_no.strip(), "d": date_hired})
        audit(c, actor, "EMPLOYEE_ADDED", "users", uid)
    return uid